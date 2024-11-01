from django.urls import path
from .views import make_sale, search_products, search_customers, sales_list, sale_detail, \
    dashboard, receipt_view, update_sale, delete_sale

urlpatterns = [
    path('', dashboard, name='sale_dashboard'),
    path('make_sale/', make_sale, name='make_sale'),  # Keep one of these
    path('list/', sales_list, name='sales_list'),
    path('detail/<int:sale_id>/', sale_detail, name='sale_detail'),
    path('search_products/', search_products, name='search_products'),
    path('search_customers/', search_customers, name='search_customers'),
    path('print_receipt/<int:sale_id>/', receipt_view, name='print_receipt'),
    path('sales/<int:sale_id>/update/', update_sale, name='update_sale'),  # Make sure this exists
    path('sales/<int:sale_id>/delete/', delete_sale, name='delete_sale'),  # Optional: make it consistent with update
]
