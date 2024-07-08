from .models import Field, get_weather_data, CustomUser, PendingUser
from .forms import (
    FieldForm,
    AddressForm,
    SoilDataForm,
    LoginForm,
    CustomUserUpdateForm,
    CustomPasswordChangeForm,
    PendingUserForm,
)
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import json
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.hashers import check_password

#               PRAgab19-5158-794


# authentication logic pages
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


# # logic sign up for users with direct sign up (no approval needed)
# def register_da_admin(request):
#     if request.method == "POST":
#         form = SignUpForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.is_da_admin = True
#             user.request_date = now()
#             user.save()
#             messages.success(
#                 request,
#                 "Account is now for validation by the admin. Please wait for 24 hours",
#             )
#             return redirect("my_login")
#         else:
#             messages.error(request, "Please check the form.")
#     else:
#         form = SignUpForm()
#     return render(request, "auth_pages/register_da_admin.html", {"form": form})


def register_barangay_officer(request):
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
            messages.error(request, "Please check the form")
    else:
        form = PendingUserForm()
    return render(request, "auth_pages/register_barangay_officer.html", {"form": form})


def register_farmer(request):
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
        return redirect("my_login")
    else:
        return redirect("forbidden")


# Main pages
def dashboard(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        fields = Field.objects.all()
        return render(request, "app_agrosavvy/dashboard.html", {"fields": fields})
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
        context = {"location": location, "weather_data": weather_data}
        return render(request, "app_agrosavvy/weather.html", context)
    else:
        return redirect("forbidden")


# update name, email and username and also add picture
def settings(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        user = get_object_or_404(CustomUser, pk=request.user.pk)

        if request.method == "POST":
            updateprofileform = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
            if updateprofileform.is_valid():
                updateprofileform.save()
                messages.success(request, "Profile updated successfully.")
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


# MANAGE ACCOUNT PROFILE VIEWS -SETTINGS EXTENSION
def password_change(request):
    if request.user.is_authenticated:
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


# MANAGE FIELDS VIEWS
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


def bofa_ai(request):
    return render(request, "bofa_pages/bofa_ai.html", {})


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
            updateprofileform = CustomUserUpdateForm(request.POST, instance=user)
            if updateprofileform.is_valid():
                updateprofileform.save()
                messages.success(request, "Profile updated successfully.")
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


# MANAGE ACCOUNT PROFILE VIEWS -SETTINGS EXTENSION
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


# CRUD FOR BOFA
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
