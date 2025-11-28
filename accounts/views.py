from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseForbidden
from django.db.models import Q

# Register
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Validation
        if not username or not email or not phone:
            messages.error(request, "All fields are required.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(Q(username=username) | Q(email=email)).exists():
            messages.error(request, "Username or email already taken.")
        else:
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                user.save()
                messages.success(request, "Account created successfully!")
                return redirect('accounts:login')  # ✅ correct namespace
            except Exception as e:
                messages.error(request, f"Error creating account: {e}")
    
    return render(request, 'accounts/signup.html')


# Login
def login_view(request):
    if request.method == "POST":
        identifier = request.POST.get('email', '').strip()  # can be username or email
        password = request.POST.get('password', '')

        user = None
        # Check if identifier is email
        if User.objects.filter(email=identifier).exists():
            email_user = User.objects.get(email=identifier)
            user = authenticate(request, username=email_user.username, password=password)
        else:
            # Assume it's a username
            user = authenticate(request, username=identifier, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("myapp:index")
        else:
            messages.error(request, "Invalid login credentials.")

    return render(request, 'accounts/login.html')


# Logout
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('accounts:login')
    else:
        return HttpResponseForbidden("Forbidden: This URL only accepts POST requests.")
