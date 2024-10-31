from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_order, name='create_order'),
    path('search/suppliers/', views.supplier_search, name='supplier_search'),
    path('search/products/', views.product_search, name='product_search'),
    path('detail/<str:order_number>/', views.order_detail, name='order_detail'),
    path('add-order-product/', views.add_order_product, name='add_order_product'),
    path('', views.list_orders, name='list_orders'),
    path('receive/<str:order_number>/', views.receive_stock, name='receive_stock'),
    path('download_lpo_pdf/<str:order_number>/', views.generate_lpo_pdf, name='download_lpo_pdf'),
    path('download_receipt_pdf/<str:order_number>/', views.generate_receipt_pdf, name='download_receipt_pdf'),
    path('order/<str:order_number>/pdf/', views.generate_lpo_pdf, name='generate_lpo_pdf'),
    path('order/<str:order_number>/receipt/', views.generate_receipt_pdf, name='generate_receipt_pdf'),

]
