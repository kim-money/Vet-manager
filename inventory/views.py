# inventory/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Product, Order, Category

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

def add_order(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if product.stock > 0:
        Order.objects.create(product=product, quantity=1)
        product.stock -= 1
        product.save()
    return redirect('product_list')

def remove_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    order.product.stock += order.quantity
    order.product.save()
    order.delete()
    return redirect('product_list')
