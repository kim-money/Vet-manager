from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code39
from reportlab.lib.pagesizes import letter
from .models import Product, Category, Batch
from .forms import ProductForm, CategoryForm, BatchForm
from django.db.models import Sum, Q
import csv
import io
import json


@login_required(login_url='/authlogin/login')
def category_list(request):
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')
    form = CategoryForm()
    return render(request, 'inventory/category_list.html', {
        'categories': categories,
        'form': form
    })


@login_required(login_url='/authlogin/login')
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'inventory/add_category.html', {'form': form})


@login_required(login_url='/authlogin/login')
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'inventory/edit_category.html', {'form': form})


@login_required(login_url='/authlogin/login')
def product_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', 'all')

    if category_id != 'all' and category_id:
        products = Product.objects.filter(category_id=category_id)
    else:
        products = Product.objects.all()

    if query:
        products = products.filter(name__icontains=query) | products.filter(barcode__icontains=query)

    # Aggregate total stock for each product
    products = products.annotate(total_stock=Sum('batches__quantity'))

    # Pagination
    per_page = request.GET.get('per_page', 25)
    paginator = Paginator(products, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    return render(request, 'inventory/product_list.html', {
        'page_obj': page_obj,
        'query': query,
        'per_page': per_page,
        'categories': categories,
        'selected_category': category_id,
    })


@login_required(login_url='/authlogin/login')
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    batches = product.batches.all()

    return render(request, 'inventory/product_detail.html', {
        'product': product,
        'batches': batches,
    })


@login_required(login_url='/authlogin/login')
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        print("Request method:", request.method) 
        print("Form data:", request.POST)         
        
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully.")
            return redirect('product_list') 
        else:
            print("Form errors:", form.errors)  
            messages.error(request, "There was an error with your form submission.")
    else:
        form = ProductForm()

    return render(request, 'inventory/add_product.html', {'form': form})


@login_required(login_url='/authlogin/login')
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/edit_product.html', {'form': form, 'product': product})


@login_required(login_url='/authlogin/login')
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('product_list')


@login_required(login_url='/authlogin/login')
def receive_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.product = product
            batch.batch_code = batch.generate_batch_code()
            batch.save()

            product.receive_stock(batch.quantity)
            return redirect('product_detail', pk=product.id)
    else:
        form = BatchForm()

    return render(request, 'inventory/receive_stock.html', {'product': product, 'form': form})


@login_required(login_url='/authlogin/login')
def export_products(request):
    products = Product.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'

    writer = csv.writer(response)
    writer.writerow(['Barcode', 'Name', 'Buying Price', 'Selling Price', 'Stock Quantity', 'Expiry Date', 'Packaging Type', 'Category'])

    for product in products:
        writer.writerow([
            product.barcode,
            product.name,
            product.buying_price,
            product.selling_price,
            product.stock_quantity,
            product.expiry_date,
            product.packaging_type,
            product.category.name if product.category else 'Uncategorized'
        ])

    return response


@login_required(login_url='/authlogin/login')
def import_products(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('imported_file')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'File is not CSV type')
            return redirect('product_list')

        try:
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            next(io_string)  # Skip the header row

            for column in csv.reader(io_string, delimiter=',', quotechar="|"):
                barcode = column[0] if column[0] else Product.generate_barcode()
                category, _ = Category.objects.get_or_create(name=column[7])

                Product.objects.update_or_create(
                    barcode=barcode,
                    defaults={
                        'name': column[1],
                        'buying_price': column[2],
                        'selling_price': column[3],
                        'stock_quantity': column[4],
                        'expiry_date': column[5],
                        'packaging_type': column[6],
                        'category': category
                    }
                )
            messages.success(request, 'Products imported successfully!')
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            return redirect('product_list')

    return redirect('product_list')


@login_required(login_url='/authlogin/login')
def product_live_search(request):
    query = request.GET.get('q', '').strip().lower()  # Get the query and convert to lowercase
    if query:
        # Case-insensitive search for product name or barcode
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(barcode__icontains=query)
        ).values('id', 'name', 'barcode', 'selling_price', 'stock_quantity')

        # Convert the result to a list of dictionaries
        results = list(products)
    else:
        results = []

    return JsonResponse(results, safe=False)


@require_POST
@login_required(login_url='/authlogin/login')
def delete_selected_products(request):
    try:
        data = json.loads(request.body)
        product_ids = data.get('selected_products', [])

        if product_ids:
            Product.objects.filter(id__in=product_ids).delete()
            return JsonResponse({'status': 'success', 'message': 'Selected products deleted successfully.'})

        return JsonResponse({'status': 'error', 'message': 'No products selected.'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})



