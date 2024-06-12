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