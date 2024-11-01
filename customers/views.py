from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from sales.models import Sale
from .models import Customer
from .forms import CustomerForm
from django.http import JsonResponse
from decimal import Decimal
import csv
from django.http import HttpResponse


@login_required(login_url='/auth/login/')
def customer_detail(request, id):
    customer = get_object_or_404(Customer, customer_id=id)
    sales = Sale.objects.filter(customer=customer)
    return render(request, 'customers/customer_detail.html', {
        'customer': customer,
        'sales': sales,
    })


@login_required(login_url='/auth/login/')
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'customers/customer_list.html', {'customers': customers})



@login_required(login_url='/auth/login/')
def customer_add(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'customers/add_customer.html', {'form': form})

@login_required(login_url='/auth/login/')
def customer_edit(request, id):
    customer = get_object_or_404(Customer, customer_id=id)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_detail', id=customer.customer_id)
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'customers/customer_edit.html', {'form': form, 'customer': customer})

@login_required(login_url='/auth/login/')
def customer_delete(request, id):
    customer = get_object_or_404(Customer, customer_id=id)
    if request.method == "POST":
        customer.delete()
        return redirect('customer_list')
    return render(request, 'customers/customer_confirm_delete.html', {'customer': customer})

# Additional view to handle customer payments toward credit
@login_required(login_url='/auth/login/')
def make_credit_payment(request, customer_id):
    customer = get_object_or_404(Customer, customer_id=customer_id)
    if request.method == "POST":
        payment_amount = Decimal(request.POST.get('payment_amount'))
        if payment_amount <= customer.credit_balance:
            customer.credit_balance -= payment_amount
            customer.save()
            return redirect('customer_detail', id=customer.customer_id)
        else:
            return JsonResponse({'error': 'Payment exceeds the customer’s credit balance.'})
    return render(request, 'customers/make_credit_payment.html', {'customer': customer})


@login_required(login_url='/auth/login/')
def export_customers(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers.csv"'

    writer = csv.writer(response)
    # Write the header row
    writer.writerow(
        ['Customer ID', 'First Name', 'Last Name', 'Phone', 'Email', 'Address', 'Credit Limit', 'Credit Balance',
         'Date Added'])

    # Write the data rows
    for customer in Customer.objects.all():
        writer.writerow([customer.customer_id, customer.first_name, customer.last_name, customer.phone, customer.email,
                         customer.address, customer.credit_limit, customer.credit_balance, customer.date_added])

    return response


@login_required(login_url='/auth/login/')
def import_customers(request):
    if request.method == 'POST':
        csv_file = request.FILES['file']
        if not csv_file.name.endswith('.csv'):
            return render(request, 'customers/import_customers.html', {'error': 'Please upload a CSV file.'})

        # Read CSV and create customer records
        file_data = csv_file.read().decode('UTF-8').splitlines()
        reader = csv.DictReader(file_data)

        for row in reader:
            Customer.objects.create(
                first_name=row['First Name'],
                last_name=row['Last Name'],
                phone=row['Phone'],
                email=row['Email'],
                address=row['Address'],
                credit_limit=row['Credit Limit'],
                credit_balance=row['Credit Balance']
            )
        return redirect('customer_list')

    return render(request, 'customers/import_customers.html')

