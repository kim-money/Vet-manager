from django.urls import path
from . import views

urlpatterns = [
    path('', views.shop_details, name='shop_details'),
    path('shop/edit/', views.edit_shop_details, name='edit_shop_details'),
]