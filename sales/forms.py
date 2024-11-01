from django import forms
from .models import Sale, SaleItem

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['customer', 'payment_method', 'cash_given', 'credit_amount']

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        cash_given = cleaned_data.get('cash_given')
        credit_amount = cleaned_data.get('credit_amount')

        if payment_method == 'credit' and not credit_amount:
            raise forms.ValidationError("Credit amount is required for credit payments.")
        return cleaned_data

class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['batch', 'quantity']

    def clean(self):
        cleaned_data = super().clean()
        batch = cleaned_data.get('batch')
        quantity = cleaned_data.get('quantity')

        if batch and quantity:
            if batch.quantity < quantity:
                raise forms.ValidationError("Not enough stock in the selected batch.")
        return cleaned_data
