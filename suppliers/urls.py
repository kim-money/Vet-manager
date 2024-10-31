from django.urls import path
from . import views

urlpatterns = [
    path('', views.supplier_list, name='supplier_list'),
    path('add/', views.add_supplier, name='add_supplier'),
    path('<str:supplier_id>/edit/', views.edit_supplier, name='edit_supplier'),
    path('<str:supplier_id>/delete/', views.delete_supplier, name='delete_supplier'),
    path('view/<str:supplier_id>/', views.view_supplier, name='view_supplier'),
]
