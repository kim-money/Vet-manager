from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'first_name', 'last_name', 'phone', 'email', 'date_added')
    search_fields = ('first_name', 'last_name', 'phone', 'email', 'customer_id')
