# inventory/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add_order/<int:product_id>/', views.add_order, name='add_order'),
    path('remove_order/<int:order_id>/', views.remove_order, name='remove_order'),
]
