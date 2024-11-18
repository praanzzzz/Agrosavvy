from django import forms
from .models import (
    Field,
    FieldCropData,
    FieldSoilData,
    Address,
    FieldSoilData,
    CustomUser,
    PendingUser,
    ReviewRating,
    Barangay,
    ImageAnalysis,
    Notification,
    UserAddress,
    RoleUser,
)
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator




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
            "official_user_id",
            "firstname",
            "lastname",
            "username",
            "email",
            "date_of_birth",
            "gender",
            "useraddress",
            "password",

        ]
        widgets = {
            "official_user_id": forms.TextInput(attrs={"class": "form-control"}),
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
            "gender": forms.Select(attrs={"class": "form-control"}),
            "useraddress": forms.Select(attrs={"class": "form-control"}),
        }


    def clean_official_user_id(self):
        official_user_id = self.cleaned_data.get("official_user_id")
        
        if CustomUser.objects.filter(official_user_id=official_user_id).exists():
            raise forms.ValidationError("The user ID is already in use.")
            
        if PendingUser.objects.filter(official_user_id=official_user_id).exists():
            raise forms.ValidationError("ID is already in use and is waiting for approval.")
            
        return official_user_id

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already used.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already in use.")
            
        if PendingUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use and is waiting for approval.")
            
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
            "gender",
            "email",
            "date_of_birth",
            "useraddress",
            "profile_picture",
            
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
        self.fields["useraddress"].label = "Address"
        self.fields["profile_picture"].label = "Profile Picture"
        self.fields["gender"].disabled = True

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
        fields = ["field_name", "field_acres"]
        labels = {
            "field_acres": "Field Hectares"
        }
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
                    "placeholder": "Enter field size in hectares",
                }
            ),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["barangay", "city_municipality", "country", "latitude", "longitude"]
        widgets = {
            # "barangay": forms.TextInput(
            #     attrs={"class": "form-control", "placeholder": "Enter barangay"}
            # ),

            # selection barangay code
            "barangay": forms.Select(
                attrs={"class": "form-control", "placeholder": "Enter barangay"}
            ),

        
            "city_municipality": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter city or municipality",
                    "readonly": "readonly",
                    "value": "Cebu City",
                }
            ),
            "country": forms.HiddenInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter country",
                    "readonly": "readonly",
                    "value": "Philippines",
                }
            ),
            # "latitude": forms.HiddenInput(),
            # "longitude": forms.HiddenInput(),
            "latitude": forms.NumberInput(
                  attrs={
                    "class": "form-control",
                    "placeholder": "Click show on map to get coordinates",
                    "readonly": "readonly",
                }
            ),
            "longitude": forms.NumberInput(
                  attrs={
                    "class": "form-control",
                    "placeholder": "Click show on map to get coordinates",
                    "readonly": "readonly",
                }
            ),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['barangay'].queryset = Barangay.objects.all().order_by('brgy_name')



class FieldCropForm(forms.ModelForm):
    class Meta:
        model = FieldCropData
        fields = ["crop_planted", "planting_date"]
        widgets = {
            "crop_planted": forms.Select(attrs={"class": "form-control"}),
            "planting_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }



class FieldSoilDataForm(forms.ModelForm):
    class Meta:
        model = FieldSoilData
        fields = ["nitrogen", "phosphorous", "potassium", "ph", "record_date"]
        widgets = {
            # field = autoselect something
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
                attrs={"class": "form-control", "placeholder": "Enter pH level","min": 0, "max": 10,}
            ),
            "record_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }


class ReviewratingForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ["rating", "review_header", "review_body"]
        widgets = {
            "rating": forms.Select(
                choices=[
                    ("1", "Excellent"),
                    ("2", "Good"),
                    ("3", "Average"),
                    ("4", "Bad"),
                    ("5", "Worse"),
                ],
                attrs={"class": "form-control"},
            ),
            "review_header": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter review header"}
            ),
            "review_body": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Enter your review"}
            ),
        }




# class ImageAnalysisForm(forms.ModelForm):
#     class Meta:
#         model = ImageAnalysis
#         fields = ['image']
#         widgets = {
#             'image': forms.ClearableFileInput(attrs={
#                 'class': 'form-control-file', 
#             })
#         }

class ImageAnalysisForm(forms.ModelForm):
    class Meta:
        model = ImageAnalysis
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control-file form-control',  # Bootstrap class for form styling
                'accept': 'image/*',  # Restrict to image files
                'placeholder': 'Choose an image',  # Add placeholder text
            })
        }



class CreateNotificationForm(forms.ModelForm):
    NOTIF_CHOICES = [
        ('all', 'All Users'),
        ('single_user', 'Single User'),
        ('role', 'By Role'),
        ('useraddress', 'By User Address'),
    ]

    notification_type = forms.ChoiceField(choices=NOTIF_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    user_receiver = forms.ModelChoiceField(queryset=CustomUser.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    role = forms.ModelChoiceField(queryset=RoleUser.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    useraddress = forms.ModelChoiceField(queryset=UserAddress.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}), required=False)

    class Meta:
        model = Notification
        fields = ['subject', 'message']
        widgets = {
            "subject": forms.TextInput(attrs={'class': 'form-control'}),
            "message": forms.Textarea(attrs={'class': 'form-control'}),
        }