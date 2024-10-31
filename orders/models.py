from django.db import models
from suppliers.models import Supplier
from inventory.models import Product

class Order(models.Model):
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_received = models.BooleanField(default=False)  # New field to track if the order has been received

    def save(self, *args, **kwargs):
        if not self.order_number:
            max_id = Order.objects.aggregate(max_id=models.Max('id'))['max_id']
            new_id = max_id + 1 if max_id else 1
            self.order_number = f'ORD{new_id:06d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_ordered = models.PositiveIntegerField()
    quantity_delivered = models.PositiveIntegerField(default=0)  # New field for tracking delivered quantity
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} ({self.quantity_ordered})"
