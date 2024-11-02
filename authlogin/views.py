from django.shortcuts import render, redirect 
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('sale_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    else:
        form = AuthenticationForm()
    return render(request, 'authlogin/login.html', {'form': form})

@login_required(login_url='/authlogin/login/')
def user_logout(request):
    logout(request)
    return redirect('login')

