from django.contrib import admin
from .models import Appointment
from .models import Product

# Register your models here.


@admin.register(Appointment)
class appointmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'submitted_at')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('submitted_at',)



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price')
    search_fields = ('name', 'category')
