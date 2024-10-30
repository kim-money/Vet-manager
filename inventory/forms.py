# inventory/forms.py

from django import forms
from .models import Product, Category, Order, OrderItem

class ProductForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    new_category = forms.CharField(
        required=False,
        label="Or New Category",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'New Category'})
    )

    class Meta:
        model = Product
        fields = ['name', 'category', 'new_category', 'price', 'stock'] 

class OrderForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="Select Product",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        label="Quantity",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'})
    )
    buying_price = forms.DecimalField(
        max_digits=10, decimal_places=2,
        label="Buying Price",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter buying price'})
    )

    class Meta:
        model = Order
        fields = []  # No direct fields from Order itself; items are added through OrderItems

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'buying_price']