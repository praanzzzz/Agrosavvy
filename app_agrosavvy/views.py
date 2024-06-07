from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Field, Crop
from .forms import FieldForm
from django.contrib.messages import success


# Main pages
def dashboard(request):
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



#pede ra tangtangon
def add_field(request):
    if request.method == 'POST':
        form = FieldForm(request.POST)
        if form.is_valid():
            # Save the form data to create a new Field object
            field = form.save(commit=False)
            # Perform any additional processing if needed
            # For example, you can set the user associated with the field
            # field.user = request.user
            field.save()
            #return a notif or I dunno for success notif then go to dashboard
            return JsonResponse({'status': 'success'})
        else:
            # If form is invalid, return error message
            return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        # If request method is not POST, render the form
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

