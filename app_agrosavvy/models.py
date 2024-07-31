from django.db import models
from django.contrib.auth.models import AbstractUser
import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.utils import timezone

# abstract user is a helper class with default fields: username, password1 and password2, status
class CustomUser(AbstractUser):
    user_id = models.CharField(max_length=50, unique=True, blank=True, null=True) # no values since it is not autofill
    email = models.EmailField(unique=True)
    firstname = models.CharField(max_length=30, blank=True)
    lastname = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    # user role
    is_farmer = models.BooleanField(default=False)
    is_barangay_officer = models.BooleanField(default=False)
    is_da_admin = models.BooleanField(default=False)
    # registration and account status info
    active_status = models.BooleanField(default=True) #used custom instead of default is_active
    is_approved = models.BooleanField(default=False)
    request_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_users')

    def __str__(self):
        return self.username
    

class PendingUser(models.Model):
    username = models.CharField(max_length=150, unique=False)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    firstname = models.CharField(max_length=30, blank=True)
    lastname = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_farmer = models.BooleanField(default=False)
    is_barangay_officer = models.BooleanField(default=False)
    is_da_admin = models.BooleanField(default=False)
    request_date = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'firstname', 'lastname']

    # hashing password
    def save(self, *args, **kwargs):
        if not self.pk and self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.username


# # To Migrate
# class Review_Rating(models.Model):
#     reviewrating_id= models.AutoField(primary_key=True)
#     rating= [
#         ("1", "1"),
#         ("2", "2"),
#         ("3", "3"),
#         ("4", "4"),
#         ("5", "5"),
#     ]
#     review=models.TextField(max_length=200, blank=True, null=True)
#     rate_date = models.DateTimeField(auto_now_add=True)
#     reviewer= models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    

class Crop(models.Model):
    CROP_CHOICES = [
        ("Carrots", "Carrots"),
        ("Potato", "Potato"),
        ("Garlic", "Garlic"),
        ("Eggplant", "Eggplant"),
        ("Tomato", "Tomato"),
        ("Squash", "Squash"),
        ("Bitter Gourd", "Bitter Gourd"),
        ("Cabbage", "Cabbage"),
        ("Onion", "Onion"),
    ]
    crop_id = models.AutoField(primary_key=True)
    crop_type = models.CharField(max_length=50, choices=CROP_CHOICES)

    def __str__(self):
        return self.crop_type


class Address(models.Model):
    address_id = models.AutoField(primary_key=True)
    barangay = models.CharField(max_length=100)
    city_municipality = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f"{self.barangay}, {self.city_municipality}, {self.country}"


class SoilData(models.Model):
    soil_id = models.AutoField(primary_key=True)
    nitrogen = models.FloatField(null=True, blank=True)
    phosphorous = models.FloatField(null=True, blank=True)
    potassium = models.FloatField(null=True, blank=True)
    ph = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"N: {self.nitrogen}, P: {self.phosphorous}, K: {self.potassium}, pH: {self.ph}"


class Field(models.Model):
    field_id = models.AutoField(primary_key=True)
    field_name = models.CharField(max_length=100)
    field_acres = models.FloatField()
    address = models.ForeignKey(
        Address, on_delete=models.SET_NULL, related_name="fields", null=True
    )
    soil_data = models.ForeignKey(
        SoilData,
        on_delete=models.SET_NULL,
        related_name="fields",
        blank=True,
        null=True,
    )
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, blank=True, null=True)
    owner = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, related_name="fields", null=True
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.field_name

    class Meta:
        ordering = ['-created_at']



# this function just gets data from openweathermap, it does not really interact with the database so no need for migrations for now
def get_weather_data(location):
    api_key = settings.WEATHER_API_KEY
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": location, "appid": api_key, "units": "metric"}  # metric or imperial

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception for error codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting weather data: {e}")
        return None
