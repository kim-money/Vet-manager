# inventory/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Order, Category, Product, Order, OrderItem
from .forms import ProductForm, OrderForm, OrderItemForm
from django.db.models import Q
from django.forms import formset_factory
from django.contrib import messages
from django.http import JsonResponse
import json

@login_required(login_url='/authlogin/login/')
def product_list(request):
    query = request.GET.get('search', '')
    category_id = request.GET.get('category', None)
    products = Product.objects.filter(stock__gt=0)

    if query:
        products = products.filter(Q(name__icontains=query) | Q(category__name__icontains=query))
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    categories = Category.objects.all()
    return render(request, 'inventory/product_list.html', {'products': products, 'categories': categories})

@login_required(login_url='/authlogin/login/')
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data['category']
            new_category = form.cleaned_data['new_category']

            # Create new category if provided
            if not category and new_category:
                category, created = Category.objects.get_or_create(name=new_category)

            # Save the product with the selected or newly created category
            product = form.save(commit=False)
            product.category = category
            product.save()
            
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'inventory/add_product.html', {'form': form})

@login_required(login_url='/authlogin/login/')
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/edit_product.html', {'form': form})

def delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'inventory/delete_product.html', {'product': product})

def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'inventory/product_detail.html', {'product': product})

@login_required(login_url='/authlogin/login/')
def remove_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    order.product.stock += order.quantity  # Add the stock back
    order.product.save()
    order.delete()
    
    messages.success(request, 'Order removed successfully.')
    return redirect('product_list')

@login_required(login_url='/authlogin/login/')
def create_order(request):
    OrderItemFormSet = formset_factory(OrderItemForm, extra=1)
    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        if order_form.is_valid() and formset.is_valid():
            order = order_form.save()
            for form in formset:
                order_item = form.save(commit=False)
                order_item.order = order
                order_item.save()
            return redirect('product_list')
    else:
        order_form = OrderForm()
        formset = OrderItemFormSet()

    return render(request, 'inventory/add_order.html', {
        'order_form': order_form,
        'formset': formset,
    })


def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query)
    results = [{'id': product.id, 'name': product.name, 'buying_price': float(product.price), 'stock_quantity': product.stock} for product in products]
    return JsonResponse(results, safe=False)
