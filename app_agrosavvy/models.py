from django.db import models

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

    def __str__(self):
        return self.field_name
