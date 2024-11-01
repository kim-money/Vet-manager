from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('add/', views.customer_add, name='customer_add'),
    path('export/', views.export_customers, name='export_customers'),  # Put export before dynamic ID
    path('import/', views.import_customers, name='import_customers'),  # Put import before dynamic ID
    path('credit_payment/<str:customer_id>/', views.make_credit_payment, name='make_credit_payment'),
    path('<str:id>/edit/', views.customer_edit, name='customer_edit'),
    path('<str:id>/delete/', views.customer_delete, name='customer_delete'),
    path('<str:id>/', views.customer_detail, name='customer_detail'),  # This should be last
]
