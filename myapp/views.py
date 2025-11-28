import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from requests.auth import HTTPBasicAuth
from .models import Product
from myapp.credentials import LipanaMpesaPpassword, MpesaAccessToken
from .forms import AppointmentForm
from .models import Appointment


# ========== BASIC PAGES ==========

def index(request):
    return render(request, "index.html")

def about(request):
    return render(request, "about.html")

def service(request):
    return render(request, "service.html")

def testimonial(request):
    return render(request, "testimonial.html")

def blog(request):
    return render(request, "blog.html")

def team(request):
    return render(request, "mine.html")

@login_required
def marketplace(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category')
        price = request.POST.get('price')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        contact = request.POST.get('contact')

        # Create the product
        product = Product.objects.create(
            farmer=request.user,
            name=name,
            category=category,
            price=price,
            description=description,
            image=image,
            contact=contact
        )

        # Save product ID in session
        request.session['pending_product_id'] = product.id

        # ✅ Redirect to the pay page (no arguments)
        return redirect('myapp:pay')

    return render(request, 'marketplace.html')




def products_list(request):
    products = Product.objects.all()
    return render(request, 'products_list.html', {'products': products})

@login_required
def my_products(request):
    products = Product.objects.filter(farmer=request.user)
    return render(request, 'my_products.html', {'products': products})

@login_required(login_url='accounts:login')
def appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user  # link appointment to the logged-in user
            appointment.save()
            messages.success(request, "Your appointment has been submitted successfully!")
            return redirect('myapp:show_appointments')
        else:
            messages.error(request, "There was an error submitting your appointment. Please try again.")
    else:
        form = AppointmentForm()

    return render(request, 'appointment.html', {'form': form})


@login_required(login_url='accounts:login')
def retrieve_appointments(request):
    """Admins see all appointments, users see only their own"""
    if request.user.is_staff or request.user.is_superuser:
        appointments = Appointment.objects.all().order_by('-submitted_at')
    else:
        appointments = Appointment.objects.filter(user=request.user).order_by('-submitted_at')

    context = {'appointments': appointments}
    return render(request, 'show_appointments.html', context)


@login_required(login_url='accounts:login')
def delete_appointment(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    if request.user == appointment.user or request.user.is_staff:
        appointment.delete()
        messages.success(request, "Appointment deleted successfully.")
    else:
        messages.error(request, "You are not authorized to delete this appointment.")
    return redirect("myapp:show_appointments")


@login_required(login_url='accounts:login')
def update_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.user != appointment.user and not request.user.is_staff:
        messages.error(request, "You are not authorized to edit this appointment.")
        return redirect("myapp:show_appointments")

    if request.method == 'POST':
        appointment.name = request.POST.get('name')
        appointment.date = request.POST.get('date')
        appointment.email = request.POST.get('email')
        appointment.message = request.POST.get('message')
        appointment.save()
        messages.success(request, "Appointment updated successfully.")
        return redirect("myapp:show_appointments")

    return render(request, "update_appointment.html", {'appointment': appointment})


# ========== M-PESA PAYMENT ==========

@login_required
def pay(request):
    """Renders the form to initiate a payment"""
    return render(request, 'pay.html')


def token(request):
    """Generates M-Pesa API access token"""
    consumer_key = 'A0lFhp6Kw10Ugb8mrjnv2jI59wFNslVV3dra99YHn3BFUb75'
    consumer_secret = 'qKJfOMvZz6CiogCbYo2ofWFfMsIIekt9ebmPoqH7TO3y4fX0EUXg7o0X8v0F7FNq'
    api_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    mpesa_access_token = json.loads(r.text)
    validated_mpesa_access_token = mpesa_access_token["access_token"]

    return render(request, 'token.html', {"token": validated_mpesa_access_token})


def stk(request):
    """Sends STK push to user's phone"""
    if request.method == "POST":
        phone = request.POST['phone']
        amount = request.POST['amount']
        access_token = MpesaAccessToken.validated_mpesa_access_token
        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        headers = {"Authorization": f"Bearer {access_token}"}

        payload = {
            "BusinessShortCode": LipanaMpesaPpassword.Business_short_code,
            "Password": LipanaMpesaPpassword.decode_password,
            "Timestamp": LipanaMpesaPpassword.lipa_time,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": LipanaMpesaPpassword.Business_short_code,
            "PhoneNumber": phone,
            "CallBackURL": "https://sandbox.safaricom.co.ke/mpesa/",
            "AccountReference": "eMobilis",
            "TransactionDesc": "Appointment Payment"
        }

        response = requests.post(api_url, json=payload, headers=headers)
        return HttpResponse("Payment request sent successfully!")


@login_required
def delete_product(request, id):
    product = get_object_or_404(Product, id=id, farmer=request.user)
    if request.method == 'POST':
        product.delete()
    return redirect('myapp:my_products')


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # only if you’re testing without CSRF setup — remove once CSRF works
def consult_ai(request):
    if request.method == "POST":
        question = request.POST.get("question", "").strip()
        image = request.FILES.get("image")

        # Validate input
        if not question and not image:
            return JsonResponse({"answer": "Please type a question or upload an image."})

        # 🧠 Text question handling
        if question and not image:
            ai_reply = f"🤖 You asked: '{question}'. I’ll analyze this and provide a response soon!"
        
        # 🖼️ Image upload handling
        elif image and not question:
            ai_reply = f"🖼️ Received your image **{image.name}**. Currently, I can only process text questions, but image analysis is coming soon!"

        # 🧠 Text + Image together
        else:
            ai_reply = f"📸 You asked '{question}' and uploaded {image.name}. I'll process both shortly!"

        return JsonResponse({"answer": ai_reply})

    return JsonResponse({"error": "Invalid request method."}, status=400)
