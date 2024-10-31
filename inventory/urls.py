from django.urls import path
from . import views

urlpatterns = [
    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<int:pk>/edit/', views.edit_category, name='edit_category'),

    # Product URLs
    path('', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:pk>/delete/', views.delete_product, name='delete_product'),
    path('products/delete/', views.delete_selected_products, name='delete_selected_products'),
    path('products/export/', views.export_products, name='export_products'),
    path('products/import/', views.import_products, name='import_products'),
    path('products/print-barcodes/', views.print_barcodes, name='print_barcodes'),

    # Live Search (Updated to case-insensitive search)
    path('products/live-search/', views.product_live_search, name='product_live_search'),
]
