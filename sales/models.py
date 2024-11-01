from django.db import models
from django.conf import settings
from customers.models import Customer
from inventory.models import Product, Batch
from decimal import Decimal
from django.utils.timezone import now


class Sale(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('credit', 'Credit'),
    ]

    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    cash_given = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    change_due = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    credit_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sale_date = models.DateTimeField(default=now)
    mpesa_reference = models.CharField(max_length=255, blank=True, null=True)
    is_complete = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Sale #{self.id} - {self.total_amount}"

    @property
    def outstanding_credit(self):
        if self.payment_method == 'credit':
            return self.total_amount - (self.credit_amount or 0)
        return 0


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)  # Link to specific batch
    quantity = models.PositiveIntegerField()
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.selling_price
        super().save(*args, **kwargs)
        self.reduce_stock()

    def reduce_stock(self):
        # FIFO: Sort batches by expiry date or creation date
        batches = Batch.objects.filter(product=self.product).order_by('expiry_date')
        quantity_needed = self.quantity

        for batch in batches:
            if batch.quantity >= quantity_needed:
                batch.quantity -= quantity_needed
                batch.save()
                break
            else:
                quantity_needed -= batch.quantity
                batch.quantity = 0
                batch.save()

        self.product.stock_quantity -= self.quantity
        self.product.save()
