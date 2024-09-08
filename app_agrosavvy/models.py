from django.db import models
from django.contrib.auth.models import AbstractUser
import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.utils import timezone


class RoleUser(models.Model):
    ROLEUSER_CHOICES = [
        ("da_admin", "da_admin"),
        ("brgy_officer", "brgy_officer"),
        ("farmer", "farmer")
    ]
    roleuser = models.CharField(max_length=50, choices=ROLEUSER_CHOICES)

    def __str__(self):
        return self.roleuser
    


# class UserAddress(models.Model):
#     address_id = models.AutoField(primary_key=True)
#     barangay = models.CharField(max_length=100)
#     city_municipality = models.CharField(max_length=100)
#     country = models.CharField(max_length=100)

#     def __str__(self):
#         return f"{self.barangay}, {self.city_municipality}, {self.country}"


class Gender(models.Model):
    GENDER_CHOICES=[
        ("Male", "Male"),
        ("Female","Female"),
        ("Other", "Other"),
    ]
    gender = models.CharField(max_length=7, choices=GENDER_CHOICES)

    def __str__(self):
        return self.gender

# abstract user is a helper class with default fields: username, password1 and password2, status
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    firstname = models.CharField(max_length=30, blank=True)
    lastname = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    gender = models.ForeignKey(Gender, on_delete=models.SET_NULL, blank=True, null=True)
    # useraddress = models.ForeignKey(UserAddress, on_delete=models.CASCADE, null=True, blank=True)  
    roleuser = models.ForeignKey(RoleUser, on_delete=models.SET_NULL, blank=True, null=True)
    active_status = models.BooleanField(default=True) #used custom instead of default is_active
    is_approved = models.BooleanField(default=False)
    request_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_users')
    
    def __str__(self):
        return self.username
    
    class Meta:
        ordering = ['-approved_date']
    

class PendingUser(models.Model):
    username = models.CharField(max_length=150, unique=False)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    firstname = models.CharField(max_length=30, blank=True)
    lastname = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.ForeignKey(Gender, on_delete=models.SET_NULL, blank=True, null=True )
    # useraddress = models.ForeignKey(UserAddress, on_delete=models.CASCADE, null=True, blank=True)  
    roleuser = models.ForeignKey(RoleUser, on_delete=models.SET_NULL, blank=True, null=True)
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



class ReviewRating(models.Model):
    reviewrating_id = models.AutoField(primary_key=True)
    
    RATING_CHOICES = [
        ("1", "Excellent"),
        ("2", "Good"),
        ("3", "Average"),
        ("4", "Bad"),
        ("5", "Worse"),
    ]
    
    rating = models.CharField(max_length=1, choices=RATING_CHOICES)
    review_header = models.CharField(max_length=30, blank=True, null=True)
    review_body = models.CharField(max_length=200, blank=True, null=True)
    rate_date = models.DateTimeField(auto_now_add=True)
    reviewer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    is_deleted = models.BooleanField(default = False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return f"{self.get_rating_display()}: {self.review_header or 'No Header'}"
    

# brgy choices
class Barangay(models.Model):
    BRGY_CHOICES = [
        ("Adlaon", "Adlaon"),
        ("Agsungot", "Agsungot"),
        ("Apas", "Apas"),
        ("Babag", "Babag"),
        ("Bacayan", "Bacayan"),
        ("Banilad", "Banilad"),
        ("Basak Pardo", "Basak Pardo"),
        ("Busay", "Busay"),
        ("Calamba", "Calamba"),
        ("Cambinocot", "Cambinocot"),
        ("Camputhaw", "Camputhaw"),
        ("Capitol Site", "Capitol Site"),
        ("Carreta", "Carreta"),
        ("Central", "Central"),
        ("Cogon Pardo", "Cogon Pardo"),
        ("Cogon Ramos", "Cogon Ramos"),
        ("Day-as", "Day-as"),
        ("Duljo", "Duljo"),
        ("Ermita", "Ermita"),
        ("Guadalupe", "Guadalupe"),
        ("Guba", "Guba"),
        ("Hippodromo", "Hippodromo"),
        ("Inayawan", "Inayawan"),
        ("Kalubihan", "Kalubihan"),
        ("Kalunasan", "Kalunasan"),
        ("Kamagayan", "Kamagayan"),
        ("Kasambagan", "Kasambagan"),
        ("Kinasang-an Pardo", "Kinasang-an Pardo"),
        ("Labangon", "Labangon"),
        ("Lahug", "Lahug"),
        ("Lorega (Lorega San Miguel)", "Lorega (Lorega San Miguel)"),
        ("Lusaran", "Lusaran"),
        ("Luz", "Luz"),
        ("Mabini", "Mabini"),
        ("Mabolo", "Mabolo"),
        ("Malubog", "Malubog"),
        ("Mambaling", "Mambaling"),
        ("Pahina Central", "Pahina Central"),
        ("Pahina San Nicolas", "Pahina San Nicolas"),
        ("Pamutan", "Pamutan"),
        ("Pardo", "Pardo"),
        ("Pari-an", "Pari-an"),
        ("Paril", "Paril"),
        ("Pasil", "Pasil"),
        ("Pit-os", "Pit-os"),
        ("Pulangbato", "Pulangbato"),
        ("Pung-ol-Sibugay", "Pung-ol-Sibugay"),
        ("Punta Princesa", "Punta Princesa"),
        ("Quiot Pardo", "Quiot Pardo"),
        ("Sambag I", "Sambag I"),
        ("Sambag II", "Sambag II"),
        ("San Antonio", "San Antonio"),
        ("San Jose", "San Jose"),
        ("San Nicolas Central", "San Nicolas Central"),
        ("San Roque (Ciudad)", "San Roque (Ciudad)"),
        ("Santa Cruz", "Santa Cruz"),
        ("Sapangdaku", "Sapangdaku"),
        ("Sawang Calero", "Sawang Calero"),
        ("Sinsin", "Sinsin"),
        ("Sirao", "Sirao"),
        ("Suba Poblacion (Suba San Nicolas)", "Suba Poblacion (Suba San Nicolas)"),
        ("Sudlon I", "Sudlon I"),
        ("Sudlon II", "Sudlon II"),
        ("Tabunan", "Tabunan"),
        ("Tagbao", "Tagbao"),
        ("Talamban", "Talamban"),
        ("Taptap", "Taptap"),
        ("Tejero (Villa Gonzalo)", "Tejero (Villa Gonzalo)"),
        ("Tinago", "Tinago"),
        ("Tisa", "Tisa"),
        ("To-ong Pardo", "To-ong Pardo"),
        ("T. Padilla", "T. Padilla"),
        ("Zapatera", "Zapatera")
    ]
    brgy_id = models.AutoField(primary_key=True)
    brgy_name = models.CharField(max_length=50, choices=BRGY_CHOICES)

    def __str__(self):
        return f"{self.brgy_name}"
    
    class Meta:
        ordering = ['brgy_name']
    

# used in field address
class Address(models.Model):
    address_id = models.AutoField(primary_key=True)
    barangay = models.ForeignKey(Barangay, on_delete=models.SET_NULL, blank=True, null=True)
    city_municipality = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f"{self.barangay}, {self.city_municipality}, {self.country}"



class Field(models.Model):
    field_id = models.AutoField(primary_key=True)
    field_name = models.CharField(max_length=100)
    field_acres = models.FloatField()
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, related_name="fields", null=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="fields", null=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default = False)


    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return self.field_name

    class Meta:
        ordering = ['-created_at']


# crop choices
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
        return f"{self.crop_type}"
    



# tracks field data (soil and crop data of a field) movement overtime
class FieldCropData(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    fieldcrop_id = models.AutoField(primary_key=True)
    crop_planted = models.ForeignKey(Crop, on_delete=models.CASCADE)
    planting_date = models.DateField()
    harvest_date = models.DateField()
    # new
    is_deleted = models.BooleanField(default = False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return f"{self.crop_planted} planted in {self.field.field_name} on {self.planting_date}"
    
    class Meta:
        ordering = ['-planting_date']


class FieldSoilData(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    soil_id = models.AutoField(primary_key=True)
    nitrogen = models.FloatField(null=True, blank=True)
    phosphorous = models.FloatField(null=True, blank=True)
    potassium = models.FloatField(null=True, blank=True)
    ph = models.FloatField(null=True, blank=True)
    record_date = models.DateField()
    # new
    is_deleted = models.BooleanField(default = False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return f"Soil data for {self.field.field_name} recorded at {self.record_date}"
    
    class Meta:
        ordering = ['-record_date']
    

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
