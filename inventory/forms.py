# inventory/forms.py

from django import forms
from .models import Product, Category

class ProductForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    new_category = forms.CharField(
        required=False,
        label="Add New Category",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'New Category'})
    )

    class Meta:
        model = Product
        fields = ['name', 'category', 'new_category', 'price', 'stock']  # Removed 'description' if it's not needed
