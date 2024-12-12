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
from datetime import date
import re





class LoginForm(forms.Form):
    username = forms.CharField(
        label="",
        max_length=10,
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
        max_length = 50,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
    )







class PendingUserForm(forms.ModelForm):
    # basic validations, labels, and design
    official_user_id = forms.CharField(
        label = "Official User ID",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        error_messages = {
            'required': 'ID is required.',
            'max_length': 'ID cannot exceed 30 characters.',
        },
    )

    firstname = forms.CharField(
        label = "First Name",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        error_messages = {
            'required': 'First name is required.',
            'max_length': 'First name cannot exceed 30 characters.',
        },
    )

    middle_initial = forms.CharField(
        label = "Middle Initial",
        max_length=1,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "optional",
        })
    )

    lastname = forms.CharField(
        label = "Last Name",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        error_messages = {
            'required': 'Last name is required.',
            'max_length': 'Last name cannot exceed 30 characters.',
        },
    )

    username = forms.CharField(
        label="Username:",
        max_length=10,
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(attrs={"class": "form-control"}),
        error_messages={
            'required': 'Username is required.',
            'max_length': 'Username cannot exceed 10 characters.',
            'invalid': 'Enter a valid username.',
        },
    )

    contact_number = forms.CharField(
        max_length=10,
        error_messages={
            'required': 'Contact number is required.',
        },
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 9123456789',
                'pattern': r'\d{10}',  # Enforces a 10-digit input
                'title': 'Enter the last 10 digits of your phone number starting with 9 without spaces or symbols.',
            }
        ),
    )


    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        error_messages={
            'required': 'Password is required.',
        },
    )

    password_confirmation = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        error_messages={
            'required': 'Please confirm your password.',
        },
    )

    date_of_birth = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "placeholder": "Select a date",
                "autocomplete": "off",
            }
        ),
    )

    useraddress = forms.ModelChoiceField(
        queryset=UserAddress.objects.all(),  # Dynamically fetch all addresses
        label="Address",  # Change label
        widget=forms.Select(attrs={"class": "form-control"}),  # Add styling
        empty_label="Select an Address",  # Placeholder option
    )



    email = forms.EmailField(
        max_length=50, 
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    ),

    class Meta:
        model = PendingUser
        fields = [
            "official_user_id",
            "firstname",
            "middle_initial",
            "lastname",
            "username",
            "contact_number",
            "email",
            "date_of_birth",
            "gender",
            "useraddress",
            "password",
        ]

        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-control"}),
        }


    # business logic 
    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number', '')
        if not re.match(r'^9\d{9}$', contact_number):
            raise forms.ValidationError("Enter a valid 10-digit phone number starting with 9 (e.g., 9123456789).")
        if PendingUser.objects.filter(contact_number = contact_number).exists():
            raise forms.ValidationError("Contact number is already used by one of the pending user.")
        if CustomUser.objects.filter(contact_number=contact_number).exists():
            raise forms.ValidationError("Contact number is already used by one of the registered user.")
        return f'+63{contact_number}'
    

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob: 
            if dob > date.today():
                raise forms.ValidationError("The date of birth cannot be in the future.")
        return dob

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
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already in use.")
            
        if PendingUser.objects.filter(email__iexact=email).exists():
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
    
    firstname = forms.CharField(
        label = "First Name",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    middle_initial = forms.CharField(
        label = "Middle Initial",
        max_length=1,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "optional",
        })
    )

    lastname = forms.CharField(
        label = "Last Name",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    username = forms.CharField(
        label="Username",
        max_length=10,
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )


    contact_number = forms.CharField(
        max_length=10,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 9123456789',  # Example placeholder for the remaining digits
                'pattern': r'\d{10}',  # Enforces a 10-digit input
                'title': 'Enter the last 10 digits of your phone number starting with 9 without spaces or symbols.',
            }
        ),
    )

    date_of_birth = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "placeholder": "Select a date",
                "autocomplete": "off",
            }
        ),
    )

    email = forms.EmailField(
        max_length=50, 
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    ),


    class Meta:
        model = CustomUser
        fields = [
            "firstname",
            "middle_initial",
            "lastname",
            "username",
            "gender",
            "contact_number",
            "email",
            "date_of_birth",
            # "useraddress",
            "profile_picture",
        ]

        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-control"}),
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'form-control-file form-control',  # Bootstrap class for form styling
                'accept': 'image/*',  # Restrict to image files
                'placeholder': 'Choose an image',  # Add placeholder text
            })
        }
    

    # business logic
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob:  # Only validate if the field is not empty
            if dob > date.today():
                raise forms.ValidationError("The date of birth cannot be in the future.")
        return dob
    
    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number', '')
        if not re.match(r'^9\d{9}$', contact_number):
            raise forms.ValidationError("Enter a valid 10-digit phone number starting with 9 (e.g., 9123456789).")
        if CustomUser.objects.filter(contact_number=contact_number).exists():
            raise forms.ValidationError("Contact number is already used by one of the registered user.")
        return f'+63{contact_number}'


    def clean_username(self):
        username = self.cleaned_data.get("username")
        if CustomUser.objects.filter(username=username).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("This username is already used.")
        return username


    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email__iexact=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Email already in use.")
        return email
    





class CustomPasswordChangeForm(PasswordChangeForm):    
    class Meta:
        model = CustomUser
        fields = ["old_password", "new_password1", "new_password2"]

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
   



class FieldForm(forms.ModelForm):
    field_name = forms.CharField(
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter field name",
                "autofocus": True,
            }
        ),
    )

    field_acres = forms.DecimalField(
        label = "Hectares",
        max_digits=5,
        decimal_places=2,
        min_value=0, 
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter field size in hectares",
                "step": "0.01",  # Allows two decimal precision
                "min": "0",  # Restricts negative numbers at the HTML level
            }
        ),
    )

    class Meta:
        model = Field
        fields = ["field_name", "field_acres"]
        labels = {
            "field_acres": "Field Hectares"
        }


    def clean_field_acres(self):
        field_acres = self.cleaned_data.get("field_acres")
        if field_acres is not None:
            # Round to the nearest hundredth
            return round(field_acres, 2)
        return field_acres





class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["barangay", "city_municipality", "country", "latitude", "longitude"]
        widgets = {
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

    def clean_city(self):
        city = self.cleaned_data.get("city")
        if city != "Cebu City":
            raise forms.ValidationError("The City must be in Cebu City only.")
        return city
    
    def clean_country(self):
        country = self.cleaned_data.get("country")
        if country != "Philippines":
            raise forms.ValidationError('The country must be in the Philippines only.')
        return country
            

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")

        if latitude and longitude:
            current_instance = self.instance
            
            # Check if we're updating an existing object (i.e., it's not a new one) (only old instance has pk)
            if current_instance.pk:
                # Exclude the current instance from the search to avoid a conflict with itself
                existing_address = Address.objects.exclude(pk=current_instance.pk).filter(latitude=latitude, longitude=longitude)
            else:
                # If it's a new instance, just check for duplicates
                existing_address = Address.objects.filter(latitude=latitude, longitude=longitude)

            # If the address already exists (except for the current one), raise validation error
            if existing_address.exists():
                raise forms.ValidationError("The location with these coordinates already exists. Please move the marker.")
        return cleaned_data


 


       




class FieldCropForm(forms.ModelForm):
    planting_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "placeholder": "Select a date",
                "autocomplete": "off",
            }
        ),
    )

    class Meta:
        model = FieldCropData
        fields = ["crop_planted", "planting_date"]
        widgets = {
            "crop_planted": forms.Select(attrs={"class": "form-control"}),
        }

    def clean_planting_date(self):
        pd = self.cleaned_data.get("planting_date")
        if pd:  # Only validate if the field is not empty
            if pd > date.today():
                raise forms.ValidationError("The planting date cannot be in the future.")
        return pd




class FieldSoilDataForm(forms.ModelForm):
    nitrogen = forms.DecimalField(
        max_digits=5,
        required=False,
        decimal_places=2,
        min_value=0, 
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter nitrogel level",
                "step": "0.01",  # Allows two decimal precision
                "min": "0",  # Restricts negative numbers at the HTML level
            }
        ),
        error_messages={
            "invalid": "Enter a valid number.",
            "min_value": "Value must be a non-negative number.",
        },
    )

    phosphorous = forms.DecimalField(
        max_digits=5,
        required=False,
        decimal_places=2,
        min_value=0, 
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter phosphorous level",
                "step": "0.01",  # Allows two decimal precision
                "min": "0",  # Restricts negative numbers at the HTML level
            }
        ),
        error_messages={
            "invalid": "Enter a valid number.",
            "min_value": "Value must be a non-negative number.",
        },
    )


    potassium = forms.DecimalField(
        max_digits=5,
        required=False,
        decimal_places=2,
        min_value=0, 
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter potassium level",
                "step": "0.01",  # Allows two decimal precision
                "min": "0",  # Restricts negative numbers at the HTML level
            }
        ),
        error_messages={
            "invalid": "Enter a valid number.",
            "min_value": "Value must be a non-negative number.",
        },
    )


    ph = forms.DecimalField(
        max_digits=5,
        required=False,
        decimal_places=2,
        min_value=0, 
        max_value=10,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter pH level",
                "step": "0.01",  # Allows two decimal precision
                "min": "0",  # Restricts negative numbers at the HTML level
            }
        ),
        error_messages={
            "invalid": "Enter a valid number.",
            "min_value": "Value must be a non-negative number.",
        },
    )


    record_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "placeholder": "Select a date",
                "autocomplete": "off",
            }
        ),
    )

    class Meta:
        model = FieldSoilData
        fields = ["nitrogen", "phosphorous", "potassium", "ph", "record_date"]

    def clean_record_date(self):
        rd = self.cleaned_data.get("record_date")
        if rd:  # Only validate if the field is not empty
            if rd > date.today():
                raise forms.ValidationError("The record date cannot be in the future.")
        return rd



class ReviewratingForm(forms.ModelForm):
    review_header = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter subject",
                "autofocus": True,
            }
        ),
        error_messages={
            "required": "Subject is required.",
            "max_length": "Subject cannot exceed 30 characters.",
        },
    )

    review_body = forms.CharField(
        max_length=100,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Enter body",
                "rows": 3,
                "autofocus": True,
            }
        ),
        error_messages={
            "required": "Body is required.",
            "max_length": "Body cannot exceed 100 characters.",
        },
    )

    class Meta:
        model = ReviewRating
        fields = ["rating", "review_header", "review_body"]
        widgets = {
            "rating": forms.Select(
                choices=[("", "Select Rating")] + [
                    ("1", "Excellent"),
                    ("2", "Good"),
                    ("3", "Average"),
                    ("4", "Bad"),
                    ("5", "Worse"),
                ],
                attrs={"class": "form-control"},
            ),
        }

    # ensures data integrity if the form is 
    # submitted programmatically or via non-standard means.
    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        valid_choices = ["1", "2", "3", "4", "5"]
        if rating not in valid_choices:
            raise forms.ValidationError("Invalid rating value.")
        return rating






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



    subject = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter subject",
                "autofocus": True,
            }
        ),
        error_messages={
            "required": "Subject is required.",
            "max_length": "Subject cannot exceed 30 characters.",
        },
    )

    message = forms.CharField(
        max_length=200,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Enter Announcement",
                "autofocus": True,
            }
        ),
        error_messages={
            "required": "Message is required.",
            "max_length": "Message cannot exceed 200 characters.",
        },
    )

    notification_type = forms.ChoiceField(choices=NOTIF_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    user_receiver = forms.ModelChoiceField(queryset=CustomUser.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    role = forms.ModelChoiceField(queryset=RoleUser.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    useraddress = forms.ModelChoiceField(queryset=UserAddress.objects.all(), widget=forms.Select(attrs={'class': 'form-control'}), required=False)

    class Meta:
        model = Notification
        fields = ['subject', 'message']


    












