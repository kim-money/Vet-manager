import logging
from decimal import Decimal
from django.core.paginator import Paginator
from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils.timezone import timedelta
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from .forms import SaleForm, SaleItemForm
from .models import Sale, SaleItem
from inventory.models import Product
from customers.models import Customer
from shop_details.models import Shop  
from django.db.models import Q
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages



logger = logging.getLogger('sales')


@login_required(login_url='/authlogin/login')
def dashboard(request):
    # Get today's date
    today = timezone.now().date()

    # Query for today's sales data
    daily_sales = Sale.objects.filter(sale_date__date=today).aggregate(
        total_sales=Sum('total_amount'),
        cash_sales=Sum('total_amount', filter=Q(payment_method='cash')),
        mpesa_sales=Sum('total_amount', filter=Q(payment_method='mpesa')),
        credit_sales=Sum('total_amount', filter=Q(payment_method='credit'))
    )

    # Calculate weekly sales data (starting from Monday)
    start_of_week = today - timedelta(days=today.weekday())
    weekly_sales = Sale.objects.filter(sale_date__date__gte=start_of_week).aggregate(
        total_sales=Sum('total_amount'),
        cash_sales=Sum('total_amount', filter=Q(payment_method='cash')),
        mpesa_sales=Sum('total_amount', filter=Q(payment_method='mpesa')),
        credit_sales=Sum('total_amount', filter=Q(payment_method='credit'))
    )

    # Calculate monthly sales data
    start_of_month = today.replace(day=1)
    monthly_sales = Sale.objects.filter(sale_date__date__gte=start_of_month).aggregate(
        total_sales=Sum('total_amount'),
        cash_sales=Sum('total_amount', filter=Q(payment_method='cash')),
        mpesa_sales=Sum('total_amount', filter=Q(payment_method='mpesa')),
        credit_sales=Sum('total_amount', filter=Q(payment_method='credit'))
    )

    # Calculate last six months' sales data
    six_months_ago = today - timedelta(days=6 * 30)
    six_months_sales = Sale.objects.filter(sale_date__date__gte=six_months_ago).annotate(
        month=TruncMonth('sale_date')
    ).values('month').annotate(
        total_sales=Sum('total_amount'),
        cash_sales=Sum('total_amount', filter=Q(payment_method='cash')),
        mpesa_sales=Sum('total_amount', filter=Q(payment_method='mpesa')),
        credit_sales=Sum('total_amount', filter=Q(payment_method='credit'))
    ).order_by('month')

    context = {
        'daily_sales': daily_sales,
        'weekly_sales': weekly_sales,
        'monthly_sales': monthly_sales,
        'six_months_sales': list(six_months_sales)
    }

    return render(request, 'sales/sale_dashboard.html', context)


@login_required(login_url='/authlogin/login')
def sales_list(request):
    sales = Sale.objects.all().order_by('-sale_date')
    paginator = Paginator(sales, 25)  # Show 25 sales per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'sales': page_obj,
    }
    return render(request, 'sales/sales_list.html', context)


@login_required(login_url='/authlogin/login')
def sale_detail(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    sale_items = SaleItem.objects.filter(sale=sale)

    context = {
        'sale': sale,
        'sale_items': sale_items,
    }
    return render(request, 'sales/sale_detail.html', context)


@csrf_exempt
@transaction.atomic
@login_required(login_url='/authlogin/login')
def make_sale(request):
    if request.method == 'GET':
        # Render the "Make Sale" page for GET requests
        shop = Shop.objects.first()  # Fetch shop details
        return render(request, 'sales/make_sale.html', {
            'shop': shop,
            'user': request.user
        })

    elif request.method == 'POST':
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            items = data.get('items', [])
            payment_method = data.get('payment_method')
            customer_id = data.get('customer_id', None)

            # Safely handle optional fields
            cash_given = Decimal(data.get('cash_given', 0)) if data.get('cash_given') is not None else Decimal('0.00')
            credit_paid = Decimal(data.get('credit_paid', 0)) if data.get('credit_paid') is not None else Decimal(
                '0.00')
            mpesa_reference = data.get('mpesa_reference', None)

            # Validate the presence of sale items
            if not items:
                return JsonResponse({'status': 'error', 'message': 'No items provided for the sale.'}, status=400)

            # Retrieve or set customer information (if applicable)
            customer = None
            if customer_id:
                try:
                    customer = Customer.objects.get(id=customer_id)
                except Customer.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Customer not found.'}, status=404)

            # Calculate total amount from the sale items
            total_amount = Decimal(0)
            for item in items:
                product_id = item.get('product_id')
                if not product_id:
                    return JsonResponse({'status': 'error', 'message': 'Missing product_id in sale items.'}, status=400)

                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f'Product with id {product_id} not found.'},
                                        status=404)

                quantity = int(item.get('quantity', 0))
                if quantity <= 0:
                    return JsonResponse({'status': 'error', 'message': f'Invalid quantity for product {product.name}.'},
                                        status=400)

                price = Decimal(item.get('price', 0))
                subtotal = price * quantity
                total_amount += subtotal

            # Handle payment method and calculate any due amounts
            if payment_method == 'cash':
                change_due = cash_given - total_amount
            else:
                change_due = Decimal('0.00')

            if payment_method == 'credit':
                balance_due = total_amount - credit_paid
            else:
                balance_due = Decimal('0.00')

            # Create the sale
            sale = Sale.objects.create(
                customer=customer,
                total_amount=total_amount,
                payment_method=payment_method,
                cash_given=cash_given if payment_method == 'cash' else None,
                change_due=change_due if payment_method == 'cash' else None,
                credit_amount=credit_paid if payment_method == 'credit' else None,
                mpesa_reference=mpesa_reference if payment_method == 'mpesa' else None,
                is_complete=True,
                user=request.user
            )

            # Process sale items and reduce product stock
            for item in items:
                product = Product.objects.get(id=item['product_id'])
                quantity = int(item['quantity'])

                # Reduce stock quantity
                if product.stock_quantity < quantity:
                    return JsonResponse({'status': 'error', 'message': f'Not enough stock for product {product.name}.'},
                                        status=400)



                # Create sale item entry
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    selling_price=Decimal(item['price']),
                    subtotal=Decimal(item['price']) * quantity
                )

            return JsonResponse({
                'status': 'success',
                'sale_id': sale.id,
                'total_amount': str(total_amount),
                'change_due': str(change_due),
                'balance_due': str(balance_due)
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


def receipt_view(request, sale_id):
    # Retrieve the sale using the provided sale ID
    sale = get_object_or_404(Sale, id=sale_id)

    # Retrieve all the sale items related to the sale
    sale_items_data = sale.items.all()

    # Calculate credit-related details if the payment method is credit
    credit_paid = sale.credit_amount if sale.payment_method == 'credit' else None
    balance_due = sale.total_amount - (credit_paid or 0) if sale.payment_method == 'credit' else 0

    # Prepare the shop details, handle case if no shop record exists
    shop = Shop.objects.first()

    context = {
        'items': sale_items_data,
        'total_amount': sale.total_amount,
        'payment_method': sale.get_payment_method_display(),  # Display payment method properly
        'credit_amount': credit_paid,
        'balance_due': balance_due,
        'cash_given': sale.cash_given if sale.payment_method == 'cash' else None,  # Show only for cash payments
        'change_due': sale.change_due if sale.payment_method == 'cash' else None,  # Show only for cash payments
        'mpesa_reference': sale.mpesa_reference if sale.payment_method == 'mpesa' else None,  # Show for Mpesa payments
        'served_by': sale.user.username,
        'sale_date': sale.sale_date.strftime('%Y-%m-%d %H:%M:%S'),
        'shop': shop  # Shop details for receipt
    }

    return render(request, 'sales/receipt.html', context)


@login_required(login_url='/authlogin/login')
def search_products(request):
    query = request.GET.get('q', '').strip().lower()
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(barcode__icontains=query)
    ).values('id', 'name', 'barcode', 'selling_price', 'stock_quantity')
    return JsonResponse(list(products), safe=False)


@login_required(login_url='/authlogin/login')
def search_customers(request):
    query = request.GET.get('q', '').strip().lower()
    customers = Customer.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(phone__icontains=query)
    ).values('id', 'first_name', 'last_name', 'phone')
    return JsonResponse(list(customers), safe=False)


@login_required(login_url='/authlogin/login')
@transaction.atomic
def update_sale(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    # Create a formset for SaleItems
    SaleItemFormSet = modelformset_factory(SaleItem, form=SaleItemForm, extra=0, can_delete=True)

    if request.method == 'POST':
        # Handle sale form data and sale items formset
        sale_form = SaleForm(request.POST, instance=sale)
        sale_item_formset = SaleItemFormSet(request.POST, queryset=SaleItem.objects.filter(sale=sale))

        if sale_form.is_valid() and sale_item_formset.is_valid():
            sale_form.save()

            sale_items = sale_item_formset.save(commit=False)
            # Update each sale item and adjust product stock as necessary
            for item in sale_items:
                original_item = SaleItem.objects.get(id=item.id)
                stock_adjustment = original_item.quantity - item.quantity
                item.batch.product.stock_quantity += stock_adjustment
                item.batch.product.save()

                item.save()

            return redirect('sales_list')  # Redirect after successful update
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid form data'})

    else:
        # Prepopulate the sale and sale items in the formset
        sale_form = SaleForm(instance=sale)
        sale_item_formset = SaleItemFormSet(queryset=SaleItem.objects.filter(sale=sale))

        context = {
            'sale': sale,
            'sale_form': sale_form,
            'sale_items': sale_item_formset,  # Pass the formset to the template
        }

        return render(request, 'sales/update_sale.html', context)



@login_required(login_url='/authlogin/login')
def delete_sale(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    if request.method == 'POST':
        # Return sold items back to stock before deleting the sale
        for item in sale.items.all():
            product = item.product
            product.stock_quantity += item.quantity  # Add the sold quantity back to the product's stock
            product.save()

        # Delete the sale and its items
        sale.delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # Check for AJAX request
            return JsonResponse({'success': True})
        else:
            messages.success(request, 'Sale deleted successfully and stock quantities restored.')
            return redirect('sales_list')

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


@login_required(login_url='/authlogin/login')
def edit_sale(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)

    if request.method == 'GET':
        # Send sale data to the modal
        data = {
            'total_amount': sale.total_amount,
            'payment_method': sale.payment_method,
            'customer': sale.customer.id if sale.customer else ''
        }
        return JsonResponse(data)

    elif request.method == 'POST':
        # Update sale details
        sale.total_amount = request.POST.get('total_amount')
        sale.payment_method = request.POST.get('payment_method')
        customer_id = request.POST.get('customer')
        if customer_id:
            sale.customer = get_object_or_404(Customer, id=customer_id)
        sale.save()
        return redirect('sales_list')