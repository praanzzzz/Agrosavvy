from django import forms
from .models import Field, Address, SoilData, CustomUser, PendingUser
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator

# from django.contrib.auth.forms import UserCreationForm

# in progress (goose ai)
class AskrecoForm(forms.Form):
    barangay = forms.CharField(label='Barangay', max_length=100)
    city_municipality = forms.CharField(label='City/Municipality', max_length=100)
    country = forms.CharField(label='Country', max_length=100)
    nitrogen = forms.IntegerField(label='Nitrogen') 
    phosphorous = forms.IntegerField(label='Phosphorous') 
    potassium = forms.IntegerField(label='Potassium') 
    ph = forms.IntegerField(label='pH')  
    # latitude = forms.FloatField(label='Latitude')
    # longitude = forms.FloatField(label='Longitude')



class LoginForm(forms.Form):
    username = forms.CharField(
        label="",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
    )


# # we can call username, p1 and p2 since we use usercrreationform which has default fields for these fields.
# class SignUpForm(UserCreationForm):
#     username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control",}))
#     password1 = forms.CharField(
#         widget=forms.PasswordInput(attrs={"class": "form-control"})
#     )
#     password2 = forms.CharField(
#         widget=forms.PasswordInput(attrs={"class": "form-control"})
#     )

#     # fields from models
#     firstname = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control","autofocus": True}))
#     lastname = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
#     email = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))

#     # connecting default and custom fields from usercreationforms to abstractuser default and custom fields
#     class Meta:
#         model = CustomUser
#         fields = (
#             "username",
#             "password1",
#             "password2",
#             "email",
#             "firstname",
#             "lastname",
#         )



class PendingUserForm(forms.ModelForm):
    username = forms.CharField(
        # label="",
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password_confirmation = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = PendingUser
        fields = [
            "firstname",
            "lastname",
            "username",
            "email",
            "date_of_birth",
            "password",

            
        ]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "firstname": forms.TextInput(attrs={"class": "form-control"}),
            "lastname": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "placeholder": "Select a date",
                    "autocomplete": "off",
                }
            ),
        }


    def clean_username(self):
        username = self.cleaned_data.get("username")
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already used.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already in use")
        return email

    def clean_pending_email(self):
        email = self.cleaned_data.get("email")
        if PendingUser.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "Email is already in use and is waiting for approval"
            )
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(str(e))
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirmation = cleaned_data.get("password_confirmation")

        if password != password_confirmation:
            self.add_error("password_confirmation", "Passwords do not match.")
        return cleaned_data


class CustomUserUpdateForm(UserChangeForm):
    password = None

    class Meta:
        model = CustomUser
        fields = [
            "firstname",
            "lastname",
            "username",
            "email",
            "date_of_birth",
            'profile_picture',
        ]  # Adjusted field names

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove help text for the username field
        self.fields["username"].help_text = None

        # # Customize labels and placeholders if needed
        # self.fields["username"].label = "Username"
        # self.fields["email"].label = "Email Address"
        self.fields["firstname"].label = "First Name"
        self.fields["lastname"].label = "Last Name"

        for field_name, field in self.fields.items():
            field.widget.attrs.update(
                {"class": "form-control"}
            )  # Add Bootstrap class for styling

        # Add a date picker widget for date_of_birth field
        self.fields["date_of_birth"].widget = forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "placeholder": "Select a date",
                "autocomplete": "off",  # Disable autocomplete to prevent browser suggestions
            }
        )


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Old Password",
                "autofocus": True,
            }
        ),
    )
    new_password1 = forms.CharField(
        label="",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "New Password"}
        ),
    )
    new_password2 = forms.CharField(
        label="",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm New Password"}
        ),
    )

    class Meta:
        model = CustomUser
        fields = ["old_password", "new_password1", "new_password2"]


class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ["field_name", "field_acres", "crop"]
        widgets = {
            "field_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter field name",
                    "autofocus": True,
                }
            ),
            "field_acres": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter field size in acres",
                }
            ),
            "crop": forms.Select(attrs={"class": "form-control"}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["barangay", "city_municipality", "country", "latitude", "longitude"]
        widgets = {
            "barangay": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter barangay"}
            ),
            "city_municipality": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter city or municipality",
                }
            ),
            "country": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter country"}
            ),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
        }

    def clean_city_municipality(self):
        city = self.cleaned_data.get("city_municipality")
        if city.strip().lower() != "cebu city":
            raise ValidationError("The address must be in Cebu City.")
        return city


class SoilDataForm(forms.ModelForm):
    class Meta:
        model = SoilData
        fields = ["nitrogen", "phosphorous", "potassium", "ph"]
        widgets = {
            "nitrogen": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Enter nitrogen level"}
            ),
            "phosphorous": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter phosphorous level",
                }
            ),
            "potassium": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Enter potassium level"}
            ),
            "ph": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Enter pH level"}
            ),
        }
