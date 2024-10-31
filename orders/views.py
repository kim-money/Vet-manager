from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.contrib import messages
from shop_details.models import Shop
from .models import Order, OrderItem
from inventory.forms import ProductForm
from .forms import OrderForm, OrderItemForm
from inventory.models import Product, Batch
from suppliers.models import Supplier
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
import json
from datetime import datetime


@login_required(login_url='/auth/login/')
def list_orders(request):
    """List all orders with pagination."""
    orders = Order.objects.all().order_by('-created_at')
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'orders/list_orders.html', {'page_obj': page_obj})


@login_required(login_url='/auth/login/')
def order_detail(request, order_number):
    """Show order details including items and totals."""
    order = get_object_or_404(Order, order_number=order_number)

    items = []
    total = 0
    for item in order.items.all():
        subtotal = item.buying_price * item.quantity_ordered  # Calculate the subtotal
        items.append({
            'product_name': item.product.name,
            'quantity': item.quantity_ordered,
            'buying_price': item.buying_price,
            'subtotal': subtotal,
        })
        total += subtotal

    context = {
        'order': order,
        'items': items,
        'total': total,
    }
    return render(request, 'orders/order_detail.html', context)


@login_required(login_url='/auth/login/')
def create_order(request):
    """Create a new order with multiple items."""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        items_data = request.POST.get('items_data')

        if form.is_valid() and items_data:
            order = form.save()

            items = json.loads(items_data)
            for item in items:
                product = Product.objects.get(id=item['product_id'])
                quantity_ordered = item['quantity']
                buying_price = item.get('buying_price', product.buying_price)

                # Ensure buying_price is set
                if buying_price is None:
                    return render(request, 'orders/create_order.html', {
                        'form': form,
                        'error': 'Buying price is required for all order items.'
                    })

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity_ordered=quantity_ordered,
                    buying_price=buying_price
                )

            return redirect('order_detail', order_number=order.order_number)

    else:
        form = OrderForm()

    return render(request, 'orders/create_order.html', {'form': form})


@login_required(login_url='/auth/login/')
def receive_stock(request, order_number):
    """Receive stock for an order and create batches for products."""
    order = get_object_or_404(Order, order_number=order_number)

    if request.method == 'POST':
        for item in order.items.all():
            product = item.product
            quantity_received = int(request.POST.get(f'quantity_received_{item.id}', item.quantity_ordered))
            new_buying_price = float(request.POST.get(f'buying_price_{item.id}', product.buying_price))
            new_selling_price = float(request.POST.get(f'selling_price_{item.id}', product.selling_price))
            expiry_date = request.POST.get(f'expiry_date_{item.id}', None)

            # Update product's stock and prices
            product.stock_quantity += quantity_received
            product.buying_price = new_buying_price
            product.selling_price = new_selling_price
            product.save()

            # Create a batch for the product
            batch_code = f"{product.name.replace(' ', '_')}.{datetime.now().strftime('%Y%m%d')}"
            Batch.objects.create(
                product=product,
                batch_code=batch_code,
                quantity=quantity_received,
                price=new_buying_price,
                expiry_date=expiry_date if expiry_date else None
            )

        # Mark the order as received
        order.is_received = True
        order.save()

        messages.success(request, f'Stock received for order {order.order_number}')
        return redirect('order_detail', order_number=order.order_number)

    return render(request, 'orders/receive_stock.html', {'order': order})


@login_required(login_url='/auth/login/')
def add_order_product(request):
    """Add a new product to the order."""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            return JsonResponse({
                'id': product.id,
                'name': product.name,
                'buying_price': product.buying_price,
            }, status=201)
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = ProductForm()

    return render(request, 'inventory/add_product.html', {'form': form})


def supplier_search(request):
    """AJAX search for suppliers."""
    query = request.GET.get('q', '').strip()
    suppliers = Supplier.objects.filter(name__icontains=query)[:10]
    results = [{'supplier_id': supplier.id, 'name': supplier.name} for supplier in suppliers]
    return JsonResponse(results, safe=False)


def product_search(request):
    """AJAX search for products."""
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(name__icontains=query)[:10]
    results = [{'id': product.id, 'name': product.name, 'stock_quantity': product.stock_quantity,
                'buying_price': product.buying_price} for product in products]
    return JsonResponse(results, safe=False)


@login_required(login_url='/auth/login/')
def generate_lpo_pdf(request, order_number):
    """Generate a PDF for the order's Local Purchase Order (LPO)."""
    order = get_object_or_404(Order, order_number=order_number)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{order.order_number}_LPO.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    shop = Shop.objects.first()

    if shop.logo:
        logo = Image(shop.logo.path, width=1.5 * inch, height=1.5 * inch)
        elements.append(Spacer(1, 6))
        elements.append(logo)

    left_column = [
        Paragraph(shop.name, styles['Title']),
        Paragraph(f"Address: {shop.address}", styles['Normal']),
        Paragraph(f"Phone: {shop.phone}", styles['Normal']),
        Paragraph(f"Website: {shop.website}", styles['Normal']) if shop.website else '',
    ]

    right_column = [
        Paragraph("<b>LPO Details</b>", styles['Title']),
        Paragraph(f"DATE: {order.updated_at.strftime('%Y-%m-%d')}", styles['Normal']),
        Paragraph(f"PO #: {order.order_number}", styles['Normal']),
    ]

    data = [[left_column, right_column]]
    header_table = Table(data, colWidths=[4 * inch, 3 * inch])
    header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('ALIGN', (1, 0), (1, 0), 'RIGHT')]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    supplier_info = [
        [
            [
                Paragraph("<b>SUPPLIER</b>", styles['Heading2']),
                Paragraph(order.supplier.name, styles['Normal']),
                Paragraph(order.supplier.address, styles['Normal']),
                Paragraph(f"City: {order.supplier.city}, {order.supplier.country}", styles['Normal']),
                Paragraph(f"Phone: {order.supplier.phone}", styles['Normal']),
            ],
            [
                Paragraph("<b>SHIPPING ADDRESS</b>", styles['Heading2']),
                Paragraph(shop.address, styles['Normal']),
                Paragraph(f"{shop.phone}", styles['Normal']),
            ]
        ]
    ]
    supplier_table = Table(supplier_info, colWidths=[4 * inch, 3 * inch])
    supplier_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(supplier_table)
    elements.append(Spacer(1, 12))

    order_items = [["Product Name", "Quantity", "Buying Price", "Subtotal"]]
    total = 0
    for item in order.items.all():
        quantity = item.quantity_ordered
        subtotal = quantity * item.buying_price
        total += subtotal
        order_items.append([item.product.name, str(quantity), f"{item.buying_price:.2f}", f"{subtotal:.2f}"])

    order_items.append(["", "", "Total", f"{total:.2f}"])
    order_table = Table(order_items, colWidths=[3 * inch, 1.5 * inch, 1.5 * inch, 2 * inch])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.green),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(order_table)

    doc.build(elements)
    return response


@login_required(login_url='/auth/login/')
def generate_receipt_pdf(request, order_number):
    """Generate a PDF for the order's receipt."""
    order = get_object_or_404(Order, order_number=order_number)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{order.order_number}_Receipt.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    shop = Shop.objects.first()

    if shop.logo:
        logo = Image(shop.logo.path, width=1.5 * inch, height=1.5 * inch)
        elements.append(Spacer(1, 6))
        elements.append(logo)

    left_column = [
        Paragraph(shop.name, styles['Title']),
        Paragraph(f"Address: {shop.address}", styles['Normal']),
        Paragraph(f"Phone: {shop.phone}", styles['Normal']),
        Paragraph(f"Website: {shop.website}", styles['Normal']) if shop.website else '',
    ]

    right_column = [
        Paragraph("<b>Receipt Details</b>", styles['Title']),
        Paragraph(f"DATE: {order.updated_at.strftime('%Y-%m-%d')}", styles['Normal']),
        Paragraph(f"Receipt #: {order.order_number}", styles['Normal']),
    ]

    data = [[left_column, right_column]]
    header_table = Table(data, colWidths=[4 * inch, 3 * inch])
    header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('ALIGN', (1, 0), (1, 0), 'RIGHT')]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    supplier_info = [
        [
            [
                Paragraph("<b>SUPPLIER</b>", styles['Heading2']),
                Paragraph(order.supplier.name, styles['Normal']),
                Paragraph(order.supplier.address, styles['Normal']),
                Paragraph(f"City: {order.supplier.city}, {order.supplier.country}", styles['Normal']),
                Paragraph(f"Phone: {order.supplier.phone}", styles['Normal']),
            ],
            [
                Paragraph("<b>SHIPPING ADDRESS</b>", styles['Heading2']),
                Paragraph(shop.address, styles['Normal']),
                Paragraph(f"{shop.phone}", styles['Normal']),
            ]
        ]
    ]
    supplier_table = Table(supplier_info, colWidths=[4 * inch, 3 * inch])
    supplier_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(supplier_table)
    elements.append(Spacer(1, 12))

    order_items = [["Product Name", "Quantity", "Buying Price", "Subtotal"]]
    total = 0
    for item in order.items.all():
        quantity = item.quantity_ordered
        subtotal = quantity * item.buying_price
        total += subtotal
        order_items.append([item.product.name, str(quantity), f"{item.buying_price:.2f}", f"{subtotal:.2f}"])

    order_items.append(["", "", "Total", f"{total:.2f}"])
    order_table = Table(order_items, colWidths=[3 * inch, 1.5 * inch, 1.5 * inch, 2 * inch])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.green),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(order_table)

    doc.build(elements)
    return response
