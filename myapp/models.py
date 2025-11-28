from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
import os


class Appointment(models.Model):
    phone_validator = RegexValidator(
        r'^\d{10}$',
        'Phone number must be 10 digits.'
    )

    # ✅ Allow null/blank for existing records
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='appointments',
        null=True,      # existing rows can stay without user
        blank=True      # allow forms to leave it empty if needed
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=10, validators=[phone_validator])
    date = models.DateField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"

import os
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Product(models.Model):
    farmer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='products',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    contact = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Phone number or email for buyers to reach you"
    )
    image = models.ImageField(upload_to='products/')
    date_posted = models.DateTimeField(default=timezone.now)
    paid = models.BooleanField(default=False)



    def __str__(self):
        return self.name

    # ✅ Automatically delete image file when Product is deleted
    def delete(self, *args, **kwargs):
        if self.image and os.path.isfile(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)

