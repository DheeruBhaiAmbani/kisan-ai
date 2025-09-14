from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='farmer')
    pin_code = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)

    # Add any other fields common to both user types
    # For email verification, make email=True in AbstractUser and handle verification logic in views

    def __str__(self):
        return self.username

class FarmerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, limit_choices_to={'user_type': 'farmer'})
    farm_size_acres = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    primary_crops = models.CharField(max_length=255, blank=True) # Comma-separated list

    def __str__(self):
        return f"{self.user.username}'s Farmer Profile"

class BuyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, limit_choices_to={'user_type': 'buyer'})
    business_name = models.CharField(max_length=255, blank=True)
    business_type = models.CharField(max_length=100, blank=True) # e.g., 'Wholesaler', 'Retailer', 'Restaurant'

    def __str__(self):
        return f"{self.user.username}'s Buyer Profile"