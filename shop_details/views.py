from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from .models import Shop
from .forms import ShopForm



@login_required(login_url='/authlogin/login/')
def shop_details(request):
    shop = Shop.objects.first()  
    return render(request, 'shop_details/shop_details.html', {'shop': shop})


@login_required(login_url='/authlogin/login/')
def edit_shop_details(request):
    shop = Shop.objects.first()
    if request.method == 'POST':
        form = ShopForm(request.POST, request.FILES, instance=shop)
        if form.is_valid():
            form.save()
            return redirect('shop_details')
        else:
           return render(request, 'shop_details/edit_shop_details.html', {'form': form})
    else:
        form = ShopForm(instance=shop)
    return render(request, 'shop_details/edit_shop_details.html', {'form': form})


