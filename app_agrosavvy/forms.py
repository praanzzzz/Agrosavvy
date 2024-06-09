from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Field, CustomUser

class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ['field_name', 'barangay', 'city_municipality', 'country', 'latitude', 'longitude', 'nitrogen', 'phosphorous', 'potassium', 'ph', 'crop', 'field_acres']




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
    email = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control"
            }
        )
    )
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
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'is_da_admin', 'is_barangay_officer', 'is_farmer','firstname','lastname')