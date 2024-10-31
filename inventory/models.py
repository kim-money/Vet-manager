from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, datetime
import random
import string


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subcategories', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def clean(self):
        if self.parent and self.parent == self:
            raise ValidationError("A category cannot be its own parent.")
        if self.parent and self.parent.is_subcategory():
            raise ValidationError("A category cannot have a subcategory as its parent.")

    def is_subcategory(self):
        return self.parent is not None


class Product(models.Model):
    name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=255, blank=True, null=True, unique=True)
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Optional
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=0)  # To trigger low stock alert
    packaging_type = models.CharField(max_length=50, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.barcode if self.barcode else ''} {self.name}"

    def clean(self):
        if self.selling_price <= self.buying_price:
            raise ValidationError("Selling price must be greater than buying price.")
        if self.stock_quantity < 0:
            raise ValidationError("Stock quantity cannot be negative.")
        if self.low_stock_threshold < 0:
            raise ValidationError("Low stock threshold cannot be negative.")

    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = self.generate_barcode()
        self.clean()
        super().save(*args, **kwargs)

    def generate_barcode(self):
        return ''.join(random.choices(string.digits, k=12))

    def receive_stock(self, quantity):
        if quantity < 0:
            raise ValidationError("Cannot receive negative stock.")
        self.stock_quantity += quantity
        self.save()

    def is_nearing_expiry(self):
        if self.expiry_date:
            return timezone.now().date() >= (self.expiry_date - timedelta(days=30))
        return False

    def has_expired(self):
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False

    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold


class Batch(models.Model):
    product = models.ForeignKey(Product, related_name='batches', on_delete=models.CASCADE)
    batch_code = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Batch {self.batch_code} for {self.product.name}"

    def save(self, *args, **kwargs):
        if not self.batch_code:
            self.batch_code = self.generate_batch_code()
        super().save(*args, **kwargs)

    def generate_batch_code(self):
        date_stamp = datetime.now().strftime("%Y%m%d")
        return f"{self.product.name.replace(' ', '_')}.{date_stamp}"
