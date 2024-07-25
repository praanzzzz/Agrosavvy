# from django.conf import settings
from .models import Field, get_weather_data, CustomUser, PendingUser, Crop
from .forms import (
    FieldForm,
    AddressForm,
    SoilDataForm,
    LoginForm,
    CustomUserUpdateForm,
    CustomPasswordChangeForm,
    PendingUserForm,
    AskrecoForm,
)

#others
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import json
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.hashers import check_password
import requests
from django.views.decorators.csrf import csrf_exempt

# for charts in dashboard
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from django.db.models import Count

#           PRAgab19-5158-794

# authentication pages
def landing_page(request):
    return render(request, "app_agrosavvy/landing_page.html", {})

def register_da_admin(request):
    if request.method == "POST":
        form = PendingUserForm(request.POST)
        if form.is_valid():
            pending_user = form.save(commit=False)
            pending_user.is_da_admin = True
            pending_user.request_date = now()
            pending_user.save()
            messages.success(
                request,
                "Account is now for validation by the admin. Please wait for 24 hours",
            )
            return redirect("my_login")
        else:
            messages.error(request, "Please check the form.")
    else:
        form = PendingUserForm()
    return render(request, "auth_pages/register_da_admin.html", {"form": form})

'''
# logic sign up for users with direct sign up (no approval needed)
def register_da_admin(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_da_admin = True
            user.request_date = now()
            user.save()
            messages.success(
                request,
                "Account is now for validation by the admin. Please wait for 24 hours",
            )
            return redirect("my_login")
        else:
            messages.error(request, "Please check the form.")
    else:
        form = SignUpForm()
    return render(request, "auth_pages/register_da_admin.html", {"form": form})
'''

def register_barangay_officer(request):
    if request.method == "POST":
        form = PendingUserForm(request.POST)
        if form.is_valid():
            pending_user = form.save(commit=False)
            pending_user.is_barangay_officer = True
            pending_user.request_date = now()
            pending_user.save()
            messages.success(
                request,
                "Account is now for validation by the admin. Please wait for 24 hours",
            )
            return redirect("my_login")
        else:
            messages.error(request, "Please check the form")
    else:
        form = PendingUserForm()
    return render(request, "auth_pages/register_barangay_officer.html", {"form": form})

def register_farmer(request):
    if request.method == "POST":
        form = PendingUserForm(request.POST)
        if form.is_valid():
            pending_user = form.save(commit=False)
            pending_user.is_farmer = True
            pending_user.request_date = now()
            pending_user.save()
            messages.success(
                request,
                "Account is now for validation by the admin. Please wait for 24 hours",
            )
            return redirect("my_login")
        else:
            messages.error(request, "Please check the form")
    else:
        form = PendingUserForm()
    return render(request, "auth_pages/register_farmer.html", {"form": form})

def my_login(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            # Check if the user is in the PendingUser table
            try:
                pending_user = PendingUser.objects.get(username=username)
                if check_password(password, pending_user.password):
                    messages.info(
                        request, "Your registration request is awaiting approval."
                    )
                    return render(request, "auth_pages/my_login.html", {"form": form})
                else:
                    messages.error(request, "Invalid username or password")
                    return render(request, "auth_pages/my_login.html", {"form": form})
            except PendingUser.DoesNotExist:
                pass

            user = authenticate(username=username, password=password)
            if user is not None:
                if user.active_status:
                    if user.is_da_admin:
                        login(request, user)
                        messages.success(request, "Account logged in successfully")
                        return redirect("dashboard")
                    elif user.is_barangay_officer or user.is_farmer:
                        login(request, user)
                        messages.success(request, "Account logged in successfully")
                        return redirect("bofa_dashboard")
                    else:
                        messages.error(request, "Invalid credentials")
                else:
                    messages.error(request, "Account is deactivated")
                    # redirect to a page that handles account reactivation request
            else:
                messages.error(
                    request,
                    "Invalid username or password",
                )
        else:
            messages.error(request, "Error validating form")
    return render(request, "auth_pages/my_login.html", {"form": form})

def my_logout(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Account logged out successfully")
        return redirect("landing_page")
    else:
        return redirect("forbidden")


# Main pages
@csrf_exempt
def dashboard(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        fields = Field.objects.all()
        crops = Crop.objects.all()
        crop_filter = request.GET.get('crop', None)
        line_chart = generate_line_chart(crop_filter)
        donut_chart = generate_donut_chart()
        context = {
            "fields": fields, 
            "donut_chart": donut_chart,
            "line_chart": line_chart,
            "crops": crops
        }
        return render(request, "app_agrosavvy/dashboard.html", context)
    else:
        return redirect("forbidden")  # or go to login, change later

def ai(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        return render(request, "app_agrosavvy/ai.html", {})
    else:
        return redirect("forbidden")

def map(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        fields = Field.objects.all()
        fields_json = []

        for field in fields:
            if field.address:
                fields_json.append(
                    {
                        "name": field.field_name,
                        "acres": field.field_acres,
                        "latitude": field.address.latitude,
                        "longitude": field.address.longitude,
                    }
                )

        context = {"fields_json": json.dumps(fields_json, cls=DjangoJSONEncoder)}
        return render(request, "app_agrosavvy/map.html", context)
    else:
        return redirect("forbidden")

def add_field(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        if request.method == "POST":
            field_form = FieldForm(request.POST)
            address_form = AddressForm(request.POST)
            soil_data_form = SoilDataForm(request.POST)

            if (
                field_form.is_valid()
                and address_form.is_valid
                and soil_data_form.is_valid
            ):
                address = address_form.save()
                soil_data = soil_data_form.save()
                field = field_form.save(commit=False)
                field.address = address
                field.soil_data = soil_data
                field.owner = request.user
                field.save()
                return JsonResponse({"status": "success"})
            else:
                return JsonResponse(
                    {
                        "status": "error",
                        "errors": {
                            "field_form": field_form.errors,
                            "address_form": address_form.errors,
                            "soil_data_form": soil_data_form.errors,
                        },
                    }
                )
        else:
            field_form = FieldForm()
            address_form = AddressForm()
            soil_data_form = SoilDataForm()
        context = {
            # 'mapbox_api_key': settings.MAPBOX_API_KEY,
            "field_form": field_form,
            "address_form": address_form,
            "soil_data_form": soil_data_form,
        }
        return render(request, "app_agrosavvy/add_field.html", context)
    else:
        return redirect("forbidden")

def weather(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        if request.method == "POST":
            location = request.POST.get("location")
            weather_data = get_weather_data(location)
        else:
            location = ""
            weather_data = None
        context = {
            "location": location, 
            "weather_data": weather_data,
            }
        return render(request, "app_agrosavvy/weather.html", context)
    else:
        return redirect("forbidden")

# update profile
def settings(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        user = get_object_or_404(CustomUser, pk=request.user.pk)

        if request.method == "POST":
            updateprofileform = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
            if updateprofileform.is_valid():
                updateprofileform.save()
                messages.success(request, "Profile updated successfully.")
                return redirect('settings')
            else:
                messages.error(
                    request, "Error updating profile. Please check the form."
                )
        else:
            updateprofileform = CustomUserUpdateForm(instance=user)

        context = {"updateprofileform": updateprofileform}
        return render(request, "app_agrosavvy/settings.html", context)
    else:
        return redirect("forbidden")
    


# sub pages
# password change
def password_change(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        user = get_object_or_404(CustomUser, pk=request.user.pk)

        if request.method == "POST":
            passwordchangeform = CustomPasswordChangeForm(request.user, request.POST)
            if passwordchangeform.is_valid():
                user = passwordchangeform.save()
                update_session_auth_hash(request, user)  # Maintain the user's session
                logout(request)
                messages.success(
                    request, "Your password has been changed. Please log in again."
                )
                return redirect("my_login")
            else:
                messages.error(
                    request, "Error updating profile. Please check the form."
                )
        else:
            passwordchangeform = CustomPasswordChangeForm(request.user)

        context = {"passwordchangeform": passwordchangeform}
        return render(
            request, "app_agrosavvy/settings_section/password_change.html", context
        )
    else:
        return redirect("forbidden")
    

def deactivate_account(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        if request.method == 'POST':
            user = request.user
            user.active_status = False
            user.save()
            logout(request)
            messages.success(request, 'Your account has been deactivated.')
            return redirect('landing_page')
        return redirect('settings')


# manage fields/ farms
def delete_field(request, field_id):
    if request.user.is_authenticated and request.user.is_da_admin:
        field = get_object_or_404(Field, pk=field_id)
        field.delete()
        return redirect("dashboard")
    else:
        return redirect("forbidden")

def update_field(request, field_id):
    if request.user.is_authenticated and request.user.is_da_admin:
        field = get_object_or_404(Field, field_id=field_id)

        if request.method == "POST":
            field_form = FieldForm(request.POST, instance=field)
            field_instance = Field.objects.get(field_id=field.field_id)
            address_instance = field.address
            soil_data_instance = field.soil_data

            address_form = AddressForm(request.POST, instance=address_instance)
            soil_data_form = SoilDataForm(request.POST, instance=soil_data_instance)

            if (
                field_form.is_valid()
                and address_form.is_valid()
                and soil_data_form.is_valid()
            ):
                updated_field = field_form.save(commit=False)
                # updated_field.owner = field.owner
                updated_field.owner = field_instance.owner
                updated_field.save()
                updated_address = address_form.save()
                updated_soil_data = soil_data_form.save()

                return JsonResponse({"status": "success"})
            else:
                return JsonResponse(
                    {
                        "status": "error",
                        "errors": {
                            "field_form": field_form.errors,
                            "address_form": address_form.errors,
                            "soil_data_form": soil_data_form.errors,
                        },
                    }
                )
        else:
            field_form = FieldForm(instance=field)
            address_form = AddressForm(instance=field.address)
            soil_data_form = SoilDataForm(instance=field.soil_data)

        context = {
            "field_form": field_form,
            "address_form": address_form,
            "soil_data_form": soil_data_form,
        }

        return render(request, "app_agrosavvy/update_field.html", context)
    else:
        return redirect("forbidden")














# Brgy officers and farmers pages
# main pages

def bofa_dashboard(request):
    if request.user.is_authenticated and (
        request.user.is_barangay_officer or request.user.is_farmer
    ):
        fields = Field.objects.filter(owner=request.user)
        return render(request, "bofa_pages/bofa_dashboard.html", {"fields": fields})
    else:
        return redirect("forbidden")

# no auth yet
def bofa_ai(request):
    return render(request, "bofa_pages/bofa_ai.html", {})

# no auth yet
def bofa_map(request):
    fields = Field.objects.all()
    fields_json = []

    for field in fields:
        if field.address:
            fields_json.append(
                {
                    "name": field.field_name,
                    "acres": field.field_acres,
                    "latitude": field.address.latitude,
                    "longitude": field.address.longitude,
                }
            )

    context = {"fields_json": json.dumps(fields_json, cls=DjangoJSONEncoder)}
    return render(request, "bofa_pages/bofa_map.html", context)


def bofa_add_field(request):
    if request.user.is_authenticated and (
        request.user.is_barangay_officer or request.user.is_farmer
    ):
        if request.method == "POST":
            field_form = FieldForm(request.POST)
            address_form = AddressForm(request.POST)
            soil_data_form = SoilDataForm(request.POST)
            if (
                field_form.is_valid()
                and address_form.is_valid
                and soil_data_form.is_valid
            ):
                address = address_form.save()
                soil_data = soil_data_form.save()
                field = field_form.save(commit=False)
                field.address = address
                field.soil_data = soil_data
                field.owner = request.user
                field.save()
                return JsonResponse({"status": "success"})
            else:
                return JsonResponse(
                    {
                        "status": "error",
                        "errors": {
                            "field_form": field_form.errors,
                            "address_form": address_form.errors,
                            "soil_data_form": soil_data_form.errors,
                        },
                    }
                )
        else:
            field_form = FieldForm()
            address_form = AddressForm()
            soil_data_form = SoilDataForm()
        context = {
            "field_form": field_form,
            "address_form": address_form,
            "soil_data_form": soil_data_form,
        }
        return render(request, "bofa_pages/bofa_add_field.html", context)
    else:
        return redirect("forbidden")

# no auth yet
def bofa_weather(request):
    if request.method == "POST":
        location = request.POST.get("location")
        weather_data = get_weather_data(location)
    else:
        location = ""
        weather_data = None

    context = {"location": location, "weather_data": weather_data}
    return render(request, "bofa_pages/bofa_weather.html", context)

def bofa_settings(request):
    if request.user.is_authenticated and (
        request.user.is_barangay_officer or request.user.is_farmer
    ):
        user = get_object_or_404(CustomUser, pk=request.user.pk)

        if request.method == "POST":
            updateprofileform = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
            if updateprofileform.is_valid():
                updateprofileform.save()
                messages.success(request, "Profile updated successfully.")
                return redirect('bofa_settings')
            else:
                messages.error(
                    request, "Error updating profile. Please check the form."
                )
        else:
            updateprofileform = CustomUserUpdateForm(instance=user)

        context = {"updateprofileform": updateprofileform}
        return render(request, "bofa_pages/bofa_settings.html", context)
    else:
        return redirect("forbidden")


# sub pages
def bofa_password_change(request):
    if request.user.is_authenticated and (
        request.user.is_barangay_officer or request.user.is_farmer
    ):
        user = get_object_or_404(CustomUser, pk=request.user.pk)

        if request.method == "POST":
            passwordchangeform = CustomPasswordChangeForm(request.user, request.POST)
            if passwordchangeform.is_valid():
                user = passwordchangeform.save()
                update_session_auth_hash(request, user)  # Maintain the user's session
                logout(request)
                messages.success(
                    request, "Your password has been changed. Please log in again."
                )
                return redirect("my_login")
            else:
                messages.error(
                    request, "Error updating profile. Please check the form."
                )
        else:
            passwordchangeform = CustomPasswordChangeForm(request.user)

        context = {"passwordchangeform": passwordchangeform}
        return render(
            request,
            "bofa_pages/bofa_settings_section/bofa_password_change.html",
            context,
        )
    else:
        return redirect("forbidden")
    
def bofa_deactivate_account(request):
    if request.user.is_authenticated and (request.user.is_barangay_officer or request.user.is_farmer):
        if request.method == 'POST':
            user = request.user
            user.active_status = False
            user.save()
            logout(request)
            messages.success(request, 'Your account has been deactivated.')
            return redirect('landing_page')
        return redirect('bofa_settings')

# manage fields/ farms
def bofa_delete_field(request, field_id):
    if request.user.is_authenticated and (
        request.user.is_barangay_officer or request.user.is_farmer
    ):
        field = get_object_or_404(Field, pk=field_id)
        field.delete()
        return redirect("bofa_dashboard")
    else:
        return redirect("forbidden")

def bofa_update_field(request, field_id):
    if request.user.is_authenticated and (
        request.user.is_barangay_officer or request.user.is_farmer
    ):
        field = get_object_or_404(Field, pk=field_id)

        if field.owner != request.user:
            return redirect("forbidden")

        if request.method == "POST":
            field_form = FieldForm(request.POST, instance=field)
            
            address_instance = field.address
            soil_data_instance = field.soil_data

            address_form = AddressForm(request.POST, instance=address_instance)
            soil_data_form = SoilDataForm(request.POST, instance=soil_data_instance)

            if (
                field_form.is_valid()
                and address_form.is_valid()
                and soil_data_form.is_valid()
            ):
                updated_field = field_form.save(commit=False)
                updated_field.owner = field.owner
                updated_field.save()
                updated_address = address_form.save()
                updated_soil_data = soil_data_form.save()
                return JsonResponse({"status": "success"})
            else:
                return JsonResponse(
                    {
                        "status": "error",
                        "errors": {
                            "field_form": field_form.errors,
                            "address_form": address_form.errors,
                            "soil_data_form": soil_data_form.errors,
                        },
                    }
                )
        else:
            field_form = FieldForm(instance=field)
            address_form = AddressForm(instance=field.address)
            soil_data_form = SoilDataForm(instance=field.soil_data)

        context = {
            "field_form": field_form,
            "address_form": address_form,
            "soil_data_form": soil_data_form,
        }
        return render(request, "bofa_pages/bofa_update_field.html", context)
    else:
        return redirect("forbidden")






# error pages
def forbidden(request):
    return render(request, "error_pages/forbidden.html", {})



# in progress (visualization in dashboard) -- made for da admin since there no filters yet
def generate_donut_chart():
  
    fields = Field.objects.all()
    crop_counts = {}

    for field in fields:
        crop = field.crop.crop_type if field.crop else 'No Crop'
        if crop in crop_counts:
            crop_counts[crop] += 1
        else:
            crop_counts[crop] = 1

 
    labels = crop_counts.keys()
    sizes = crop_counts.values()

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,  wedgeprops={'width': 0.3})
    ax.axis('equal')

    # Save chart to a string in memory
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read()).decode('utf-8')
    uri = 'data:image/png;base64,' + string

    return uri

def generate_line_chart(crop_filter=None):
    # Fetch field data
    fields = Field.objects.all()
    if crop_filter:
        fields = fields.filter(crop__crop_type=crop_filter)

    # Aggregate fields by creation date
    fields_by_date = fields.values('created_at__date').annotate(count=Count('field_id')).order_by('created_at__date')
    
    dates = [field['created_at__date'] for field in fields_by_date]
    counts = [field['count'] for field in fields_by_date]

    # Generate line chart
    fig, ax = plt.subplots()
    ax.plot(dates, counts, marker='o')
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Fields')
    ax.set_title('Fields Created Over Time')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save chart to a string in memory
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read()).decode('utf-8')
    uri = 'data:image/png;base64,' + string

    return uri




# remove goose ai since so dumb and expensive. 
# in progress (goose ai)
def get_crop_recommendations(nitrogen, phosphorous, potassium, ph):
  
    crop_types = Crop.objects.filter(crop_type__in=[choice[0] for choice in Crop.CROP_CHOICES]).values_list('crop_type', flat=True)
    prompt = f"Based on the soil data provided, recommend the most suitable crop type for planting from the following options: {', '.join(crop_types)}.  Soil data: Nitrogen: {nitrogen}, Phosphorous: {phosphorous}, Potassium: {potassium}, pH: {ph}."

    api_key = 'sk-W7yOrKk1jByIQP40mWh0lYC1Y21ADRC108itOMGCySlusNY0'
    gooseai_api_url = "https://api.goose.ai/v1/engines/gpt-j-6b/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "prompt": prompt,
        "max_tokens": 150 

    }

    response = requests.post(gooseai_api_url, headers=headers, json=data)

    if response.status_code == 200:
        recommendations = response.json()
        return recommendations.get("choices", [])
    else:
        return []

def address_input(request):
    if request.method == "POST":
        form = AskrecoForm(request.POST)
        if form.is_valid():
            nitrogen = form.cleaned_data['nitrogen']
            phosphorous = form.cleaned_data['phosphorous']
            potassium = form.cleaned_data['potassium']
            ph = form.cleaned_data['ph']

            recommendations = get_crop_recommendations(nitrogen, phosphorous, potassium, ph)
            return render(request, 'goose_ai/result.html', {'recommendations': recommendations})
    else:
        form = AskrecoForm()
    return render(request, 'goose_ai/address_input.html', {'form': form})
