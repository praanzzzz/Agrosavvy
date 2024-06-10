from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Field, Crop
from .forms import FieldForm
from django.contrib.messages import success 



#PRAgab19-5158-794


#auth imports
from .forms import SignUpForm, LoginForm    
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


#auth views pages
def landing_page(request):
    return render(request, 'app_agrosavvy/landing_page.html', {})

def register(request):
    msg = None
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            msg = 'user created'
            #login later
            return redirect('my_login')
        else:
            msg = 'form is not valid'
    else:
        form = SignUpForm()
    return render(request,'auth_pages/register.html', {'form': form, 'msg': msg})



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
            elif user is not None and user.is_barangay_officer or user.is_farmer:
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
            fields_json.append({    
                'name': field.field_name,
                'latitude': field.latitude,
                'longitude': field.longitude
            })

        context = {
            'fields_json': json.dumps(fields_json)
        }   
        return render(request, 'app_agrosavvy/map.html', context)
    else:
        return redirect('forbidden')


def add_field(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        if request.method == 'POST':
            form = FieldForm(request.POST)
            if form.is_valid():
                field = form.save(commit=False)
                field.owner = request.user
                field.save()
                #redirect to bofa_dashboard if bofa,logic
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'errors': form.errors})
        else:
            form = FieldForm()
            return render(request, 'app_agrosavvy/add_field.html', {'form': form})
    else:
        return redirect('forbidden')


def weather(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        return render(request, 'app_agrosavvy/weather.html', {})
    else:
        return redirect('forbidden')


def settings(request):
    if request.user.is_authenticated and request.user.is_da_admin:
        return render(request, 'app_agrosavvy/settings.html', {})
    else:
        return redirect('forbidden')




#CRUD fields view


def delete_field(request, field_id):
    if request.user.is_authenticated and request.user.is_da_admin:
        field = get_object_or_404(Field, pk=field_id)
        field.delete()
        return redirect('dashboard')
    else:
        return redirect('forbidden')



def update_field(request, field_id):
    if request.user.is_authenticated and request.user.is_da_admin:
        # Get the field object or return 404 if not found
        field = get_object_or_404(Field, pk=field_id)

        if request.method == 'POST':
            # Create a form instance with POST data and instance set to the field object
            form = FieldForm(request.POST, instance=field)
            if form.is_valid():
                # Save the form but don't commit to database yet
                updated_field = form.save(commit=False)
                # Ensure the owner field is set to the current owner
                updated_field.owner = field.owner
                # Now save the updated field object to the database
                updated_field.save()
                return redirect('dashboard')  # Redirect to dashboard after successful update
        else:
            # Create a form instance with the field data pre-filled
            form = FieldForm(instance=field)

        # Render the template with the form and field data
        return render(request, 'app_agrosavvy/update_field.html', {'form': form, 'field_id': field.field_id})
    else:
        return redirect('forbidden')












# Brgy officers and farmers pages
#main pages


def bofa_dashboard(request):
    if request.user.is_authenticated and (request.user.is_barangay_officer or request.user.is_farmer):
        fields = Field.objects.filter(owner=request.user)
        return render(request, 'bofa_pages/bofa_dashboard.html', {'fields': fields})
    else:
        # Handle unauthorized access (e.g., redirect to a login page or an error page)
        return redirect('forbidden')  # Adjust the redirect as necessary


def bofa_ai(request):
    return render(request, 'bofa_pages/bofa_ai.html', {})


def bofa_map(request):
    fields = Field.objects.all()
    fields_json = []

    for field in fields:
        fields_json.append({
            'name': field.field_name,
            'latitude': field.latitude,
            'longitude': field.longitude
        })

    context = {
        'fields_json': json.dumps(fields_json)
    }   
    return render(request, 'bofa_pages/bofa_map.html', context)



def bofa_add_field(request):
    if request.user.is_authenticated and (request.user.is_barangay_officer or request.user.is_farmer):
        if request.method == 'POST':
            form = FieldForm(request.POST)
            if form.is_valid():
                field = form.save(commit=False)
                field.owner = request.user
                field.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'errors': form.errors})
        else:
            form = FieldForm()
            return render(request, 'bofa_pages/bofa_add_field.html', {'form': form})
    else:
        # Handle unauthorized access, for example by redirecting to an error page or login page
        return redirect('forbidden')  # Adjust the redirect as necessary

def bofa_weather(request):
    return render(request, 'bofa_pages/bofa_weather.html', {})


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
        return redirect('bofa_pages/bofa_dashboard')
    else:
        return redirect('forbidden')




def bofa_update_field(request, field_id):
    if request.user.is_authenticated and (request.user.is_barangay_officer or request.user.is_farmer):
        field = get_object_or_404(Field, pk=field_id)

        if field.owner != request.user:
          
            return redirect('forbidden')

        if request.method == 'POST':
            # Create a form instance with POST data and instance set to the field object
            form = FieldForm(request.POST, instance=field)
            if form.is_valid():
                # Save the form but don't commit to database yet
                updated_field = form.save(commit=False)
                # Ensure the owner field is set to the current owner
                updated_field.owner = field.owner
                # Now save the updated field object to the database
                updated_field.save()
                return redirect('bofa_dashboard')  # Redirect to dashboard after successful update
        else:
            # Create a form instance with the field data pre-filled
            form = FieldForm(instance=field)

        # Render the template with the form and field data
        return render(request, 'bofa_pages/bofa_update_field.html', {'form': form, 'field_id': field.field_id})
    else:
         # Handle unauthorized access, for example by redirecting to an error page or login page
        return redirect('forbidden')  # Adjust the redirect as necessary





#error pages
def forbidden(request):
    return render(request, 'app_agrosavvy/forbidden.html', {})