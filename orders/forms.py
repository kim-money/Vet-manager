from django import forms
from .models import OrderItem, Order
from inventory.models import Product


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['supplier']

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields['supplier'].widget.attrs.update({'class': 'form-control'})


class OrderItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="-- Select a Product --"
    )
    quantity_ordered = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Quantity Ordered"
    )
    buying_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Buying Price"
    )

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity_ordered', 'buying_price']

    def __init__(self, *args, **kwargs):
        super(OrderItemForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['buying_price'].initial = self.instance.product.buying_price
        else:
            self.fields['buying_price'].initial = None
