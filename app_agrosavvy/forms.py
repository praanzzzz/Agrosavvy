from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Field, Address, SoilData, CustomUser
from django.core.exceptions import ValidationError



class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ['field_name', 'field_acres', 'crop']
        widgets = {
            'field_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter field name'}),
            'field_acres': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter field size in acres'}),
            'crop': forms.Select(attrs={'class': 'form-control'}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['barangay', 'city_municipality', 'country', 'latitude', 'longitude']
        widgets = {
            'barangay': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter barangay'}),
            'city_municipality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city or municipality'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter country'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def clean_city_municipality(self):
        city = self.cleaned_data.get('city_municipality')
        if city.strip().lower() != 'cebu city':
            raise ValidationError('The address must be in Cebu City.')
        return city


class SoilDataForm(forms.ModelForm):
    class Meta:
        model = SoilData
        fields = ['nitrogen', 'phosphorous', 'potassium', 'ph']
        widgets = {
            'nitrogen': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter nitrogen level'}),
            'phosphorous': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter phosphorous level'}),
            'potassium': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter potassium level'}),
            'ph': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter pH level'}),
        }

class LoginForm(forms.Form):
    username = forms.CharField(
        widget= forms.TextInput(
            attrs={
                "class": "form-control"
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control"
            }
        )
    )

#we can call username, p1 and p2 since we use usercrreationform which has default fields for these fields.
class SignUpForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control"
            }
        )
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control"
            }
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control"
            }
        )
    )

    #fields from models
    firstname = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control"
            }
        )
    )
    lastname = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control"
            }
        )
    )
    email = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control"
            }
        )
    )
    
    #connecting default and custom fields from usercreationforms to abstractuser default and custom fields
    class Meta:
        model = CustomUser
        fields = ('username', 'password1', 'password2', 'email', 'firstname','lastname')