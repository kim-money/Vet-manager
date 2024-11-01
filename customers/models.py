from django.db import models

class Customer(models.Model):
    customer_id = models.CharField(max_length=10, unique=True, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    # New fields to handle credit
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    credit_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Amount owed by the customer

    def save(self, *args, **kwargs):
        if not self.customer_id:
            max_id = Customer.objects.aggregate(max_id=models.Max('id'))['max_id']
            new_id = max_id + 1 if max_id else 1
            self.customer_id = f'CST{new_id:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    # Method to check if the customer can make a purchase on credit
    def can_purchase_on_credit(self, amount):
        return self.credit_balance + amount <= self.credit_limit
