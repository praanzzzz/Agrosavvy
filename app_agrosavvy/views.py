# from django.conf import settings
from .models import Field, get_weather_data, CustomUser, PendingUser, Crop, RoleUser, FieldSoilData, FieldCropData
from .forms import (
    FieldForm,
    AddressForm,
    FieldSoilDataForm,
    FieldCropForm,
    LoginForm,
    CustomUserUpdateForm,
    CustomPasswordChangeForm,
    PendingUserForm,
    ReviewratingForm,
)

# others
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import json
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.hashers import check_password
import requests
from django.urls import reverse

# from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count 
from django.utils import timezone
from datetime import timedelta

#           PRAgab19-5158-794



# Main pages
# @csrf_exempt
def dashboard(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
        fields = Field.objects.all()
        crops = Crop.objects.all()
        active_users = CustomUser.objects.filter(active_status=True)
        total_acres = fields.aggregate(Sum("field_acres"))["field_acres__sum"] or 0
        reviewrating_context = reviewrating(request)

        # pie charts 
        labels = []
        data = []
        # Aggregate total acres for each crop
        queryset = FieldCropData.objects.values('crop_planted__crop_type').annotate(
            total_acres=Sum('field__field_acres')
        )
        # Prepare data for the chart
        labels = [entry['crop_planted__crop_type'] for entry in queryset]
        data = [entry['total_acres'] for entry in queryset]


        # field registration over time line chart
        # Set a time range for the last 12 months
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)
        
        # Aggregate the number of fields registered each month using created_at
        field_data = Field.objects.filter(
            created_at__range=[start_date, end_date]
        ).extra(select={'month': "strftime('%%Y-%%m', created_at)"}).values('month').annotate(count=Count('field_id')).order_by('month')

        # Prepare data for Chart.js
        labelsfield = [data['month'] for data in field_data]
        datafield = [data['count'] for data in field_data]

        context = {
            "fields": fields,
            "crops": crops,
            "field_count": fields.count(),
            "active_user_count": active_users.count(),
            "total_acres": total_acres,
            #charts
            "labels": labels,
            "data": data,
            "labelsfield": labelsfield,
            "datafield": datafield,

        }
        context.update(reviewrating_context)
        return render(request, "app_agrosavvy/dashboard.html", context)
    else:
        return redirect("forbidden")
    


def ai(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
        return render(request, "app_agrosavvy/ai.html", {})
    else:
        return redirect("forbidden")



def map(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
        fields_json = []

        # Fetches all field crop data (wrong)
        # add filters to show only the current crop planted. (not the history or all data)
        field_crop_data = FieldCropData.objects.select_related('field', 'crop_planted')

        for data in field_crop_data:
            if data.field.address:
                fields_json.append(
                    {
                        "name": data.field.field_name,
                        "acres": data.field.field_acres,
                        "latitude": data.field.address.latitude,
                        "longitude": data.field.address.longitude,
                        "crop": data.crop_planted.crop_type,
                    }
                )

        context = {
            "fields_json": json.dumps(fields_json, cls=DjangoJSONEncoder),
            "crops": Crop.objects.all(),
        }
        return render(request, "app_agrosavvy/map.html", context)
    else:
        return redirect("forbidden")


def add_field(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
        if request.method == "POST":
            field_form = FieldForm(request.POST)
            address_form = AddressForm(request.POST)
            if (
                field_form.is_valid()
                and address_form.is_valid                
            ):
                address = address_form.save()             
                field = field_form.save(commit=False)
                field.address = address               
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
                        },
                    }
                )
        else:
            field_form = FieldForm()
            address_form = AddressForm()
        context = {
            "field_form": field_form,
            "address_form": address_form,
        }
        return render(request, "app_agrosavvy/add_field.html", context)
    else:
        return redirect("forbidden")


def weather(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
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
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
        user = get_object_or_404(CustomUser, pk=request.user.pk)

        if request.method == "POST":
            updateprofileform = CustomUserUpdateForm(
                request.POST, request.FILES, instance=user
            )
            if updateprofileform.is_valid():
                updateprofileform.save()
                messages.success(request, "Profile updated successfully.")
                return redirect("settings")
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














# manage fields/ farms
def manage_field(request, field_id):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
        field = get_object_or_404(Field, field_id=field_id) # used for reference or select a specific field
        fieldsoildata = FieldSoilData.objects.filter(field=field) # displays soil data history of a field
        fieldcropdata = FieldCropData.objects.filter(field=field)# displays crop data history of a field

        # Create form instance for adding soil data
        asdform = FieldSoilDataForm() #form for add soil data
        acdform = FieldCropForm()

        # Create a dictionary of forms for each soil and crop data instance
        fsdforms = {fsd.soil_id: FieldSoilDataForm(instance=fsd) for fsd in fieldsoildata}
        fcdforms  = {fcd.fieldcrop_id: FieldCropForm(instance=fcd) for fcd in fieldcropdata}


        # to make it accessible by the template
        context = {
            "field": field,
            "fieldsoildata": fieldsoildata,
            "fieldcropdata": fieldcropdata,
            "asdform": asdform,
            "acdform": acdform,
            "fsdforms": fsdforms, 
            "fcdforms": fcdforms,
        }
        return render(request, "app_agrosavvy/manage_field.html", context)
    else:
        return redirect("forbidden")
    

def delete_field(request, field_id):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
        field = get_object_or_404(Field, pk=field_id)
        field.delete()
        messages.success(request, "Field is successfuly deleted")
        return redirect("dashboard")
    else:
        return redirect("forbidden")


def update_field(request, field_id):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
        field = get_object_or_404(Field, field_id=field_id)
        if request.method == "POST":
            field_form = FieldForm(request.POST, instance=field) 
            address_instance = field.address
            address_form = AddressForm(request.POST, instance=address_instance)
            if (
                field_form.is_valid()
                and address_form.is_valid()             
            ):
                updated_field = field_form.save(commit=False)
                updated_field.owner = field.owner             
                updated_field.save()
                updated_address = address_form.save()
                return JsonResponse({"status": "success"})
            else:
                return JsonResponse(
                    {
                        "status": "error",
                        "errors": {
                            "field_form": field_form.errors,
                            "address_form": address_form.errors,                          
                        },
                    }
                )
        # if get request (opening the page only)
        else:
            field_form = FieldForm(instance=field)
            address_form = AddressForm(instance=field.address)
        context = {
            "field_form": field_form,
            "address_form": address_form,            
        }
        return render(request, "app_agrosavvy/update_field.html", context)
    else:
        return redirect("forbidden")



















# Brgy officers and farmers pages
# main pages


def bofa_dashboard(request):
    if request.user.is_authenticated and (
        request.user.roleuser.roleuser == "brgy_officer"
        or request.user.roleuser.roleuser == "farmer"
    ):
        
        fields = Field.objects.filter(owner=request.user)
        total_acres = Field.objects.filter(owner=request.user).aggregate(Sum("field_acres"))["field_acres__sum"] or 0
        reviewwrating_context = reviewrating(request)

        owner = request.user 

        # Aggregate total acres for each crop, filtered by the owner's fields
        queryset = FieldCropData.objects.filter(field__owner=owner).values('crop_planted__crop_type').annotate(
            total_acres=Sum('field__field_acres')
        )

        # Prepare data for the chart
        labels = [entry['crop_planted__crop_type'] for entry in queryset]
        data = [entry['total_acres'] for entry in queryset]




        context = {
            "fields": fields,
            "field_count": fields.count(),
            "total_acres": total_acres,
            "labels": labels,
            "data": data,
            }
        context.update(reviewwrating_context)
        return render(request, "bofa_pages/bofa_dashboard.html", context)
    else:
        return redirect("forbidden")



def bofa_ai(request):
    if request.user.is_authenticated and (
    request.user.roleuser.roleuser == "brgy_officer"
    or request.user.roleuser.roleuser == "farmer"):
        return render(request, "bofa_pages/bofa_ai.html", {})

# no auth yet and filters
def bofa_map(request):
    fields_json = []

    # Fetch all field crop data
    field_crop_data = FieldCropData.objects.select_related('field', 'crop_planted')

    for data in field_crop_data:
        if data.field.address:
            fields_json.append(
                {
                    "name": data.field.field_name,
                    "acres": data.field.field_acres,
                    "latitude": data.field.address.latitude,
                    "longitude": data.field.address.longitude,
                    "crop": data.crop_planted.crop_type,
                }
            )

    context = {
        "fields_json": json.dumps(fields_json, cls=DjangoJSONEncoder),
        "crops": Crop.objects.all(),
    }
    return render(request, "bofa_pages/bofa_map.html", context)



def bofa_add_field(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "brgy_officer" or request.user.roleuser.roleuser == "farmer"
    ):
        if request.method == "POST":
            field_form = FieldForm(request.POST)
            address_form = AddressForm(request.POST)          
            if (
                field_form.is_valid() and address_form.is_valid            
            ):
                address = address_form.save()               
                field = field_form.save(commit=False)
                field.address = address
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
                        },
                    }
                )
        else:
            field_form = FieldForm()
            address_form = AddressForm()

        context = {
            "field_form": field_form,
            "address_form": address_form,
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
        request.user.roleuser.roleuser == "brgy_officer"
        or request.user.roleuser.roleuser == "farmer"
    ):
        user = get_object_or_404(CustomUser, pk=request.user.pk)

        if request.method == "POST":
            updateprofileform = CustomUserUpdateForm(
                request.POST, request.FILES, instance=user
            )
            if updateprofileform.is_valid():
                updateprofileform.save()
                messages.success(request, "Profile updated successfully.")
                return redirect("bofa_settings")
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










# manage fields/ farms
def bofa_manage_field(request, field_id):
    if request.user.is_authenticated and (
        request.user.roleuser.roleuser == "brgy_officer"
        or request.user.roleuser.roleuser == "farmer"
    ):
         
        field = get_object_or_404(Field, field_id=field_id)
        fieldsoildata = FieldSoilData.objects.filter(field=field)
        fieldcropdata = FieldCropData.objects.filter(field=field)
        
        asdform = FieldSoilDataForm()
        acdform = FieldCropForm()

        # Create a dictionary of forms for each soil and crop data instance
        fsdforms = {fsd.soil_id: FieldSoilDataForm(instance=fsd) for fsd in fieldsoildata}
        fcdforms  = {fcd.fieldcrop_id: FieldCropForm(instance=fcd) for fcd in fieldcropdata}
        
        context ={
            "field":field,
            "fieldsoildata": fieldsoildata,
            "fieldcropdata": fieldcropdata,
            "asdform": asdform,
            "acdform": acdform,
            "fsdforms": fsdforms, 
            "fcdforms": fcdforms,
        }
        return render(request, "bofa_pages/bofa_manage_field.html", context)
    else:
        return redirect("forbidden")


def bofa_delete_field(request, field_id):
    if request.user.is_authenticated and (
        request.user.roleuser.roleuser == "brgy_officer"
        or request.user.roleuser.roleuser == "farmer"
    ):
        field = get_object_or_404(Field, pk=field_id)

        if field.owner != request.user:
            return redirect("forbidden")
        
        field.delete()
        return redirect("bofa_dashboard")
    else:
        return redirect("forbidden")


def bofa_update_field(request, field_id):
    if request.user.is_authenticated and (
        request.user.roleuser.roleuser == "brgy_officer"
        or request.user.roleuser.roleuser == "farmer"
    ):
        field = get_object_or_404(Field, pk=field_id)

        if field.owner != request.user:
            return redirect("forbidden")
        
        if request.method == "POST":
            field_form = FieldForm(request.POST, instance=field)
            address_instance = field.address           
            address_form = AddressForm(request.POST, instance=address_instance)
            if (
                field_form.is_valid()
                and address_form.is_valid()
            ):
                updated_field = field_form.save(commit=False)
                updated_field.owner = field.owner
                updated_field.save()
                updated_address = address_form.save()
                return JsonResponse({"status": "success"})
            else:
                return JsonResponse(
                    {
                        "status": "error",
                        "errors": {
                            "field_form": field_form.errors,
                            "address_form": address_form.errors,
                        },
                    }
                )
        else:
            field_form = FieldForm(instance=field)
            address_form = AddressForm(instance=field.address)

        context = {
            "field_form": field_form,
            "address_form": address_form,
        }
        return render(request, "bofa_pages/bofa_update_field.html", context)
    else:
        return redirect("forbidden")



















# callable functions


def reviewrating(request):
    if request.method == "POST":
        rform = ReviewratingForm(request.POST)
        if rform.is_valid():
            rrform = rform.save(commit=False)
            rrform.rate_date = now()
            rrform.reviewer = request.user
            rrform.save()
            messages.success(request, "Thank you for submitting feedback.")
            if request.user.roleuser.roleuser == "da_admin":
                return redirect("dashboard")
            elif (
                request.user.roleuser.roleuser == "barangay_officer"
                or request.user.roleuser.roleuser == "farmer"
            ):
                return redirect("bofa_dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        rform = ReviewratingForm()

    return {"rform": rform}






    

# to be used for admin and bofa users
def add_soil_data(request, field_id):
    field = get_object_or_404(Field, field_id=field_id)
    if request.user.is_authenticated:
        if request.method == "POST":
            asdform = FieldSoilDataForm(request.POST)
            if asdform.is_valid():
                soil_data = asdform.save(commit=False)
                soil_data.field = field
                soil_data.save()
                messages.success(request, "Soil data saved successfully.")
                if request.user.roleuser.roleuser == "da_admin":
                    return redirect(reverse("manage_field", kwargs={"field_id": field_id}))
                elif request.user.roleuser.roleuser in ["brgy_officer", "farmer"]:
                   return redirect(reverse("bofa_manage_field", kwargs={"field_id": field_id}))
            else:
                messages.error(request, "Form invalid")
        else:
            asdform = FieldSoilDataForm()
        return {"asdform": asdform, "field": field}
    else:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect("forbidden")
    
    
def add_crop_data(request, field_id):
    field = get_object_or_404(Field, field_id=field_id)
    if request.user.is_authenticated:
        if request.method=='POST':
            acdform=FieldCropForm(request.POST)
            if acdform.is_valid:
                crop_data = acdform.save(commit=False)
                crop_data.field = field
                crop_data.save()
                messages.success(request, "Crop data successfully saved.")
                if request.user.roleuser.roleuser == "da_admin":
                    return redirect(reverse("manage_field", kwargs={"field_id": field_id}))
                elif request.user.roleuser.roleuser in ["brgy_officer", "farmer"]:
                    return redirect(reverse("bofa_manage_field", kwargs={"field_id": field_id}))
            else:
                messages.error(request, "Form invalid")
        else:
            acdform = FieldCropForm()
        return {"acdform": acdform, "field": field}
    else:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect("forbidden")


def update_soil_data(request, field_id, soil_id):
    if request.user.is_authenticated:
        soil = get_object_or_404(FieldSoilData, soil_id=soil_id)
        field = get_object_or_404(Field, field_id=field_id)
        if request.method == "POST":
            fsdform = FieldSoilDataForm(request.POST, instance=soil)
            if fsdform.is_valid():
                updated_soil_data = fsdform.save(commit=False)
                updated_soil_data.field = field
                updated_soil_data.save()
                messages.success(request, "Soil data updated successfully.")
                if request.user.roleuser.roleuser == "da_admin":
                    return redirect(reverse("manage_field", kwargs={"field_id": field_id}))
                elif request.user.roleuser.roleuser in ["brgy_officer", "farmer"]:
                    return redirect(reverse("bofa_manage_field", kwargs={"field_id": field_id}))
                

                # return redirect('manage_field', field_id=field_id)
            else:
                messages.error(request, "Error updating soil data.") 
        else:
            # Show the current values in the form
            fsdform = FieldSoilDataForm(instance=soil)
        return {"fsdform": fsdform, "soil": soil}
    else:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('forbidden')


    

def update_crop_data(request, fieldcrop_id, field_id):
    if request.user.is_authenticated:
        crop = get_object_or_404(FieldCropData, fieldcrop_id=fieldcrop_id)
        field = get_object_or_404(Field, field_id=field_id)
        if request.method == "POST":
            fcdform = FieldCropForm(request.POST, instance=crop)
            if fcdform.is_valid():
                updated_crop_data = fcdform.save(commit=False)
                updated_crop_data.field = field
                updated_crop_data.save()
                messages.success(request, "Crop data updated successfully.")
                # return redirect('manage_field', field_id=field_id)
                if request.user.roleuser.roleuser == "da_admin":
                    return redirect(reverse("manage_field", kwargs={"field_id": field_id}))
                elif request.user.roleuser.roleuser in ["brgy_officer", "farmer"]:
                    return redirect(reverse("bofa_manage_field", kwargs={"field_id": field_id}))
            else:
                messages.error(request, "Error updating crop data.")
        else:
            # Show the current values in the form
            fcdform = FieldCropForm(instance=crop)
        return {"fcdform": fcdform, "crop": crop}
        
    else:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('forbidden')



    

def delete_soil_data(request, soil_id):
    soil_data = get_object_or_404(FieldSoilData, soil_id=soil_id)
    field_id = soil_data.field.field_id
    if request.user.is_authenticated:
        if request.method == "POST":
            soil_data.delete()
            messages.success(request, "Soil data deleted successfully.")
            return redirect(reverse("manage_field", kwargs={"field_id": field_id}))
        else:
            messages.error(request, "Invalid request.")
            return redirect(reverse("bofa_manage_field", kwargs={"field_id": field_id}))
    else:
        return redirect("forbidden")

def delete_crop_data(request, fieldcrop_id):
    crop_data = get_object_or_404(FieldCropData, fieldcrop_id=fieldcrop_id)
    field_id = crop_data.field.field_id
    if request.user.is_authenticated:
        if request.method == "POST":
            crop_data.delete()
            messages.success(request, "Crop data deleted successfully.")
            return redirect(reverse("manage_field", kwargs={"field_id": field_id}))
        else:
            messages.error(request, "Invalid request.")
            return redirect(reverse("bofa_manage_field", kwargs={"field_id": field_id}))
    else:
        return redirect("forbidden")





















# authentication related codes
def landing_page(request):
    return render(request, "app_agrosavvy/landing_page.html", {})


def register_da_admin(request):
    if request.method == "POST":
        form = PendingUserForm(request.POST)
        if form.is_valid():
            pending_user = form.save(commit=False)
            # pending_user.is_da_admin = True
            da_admin = RoleUser.objects.get(roleuser="da_admin")
            pending_user.roleuser = da_admin
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
            brgy_officer = RoleUser.objects.get(roleuser="brgy_officer")
            pending_user.roleuser = brgy_officer
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
            farmer = RoleUser.objects.get(roleuser="farmer")
            pending_user.roleuser = farmer
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
                    if user.roleuser.roleuser == "da_admin":
                        login(request, user)
                        messages.success(request, "Account logged in successfully")
                        return redirect("dashboard")
                    elif (
                        user.roleuser.roleuser == "barangay_officer"
                        or user.roleuser.roleuser == "farmer"
                    ):
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



def password_change(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
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
    if request.user.is_authenticated:
        if request.method == "POST":
            user = request.user
            user.active_status = False
            user.save()
            logout(request)
            messages.success(request, "Your account has been deactivated.")
            return redirect("landing_page")
        # return redirect('settings.html')
        return render(request, "app_agrosavvy/settings.html")
    else:
        return redirect("forbidden")




def bofa_password_change(request):
    if request.user.is_authenticated and (
        request.user.roleuser.roleuser == "brgy_officer"
        or request.user.roleuser.roleuser == "farmer"
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
    if request.user.is_authenticated and (
        request.user.roleuser.roleuser == "brgy_officer"
        or request.user.roleuser.roleuser == "farmer"
    ):
        if request.method == "POST":
            user = request.user
            user.active_status = False
            user.save()
            logout(request)
            messages.success(request, "Your account has been deactivated.")
            return redirect("landing_page")
        return redirect("bofa_settings")


# error pages
def forbidden(request):
    return render(request, "error_pages/forbidden.html", {})