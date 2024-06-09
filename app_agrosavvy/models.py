from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    user_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    firstname = models.CharField(max_length=30, blank=True)
    lastname = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_farmer = models.BooleanField(default=False)
    is_barangay_officer = models.BooleanField(default=False)
    is_da_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username



class Crop(models.Model):
    CROP_CHOICES = [
        ('Carrots', 'Carrots'),
        ('Potato', 'Potato'),
        ('Garlic', 'Garlic'),
        ('Eggplant', 'Eggplant'),
        ('Tomato', 'Tomato'),
        ('Squash', 'Squash'),
        ('Bitter Gourd', 'Bitter Gourd'),
        ('Cabbage', 'Cabbage'),
        ('Onion', 'Onion'),
    ]
    crop_id = models.AutoField(primary_key=True)
    crop_type = models.CharField(max_length=50, choices=CROP_CHOICES)

    def __str__(self):
        return self.crop_type


class Field(models.Model):
    field_id = models.AutoField(primary_key=True)
    field_name = models.CharField(max_length=100)
    field_acres = models. FloatField()
    # address
    barangay = models.CharField(max_length=100)
    city_municipality = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    #soil data  
    nitrogen = models.FloatField(null=True)
    phosphorous = models.FloatField(null=True)
    potassium = models.FloatField(null=True)
    ph = models.FloatField(null=True)
    # fk -crop
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, null=True, blank=True)
    # foreign key - user (owner of the field)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='fields')

    def __str__(self):
        return self.field_name
