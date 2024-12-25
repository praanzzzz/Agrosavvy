from django.db import models
from django.contrib.auth.models import AbstractUser
import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import now




class RoleUser(models.Model):
    ROLEUSER_CHOICES = [
        ("super_admin", "super_admin"),
        ("da_admin", "da_admin"),
        ("brgy_officer", "brgy_officer"),
        ("farmer", "farmer")
    ]
    roleuser = models.CharField(max_length=20, choices=ROLEUSER_CHOICES)

    def __str__(self):
        return self.roleuser
    


class Gender(models.Model):
    GENDER_CHOICES=[
        ("Male", "Male"),
        ("Female","Female"),
    ]
    gender = models.CharField(max_length=7, choices=GENDER_CHOICES)

    def __str__(self):
        return self.gender
    

# 28 brgy choices
class Barangay(models.Model):
    BRGY_CHOICES = [
        ("Adlaon", "Adlaon"),
        ("Agsungot", "Agsungot"),
        ("Babag", "Babag"),
        ("Binaliw", "Binaliw"),
        ("Bonbon", "Bonbon"),
        ("Budlaan", "Budlaan"),
        ("Buhisan", "Buhisan"),
        ("Buot-Taup", "Buot-Taup"),
        ("Busay", "Busay"),
        ("Cambinocot", "Cambinocot"),
        ("Guba", "Guba"),
        ("Kalunasan", "Kalunasan"),
        ("Lusaran", "Lusaran"),
        ("Mabini", "Mabini"),
        ("Malubog", "Malubog"),
        ("Pamutan", "Pamutan"),
        ("Paril", "Paril"),
        ("Pung-ol Sibugay", "Pung-ol Sibugay"),
        ("Pulangbato", "Pulangbato"),
        ("Sapangdaku", "Sapangdaku"),
        ("Sinsin", "Sinsin"),
        ("Sirao", "Sirao"),
        ("Sudlon 1", "Sudlon 1"),
        ("Sudlon 2", "Sudlon 2"),
        ("Tabunan", "Tabunan"),
        ("Tagbao", "Tagbao"),
        ("Taptap", "Taptap"),
        ("Toong", "Toong"),
    ]
    brgy_id = models.AutoField(primary_key=True)
    brgy_name = models.CharField(max_length=50, choices=BRGY_CHOICES)

    def __str__(self):
        return f"{self.brgy_name}"
    
    class Meta:
        ordering = ['brgy_name']


    

class Address(models.Model):
    address_id = models.AutoField(primary_key=True)
    barangay = models.ForeignKey(Barangay, on_delete=models.SET_NULL, blank=True, null=True)
    city_municipality = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.FloatField(blank=True, null=True) 
    longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.barangay}, {self.city_municipality}, {self.country}"





class UserAddress(models.Model):
    USERADDRESS_CHOICES = [
        ("Adlaon, Cebu City", "Adlaon, Cebu City"),
        ("Agsungot, Cebu City", "Agsungot, Cebu City"),
        ("Apas, Cebu City", "Apas, Cebu City"),
        ("Babag, Cebu City", "Babag, Cebu City"),
        ("Bacayan, Cebu City", "Bacayan, Cebu City"),
        ("Banilad, Cebu City", "Banilad, Cebu City"),
        ("Basak Pardo, Cebu City", "Basak Pardo, Cebu City"),
        ("Binaliw, Cebu City", "Binaliw, Cebu City"),  
        ("Bonbon, Cebu City", "Bonbon, Cebu City"),    
        ("Budlaan, Cebu City", "Budlaan, Cebu City"),  
        ("Buhisan, Cebu City", "Buhisan, Cebu City"),  
        ("Buot-Taup, Cebu City", "Buot-Taup, Cebu City"), 
        ("Busay, Cebu City", "Busay, Cebu City"),
        ("Calamba, Cebu City", "Calamba, Cebu City"),
        ("Cambinocot, Cebu City", "Cambinocot, Cebu City"),
        ("Camputhaw, Cebu City", "Camputhaw, Cebu City"),
        ("Capitol Site, Cebu City", "Capitol Site, Cebu City"),
        ("Carreta, Cebu City", "Carreta, Cebu City"),
        ("Central, Cebu City", "Central, Cebu City"),
        ("Cogon Pardo, Cebu City", "Cogon Pardo, Cebu City"),
        ("Cogon Ramos, Cebu City", "Cogon Ramos, Cebu City"),
        ("Day-as, Cebu City", "Day-as, Cebu City"),
        ("Duljo, Cebu City", "Duljo, Cebu City"),
        ("Ermita, Cebu City", "Ermita, Cebu City"),
        ("Guadalupe, Cebu City", "Guadalupe, Cebu City"),
        ("Guba, Cebu City", "Guba, Cebu City"),
        ("Hippodromo, Cebu City", "Hippodromo, Cebu City"),
        ("Inayawan, Cebu City", "Inayawan, Cebu City"),
        ("Kalubihan, Cebu City", "Kalubihan, Cebu City"),
        ("Kalunasan, Cebu City", "Kalunasan, Cebu City"),
        ("Kamagayan, Cebu City", "Kamagayan, Cebu City"),
        ("Kasambagan, Cebu City", "Kasambagan, Cebu City"),
        ("Kinasang-an Pardo, Cebu City", "Kinasang-an Pardo, Cebu City"),
        ("Labangon, Cebu City", "Labangon, Cebu City"),
        ("Lahug, Cebu City", "Lahug, Cebu City"),
        ("Lorega (Lorega San Miguel), Cebu City", "Lorega (Lorega San Miguel), Cebu City"),
        ("Lusaran, Cebu City", "Lusaran, Cebu City"),
        ("Luz, Cebu City", "Luz, Cebu City"),
        ("Mabini, Cebu City", "Mabini, Cebu City"),
        ("Mabolo, Cebu City", "Mabolo, Cebu City"),
        ("Malubog, Cebu City", "Malubog, Cebu City"),
        ("Mambaling, Cebu City", "Mambaling, Cebu City"),
        ("Pahina Central, Cebu City", "Pahina Central, Cebu City"),
        ("Pahina San Nicolas, Cebu City", "Pahina San Nicolas, Cebu City"),
        ("Pamutan, Cebu City", "Pamutan, Cebu City"),
        ("Pardo, Cebu City", "Pardo, Cebu City"),
        ("Pari-an, Cebu City", "Pari-an, Cebu City"),
        ("Paril, Cebu City", "Paril, Cebu City"),
        ("Pasil, Cebu City", "Pasil, Cebu City"),
        ("Pit-os, Cebu City", "Pit-os, Cebu City"),
        ("Pulangbato, Cebu City", "Pulangbato, Cebu City"),
        ("Pung-ol-Sibugay, Cebu City", "Pung-ol-Sibugay, Cebu City"),
        ("Punta Princesa, Cebu City", "Punta Princesa, Cebu City"),
        ("Quiot Pardo, Cebu City", "Quiot Pardo, Cebu City"),
        ("Sambag I, Cebu City", "Sambag I, Cebu City"),
        ("Sambag II, Cebu City", "Sambag II, Cebu City"),
        ("San Antonio, Cebu City", "San Antonio, Cebu City"),
        ("San Jose, Cebu City", "San Jose, Cebu City"),
        ("San Nicolas Central, Cebu City", "San Nicolas Central, Cebu City"),
        ("San Roque (Ciudad), Cebu City", "San Roque (Ciudad), Cebu City"),
        ("Santa Cruz, Cebu City", "Santa Cruz, Cebu City"),
        ("Sapangdaku, Cebu City", "Sapangdaku, Cebu City"),
        ("Sawang Calero, Cebu City", "Sawang Calero, Cebu City"),
        ("Sinsin, Cebu City", "Sinsin, Cebu City"),
        ("Sirao, Cebu City", "Sirao, Cebu City"),
        ("Suba Poblacion (Suba San Nicolas), Cebu City", "Suba Poblacion (Suba San Nicolas), Cebu City"),
        ("Sudlon 1, Cebu City", "Sudlon 1, Cebu City"),  
        ("Sudlon 2, Cebu City", "Sudlon 2, Cebu City"),  
        ("Tabunan, Cebu City", "Tabunan, Cebu City"),
        ("Tagbao, Cebu City", "Tagbao, Cebu City"),
        ("Talamban, Cebu City", "Talamban, Cebu City"),
        ("Taptap, Cebu City", "Taptap, Cebu City"),
        ("Tejero (Villa Gonzalo), Cebu City", "Tejero (Villa Gonzalo), Cebu City"),
        ("Tinago, Cebu City", "Tinago, Cebu City"),
        ("Tisa, Cebu City", "Tisa, Cebu City"),
        ("Toong, Cebu City", "Toong, Cebu City"),  
        ("T. Padilla, Cebu City", "T. Padilla, Cebu City"),
        ("Zapatera, Cebu City", "Zapatera, Cebu City")
    ]
    useraddress_id = models.AutoField(primary_key=True)
    useraddress= models.CharField(max_length=100, choices=USERADDRESS_CHOICES)

    def __str__(self):
        return f"{self.useraddress}"
    
    class Meta:
        ordering = ['useraddress']






# abstract user is a helper class with default fields: username, password1 and password2, status
# ang password ra ang nagamit sa default.
class CustomUser(AbstractUser):
    first_name = None
    last_name = None
    official_user_id = models.CharField(max_length= 30, unique=True)
    email = models.EmailField(unique=True)
    firstname = models.CharField(max_length=30)
    middle_initial = models.CharField(max_length=1, null=True, blank=True)
    lastname = models.CharField(max_length=30)
    date_of_birth = models.DateField(null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    gender = models.ForeignKey(Gender, on_delete=models.SET_NULL, null= True)
    contact_number = models.CharField(max_length=13)
    useraddress = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True)  
    roleuser = models.ForeignKey(RoleUser, on_delete=models.SET_NULL, null= True)
    active_status = models.BooleanField(default=True) 
    is_approved = models.BooleanField(default=False)
    request_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_users')
    is_subscribed = models.BooleanField(default=True)


    def save(self, *args, **kwargs):
        self.username = self.username.strip()
        self.email = self.email.strip()
        self.firstname = self.firstname.strip()
        self.lastname =self.lastname.strip()
        super().save(*args, **kwargs)


    # Define your custom get_full_name method
    def get_full_name(self):
        return f"{self.firstname} {self.lastname}".strip()
    
    def __str__(self):
        return self.username
    
    class Meta:
        ordering = ['-approved_date']
    



class PendingUser(models.Model):
    official_user_id = models.CharField(max_length= 30, unique=True)
    username = models.CharField(max_length=10, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(max_length = 50, unique=True) 
    firstname = models.CharField(max_length=30)
    middle_initial = models.CharField(max_length=1, null=True, blank= True)
    lastname = models.CharField(max_length=30)
    date_of_birth = models.DateField(null=True)
    gender = models.ForeignKey(Gender, on_delete=models.SET_NULL, null= True)
    contact_number = models.CharField(max_length=13)
    useraddress = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null= True)
    roleuser = models.ForeignKey(RoleUser, on_delete=models.SET_NULL, null= True)
    request_date = models.DateTimeField(auto_now_add=True)
    is_disapproved = models.BooleanField(default=False)
    is_pending = models.BooleanField(default=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'firstname', 'lastname']

    # hashing password
    def save(self, *args, **kwargs):
        if not self.pk and self.password:
            self.password = make_password(self.password)


        self.official_user_id = self.official_user_id.strip()
        self.username = self.username.strip()
        self.email = self.email.strip()
        self.firstname = self.firstname.strip()
        self.lastname =self.lastname.strip()
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
    review_header = models.CharField(max_length=30)
    review_body = models.CharField(max_length=100)
    rate_date = models.DateTimeField(auto_now_add=True)
    reviewer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    is_deleted = models.BooleanField(default = False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return f"{self.get_rating_display()}: {self.review_header or 'No Header'}"
    



class Field(models.Model):
    field_id = models.AutoField(primary_key=True)
    field_name = models.CharField(max_length=20)
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



class Crop(models.Model):
    CROP_CHOICES = [
        ("Carrots", "Carrots"),
        ("Potato", "Potato"),
        ("Pechay", "Pechay"),
        ("Eggplant", "Eggplant"),
        ("Rice", "Rice"),
        ("Tomato", "Tomato"),
        ("Squash", "Squash"),
        ("Ampalaya", "Ampalaya"),
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
    is_deleted = models.BooleanField(default = False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return f"Crop Data {self.crop_planted} planted in {self.field.field_name} on {self.planting_date}"
    
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
    is_deleted = models.BooleanField(default = False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return f"Soil data for {self.field.field_name} recorded at {self.record_date}"
    
    class Meta:
        ordering = ['-record_date']



class Notification(models.Model):
    user_receiver = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='received_notifications')
    user_sender = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='sent_notifications')
    subject = models.TextField(max_length=30)
    message = models.TextField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default = False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return f"Notification to {self.user_receiver} - {self.subject[:20]}"


class ChatGroup(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default = False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return f'{self.id}. {self.user.username}'
    
    class Meta:
        ordering = ['-created_at']


class Chat(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    chat_group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='chats') 
    intent = models.CharField(max_length=50, null=True, blank=True)
    message = models.TextField(max_length=250)
    response = models.TextField()
    ai_context = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.message}'
    


class ImageAnalysis(models.Model):
    analysis_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="imageanalysis", null=True)
    image = models.ImageField(upload_to='image_analysis_pictures/', null=True, blank=True)
    analysis_output = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default = False)
    

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return self.analysis_output[:50]




class SoilDataSFM(models.Model):
    NITROGEN_LEVELS = [
        ('L', 'Low (0 - 2)'),
        ('ML', 'Moderately Low (2.1 - 3.5)'),
        ('MH', 'Moderately High (3.6 - 4.5)'),
        ('H', 'High (4.6 - 5.5)'),
        ('VH', 'Very High (5.5+)'),
    ]
    
    PHOSPHORUS_LEVELS = [
        ('L', 'Low (0-6)'),
        ('ML', 'Moderately Low (6.1-10)'),
        ('MH', 'Moderately High (10.1-15)'),
        ('H', 'High (15.1-20)'),
        ('VH', 'Very High (20+)'),
    ]

    POTASSIUM_LEVELS = [
        ('L', 'Low (0-75)'),
        ('ML', 'Sufficient(76-113)'),
        ('MH', 'Sufficient+ (114-150)'),
        ('H', 'Sufficient++ (151-200)'),
        ('VH', 'Sufficient+++ (200+)'),
    ]

    PH_LEVELS = [
        ('L', 'Extremely Acid (below 4.4)'),
        ('ML', 'Strongly Acid (4.5-5.5)'),
        ('MH', 'Moderately to Slightly Acid (5.6 - 6.6)'),
        ('H', 'Near Neutral to Slightly Alkaline (6.7 - 7.8)'),
        ('VH', 'Moderately, Strongly to Extremely Alkaline (7.8+)'),
    ]


    barangay = models.CharField(max_length=50)
    sitio = models.CharField(max_length=50)
    ph_level = models.CharField(max_length=2, choices=PH_LEVELS)
    nitrogen_level = models.CharField(max_length=2, choices=NITROGEN_LEVELS)
    phosphorus_level = models.CharField(max_length=2, choices=PHOSPHORUS_LEVELS)
    potassium_level = models.CharField(max_length=2, choices=POTASSIUM_LEVELS)
    crops_planted = models.TextField()  
    total_area = models.FloatField()

    def __str__(self):
        return f"Soil Data for {self.sitio} , {self.barangay}"

    class Meta:
        ordering = ['barangay']



        

# used in AI
def get_weather_data(location):
    api_key = settings.ONECALL_API_KEY
    
    # First, get latitude and longitude from the city name (using the Geocoding API)
    geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
    geocode_params = {"q": location, "appid": api_key, "limit": 1}
    
    try:
        geocode_response = requests.get(geocode_url, params=geocode_params)
        geocode_response.raise_for_status()  # Check if the request was successful
        location_data = geocode_response.json()

        if location_data:
            lat = location_data[0]['lat']
            lon = location_data[0]['lon']
            
            # Now, get the weather data for the lat/lon
            weather_url = "https://api.openweathermap.org/data/3.0/onecall"  # Update to version 3.0
            weather_params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric",  # Use metric units
                "exclude": "minutely,hourly"  
            }
            
            weather_response = requests.get(weather_url, params=weather_params)
            weather_response.raise_for_status()  # Check if the request was successful
            return weather_response.json()

        else:
            print(f"Location not found: {location}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error getting weather data: {e}")
        return None










def get_weather_data_with_minutely_hourly(location):
    api_key = settings.ONECALL_API_KEY
    
    # First, get latitude and longitude from the city name (using the Geocoding API)
    geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
    geocode_params = {"q": location, "appid": api_key, "limit": 1}
    
    try:
        geocode_response = requests.get(geocode_url, params=geocode_params)
        geocode_response.raise_for_status()  # Check if the request was successful
        location_data = geocode_response.json()

        if location_data:
            lat = location_data[0]['lat']
            lon = location_data[0]['lon']
            
            # Now, get the weather data for the lat/lon
            weather_url = "https://api.openweathermap.org/data/3.0/onecall"  # Update to version 3.0
            weather_params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric",  # Use metric units
            }
            
            weather_response = requests.get(weather_url, params=weather_params)
            weather_response.raise_for_status()  # Check if the request was successful
            return weather_response.json()

        else:
            print(f"Location not found: {location}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error getting weather data: {e}")
        return None



# manual banning of IP
class BannedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.ip_address




# automatic blocking of ip or username independently
class FailedLoginAttempt(models.Model):
    ip_address = models.GenericIPAddressField()
    username = models.CharField(max_length=150, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def is_blocked(ip_address=None, username=None):
        now_time = now()
        time_threshold = now_time - timedelta(minutes=30)

        # Check failed attempts for IP address or username independently
        ip_attempts = FailedLoginAttempt.objects.filter(
            ip_address=ip_address,
            timestamp__gte=time_threshold
        ).count()

        user_attempts = FailedLoginAttempt.objects.filter(
            username=username,
            timestamp__gte=time_threshold
        ).count()

        # Block if either IP or username exceeds threshold
        return ip_attempts >= 5 or user_attempts >= 5