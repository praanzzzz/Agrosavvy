from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Field, Address, SoilData, CustomUser
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm


class CustomUserUpdateForm(UserChangeForm):
    password = None

    class Meta:
        model = CustomUser
        fields = ["firstname", "lastname","username", "email", "date_of_birth"]  # Adjusted field names

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
        self.fields["date_of_birth"].widget = forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "placeholder": "Select a date",
            "autocomplete": "off",  # Disable autocomplete to prevent browser suggestions
        })


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Old Password", "autofocus": True}
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
                attrs={"class": "form-control", "placeholder": "Enter field name", "autofocus": True}
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


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )


# we can call username, p1 and p2 since we use usercrreationform which has default fields for these fields.
class SignUpForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    # fields from models
    firstname = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control","autofocus": True}))
    lastname = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))

    # connecting default and custom fields from usercreationforms to abstractuser default and custom fields
    class Meta:
        model = CustomUser
        fields = (
            "username",
            "password1",
            "password2",
            "email",
            "firstname",
            "lastname",
        )
