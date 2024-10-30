# inventory/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/add/', views.add_product, name='add_product'),
    path('product/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('remove_order/<int:order_id>/', views.remove_order, name='remove_order'),
    path('order/new/', views.create_order, name='add_order'),
    path('order/search/products/', views.search_products, name='search_products')
    
]
