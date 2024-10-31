from django import forms
from .models import Product, Category, Batch


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'parent']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'barcode', 'buying_price', 'selling_price', 'wholesale_price',
            'stock_quantity', 'low_stock_threshold', 'packaging_type', 'expiry_date', 'category'
        ]

    def clean_stock_quantity(self):
        stock_quantity = self.cleaned_data.get('stock_quantity')
        if stock_quantity < 0:
            raise forms.ValidationError("Stock quantity cannot be negative.")
        return stock_quantity


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['quantity', 'price', 'expiry_date']

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 0:
            raise forms.ValidationError("Batch quantity cannot be negative.")
        return quantity


class ProductImportForm(forms.Form):
    imported_file = forms.FileField(
        label='Upload CSV or Excel File',
        widget=forms.FileInput(attrs={'accept': '.csv,.xlsx'})
    )

    def clean_imported_file(self):
        file = self.cleaned_data.get('imported_file')
        if not file.name.endswith('.csv') and not file.name.endswith('.xlsx'):
            raise forms.ValidationError("Only CSV or Excel files are supported.")
        return file
