from .models import Field, Crop, get_weather_data
from .forms import FieldForm, AddressForm, SoilDataForm, SignUpForm, LoginForm
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.messages import success
from django.contrib.auth import authenticate, login, logout
from django.core.serializers.json import DjangoJSONEncoder


#PRAgab19-5158-794

#authentication logic pages

def landing_page(request):
    return render(request, 'app_agrosavvy/landing_page.html', {})

def register_da_admin(request):
    msg = None
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_da_admin = True
            user.save()
            msg = 'user created'
            return redirect('my_login')
        else:
            msg = 'form is not valid' 
    else:
        form = SignUpForm()
    return render(request,'auth_pages/register_da_admin.html', {'form': form, 'msg': msg})

def register_barangay_officer(request):
    msg = None
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_barangay_officer = True
            user.save()
            msg = 'user created'
            return redirect('my_login')
        else:
            msg = 'form is not valid'
    else:
        form = SignUpForm()
    return render(request,'auth_pages/register_barangay_officer.html', {'form': form, 'msg': msg})

def register_farmer(request):
    msg = None
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_farmer = True
            user.save()
            msg = 'user created'
            return redirect('my_login')
        else:
            msg = 'form is not valid'
    else:
        form = SignUpForm()
    return render(request,'auth_pages/register_farmer.html', {'form': form, 'msg': msg})

def my_login(request):
    form = LoginForm(request.POST or None)
    msg = None
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_da_admin:
                login(request, user)
                return redirect('dashboard')
            elif user is not None and (user.is_barangay_officer or user.is_farmer):
                login(request, user)    
                return redirect('bofa_dashboard')
            else:
                msg= 'invalid credentials'
        else:
            msg = 'error validating form'
    return render(request, 'auth_pages/my_login.html', {'form': form, 'msg': msg})

def my_logout(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('my_login')
    else:
        return redirect('forbidden')










# Main pages
def dashboard(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        fields = Field.objects.all()
        return render(request, 'app_agrosavvy/dashboard.html', {'fields': fields})
    else:
        return redirect('forbidden') #or go to login, change later
def ai(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        return render(request, 'app_agrosavvy/ai.html', {})
    else:
        return redirect('forbidden')
    
def map(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        fields = Field.objects.all()
        fields_json = []

        for field in fields:
            if field.address:
                fields_json.append({    
                    'name': field.field_name,
                    'acres': field.field_acres,
                    'latitude': field.address.latitude,
                    'longitude': field.address.longitude
                })

        context = {
            'fields_json': json.dumps(fields_json, cls=DjangoJSONEncoder)
        }   
        return render(request, 'app_agrosavvy/map.html', context)
    else:
        return redirect('forbidden')


def add_field(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        if request.method == 'POST':
            field_form = FieldForm(request.POST)
            address_form = AddressForm(request.POST)
            soil_data_form = SoilDataForm(request.POST)
            
            if field_form.is_valid() and address_form.is_valid and soil_data_form.is_valid:
                address = address_form.save()
                soil_data = soil_data_form.save()
                field = field_form.save(commit=False)
                field.address = address
                field.soil_data = soil_data
                field.owner = request.user
                field.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'errors': {
                    'field_form': field_form.errors,
                    'address_form': address_form.errors,
                    'soil_data_form': soil_data_form.errors,
                }})
        else:
            field_form = FieldForm()
            address_form = AddressForm()
            soil_data_form = SoilDataForm()
        context = {
            'field_form': field_form,
            'address_form': address_form,
            'soil_data_form': soil_data_form,
        }
        return render(request, 'app_agrosavvy/add_field.html', context)
    else:
        return redirect('forbidden')
    
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
        return redirect('forbidden')
    
def settings(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        return render(request, 'app_agrosavvy/settings.html', {})
    else:
        return redirect('forbidden')



# MANAGE ACCOUNT PROFILE VIEWS








# MANAGE FIELDS VIEWS
def delete_field(request, field_id):
    if request.user.is_authenticated and request.user.is_da_admin:
        field = get_object_or_404(Field, pk=field_id)
        field.delete()
        return redirect('dashboard')
    else:
        return redirect('forbidden')


#uses server side rendering
def update_field(request, field_id):
    if request.user.is_authenticated and request.user.is_da_admin:
        field = get_object_or_404(Field, field_id=field_id)

        if request.method == 'POST':
            field_form = FieldForm(request.POST, instance=field)
            address_instance = field.address
            soil_data_instance = field.soil_data

            address_form = AddressForm(request.POST, instance=address_instance)
            soil_data_form = SoilDataForm(request.POST, instance=soil_data_instance)

            if field_form.is_valid() and address_form.is_valid() and soil_data_form.is_valid():
                updated_field = field_form.save(commit=False)
                updated_field.owner = field.owner
                updated_field.save()
                updated_address = address_form.save()
                updated_soil_data = soil_data_form.save()

                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'errors': {
                    'field_form': field_form.errors,
                    'address_form': address_form.errors,
                    'soil_data_form': soil_data_form.errors,
                }})
        else:
            field_form = FieldForm(instance=field)
            address_form = AddressForm(instance=field.address)
            soil_data_form = SoilDataForm(instance=field.soil_data)

        context = {
            'field_form': field_form,
            'address_form': address_form,
            'soil_data_form': soil_data_form,
        }

        return render(request, 'app_agrosavvy/update_field.html', context)
    else:
        return redirect('forbidden')












# Brgy officers and farmers pages
#main pages


def bofa_dashboard(request):
    if request.user.is_authenticated and (request.user.is_barangay_officer or request.user.is_farmer):
        fields = Field.objects.filter(owner=request.user)
        return render(request, 'bofa_pages/bofa_dashboard.html', {'fields': fields})
    else:
        return redirect('forbidden') 

def bofa_ai(request):
    return render(request, 'bofa_pages/bofa_ai.html', {})   

def bofa_map(request):
    fields = Field.objects.all()
    fields_json = []

    for field in fields:
        if field.address:
            fields_json.append({
                'name': field.field_name,
                'acres': field.field_acres,
                'latitude': field.address.latitude,
                'longitude': field.address.longitude
            })

    context = {
        'fields_json': json.dumps(fields_json, cls=DjangoJSONEncoder)
    }   
    return render(request, 'bofa_pages/bofa_map.html', context)

def bofa_add_field(request):
    if request.user.is_authenticated and (request.user.is_barangay_officer or request.user.is_farmer):
        if request.method == 'POST':
            field_form = FieldForm(request.POST)
            address_form = AddressForm(request.POST)
            soil_data_form = SoilDataForm(request.POST)
            if field_form.is_valid() and address_form.is_valid and soil_data_form.is_valid:
                address = address_form.save()
                soil_data = soil_data_form.save()
                field = field_form.save(commit=False)
                field.address = address
                field.soil_data = soil_data
                field.owner = request.user
                field.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'errors': {
                    'field_form': field_form.errors,
                    'address_form': address_form.errors,
                    'soil_data_form': soil_data_form.errors,
                }})
        else:
            field_form = FieldForm()
            address_form = AddressForm()
            soil_data_form = SoilDataForm()
        context = {
            'field_form': field_form,
            'address_form': address_form,
            'soil_data_form': soil_data_form,
        }
        return render(request, 'bofa_pages/bofa_add_field.html', context)
    else:
        return redirect('forbidden')

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
    if request.user.is_authenticated and (request.user.is_barangay_officer or request.user.is_farmer):
        return render(request, 'bofa_pages/bofa_settings.html', {})
    else:
        return redirect('forbidden')








#CRUD FOR BOFA
def bofa_delete_field(request, field_id):
    if request.user.is_authenticated and (request.user.is_barangay_officer or request.user.is_farmer):
        field = get_object_or_404(Field, pk=field_id)
        field.delete()
        return redirect('bofa_dashboard')
    else:
        return redirect('forbidden')

def bofa_update_field(request, field_id):
    if request.user.is_authenticated and (request.user.is_barangay_officer or request.user.is_farmer):
        field = get_object_or_404(Field, pk=field_id)

        if field.owner != request.user:      
            return redirect('forbidden')
        
        if request.method == 'POST':
            field_form = FieldForm(request.POST, instance=field)
            address_instance = field.address
            soil_data_instance = field.soil_data

            address_form = AddressForm(request.POST, instance=address_instance)
            soil_data_form = SoilDataForm(request.POST, instance=soil_data_instance)

            if field_form.is_valid() and address_form.is_valid() and soil_data_form.is_valid():
                updated_field = field_form.save(commit=False)
                updated_field.owner = field.owner
                updated_field.save()
                updated_address = address_form.save()
                updated_soil_data = soil_data_form.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'errors': {
                    'field_form': field_form.errors,
                    'address_form': address_form.errors,
                    'soil_data_form': soil_data_form.errors,
                }})
        else:
            field_form = FieldForm(instance=field)
            address_form = AddressForm(instance=field.address)
            soil_data_form = SoilDataForm(instance=field.soil_data)

        context = {
            'field_form': field_form,
            'address_form': address_form,
            'soil_data_form': soil_data_form,
        }
        return render(request, 'bofa_pages/bofa_update_field.html', context)
    else:
        return redirect('forbidden')








#error pages
def forbidden(request):
    return render(request, 'error_pages/forbidden.html', {})