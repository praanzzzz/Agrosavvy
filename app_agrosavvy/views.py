from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Field, Crop
from .forms import FieldForm
from django.contrib.messages import success 



#auth imports
from .forms import SignUpForm, LoginForm
from django.contrib.auth import authenticate, login, logout


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
    return render(request,'app_agrosavvy/register.html', {'form': form, 'msg': msg})



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
                return redirect('dashboard')
            else:
                msg= 'invalid credentials'
        else:
            msg = 'error validating form'
    return render(request, 'app_agrosavvy/my_login.html', {'form': form, 'msg': msg})


def my_logout(request):
    logout(request)
    return redirect('my_login')





# Main pages
def dashboard(request):
    if request.user.is_authenticated:
    # and request.user.is_da_admin:
        fields = Field.objects.all()
        return render(request, 'app_agrosavvy/dashboard.html', {'fields': fields})

def ai(request):
    return render(request, 'app_agrosavvy/ai.html', {})


def map(request):
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

def add_field(request):
    if request.method == 'POST':
        form = FieldForm(request.POST)
        if form.is_valid():
            field = form.save(commit=False)
            # Perform any additional processing if needed
            # For example, you can set the user associated with the field
            # field.user = request.user
            field.save()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        form = FieldForm()
        return render(request, 'app_agrosavvy/add_field.html', {'form': form})
    
def weather(request):
    return render(request, 'app_agrosavvy/weather.html', {})

def settings(request):
    return render(request, 'app_agrosavvy/settings.html', {})








#other specifics 
#CRUD fields view


def delete_field(request, field_id):
    field = get_object_or_404(Field, pk=field_id)
    field.delete()
    return redirect('dashboard')


def update_field(request, field_id):
    # Get the field object or return 404 if not found
    field = get_object_or_404(Field, pk=field_id)
    if request.method == 'POST':
        # Create a form instance with POST data and instance set to the field object
        form = FieldForm(request.POST, instance=field)
        if form.is_valid():
            # Save the updated field object
            form.save()
            success(request, 'Field updated successfully!')
            return redirect('dashboard')  # Redirect to dashboard after successful update
    else:
        # Create a form instance with the field data pre-filled
        form = FieldForm(instance=field)

    # Render the template with the form and field data
    return render(request, 'app_agrosavvy/update_field.html', {'form': form, 'field.field_id': field.field_id})

