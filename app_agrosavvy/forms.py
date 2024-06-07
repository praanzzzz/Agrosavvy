from django import forms
from .models import Field

class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ['field_name', 'barangay', 'city_municipality', 'country', 'latitude', 'longitude', 'nitrogen', 'phosphorous', 'potassium', 'ph', 'crop', 'field_acres']
