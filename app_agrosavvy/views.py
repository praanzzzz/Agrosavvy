from .models import (
    Field,
    get_weather_data,
    CustomUser,
    PendingUser,
    Crop,
    RoleUser,
    FieldSoilData,
    FieldCropData,
    Chat,
    ChatGroup,
)
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
    PredictionAIForm,
    TipsAIForm,
    ImageAnalysisForm,
)

# others
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.hashers import check_password
import requests
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from easyaudit.models import LoginEvent, CRUDEvent
from django.utils.safestring import mark_safe
import re, base64
from django.shortcuts import render, get_object_or_404, redirect


# AI
from PIL import Image
from io import BytesIO
import os
from openai import OpenAI
client = OpenAI()
OpenAI.api_key = os.environ["OPENAI_API_KEY"]


#  Password:                PRAgab19-5158-794 




# Main pages for da_admin
def dashboard(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
        fields = Field.objects.filter(is_deleted=False)
        crops = Crop.objects.all()
        active_users = CustomUser.objects.filter(active_status=True)
        total_acres = fields.aggregate(Sum("field_acres"))["field_acres__sum"] or 0
        average_acres = fields.aggregate(Avg("field_acres"))["field_acres__avg"] or 0
        average_acres = round(average_acres, 2)
        reviewrating_context = reviewrating(request)

        # pie chart
        labels = []
        data = []
        queryset = FieldCropData.objects.filter(field__is_deleted=False, is_deleted=False
            ).values("crop_planted__crop_type").annotate(
            total_acres=Sum("field__field_acres")
        )
        labels = [entry["crop_planted__crop_type"] for entry in queryset]
        data = [entry["total_acres"] for entry in queryset]


        # line chart
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)
        field_data = (
            Field.objects.filter(
                created_at__range=[start_date, end_date], 
                is_deleted=False
            )
            .extra(select={"month": "strftime('%%Y-%%m', created_at)"})
            .values("month")
            .annotate(count=Count("field_id"))
            .order_by("month")
        )
        labelsfield = [data["month"] for data in field_data]
        datafield = [data["count"] for data in field_data]


        # paginator
        paginator = Paginator(fields, 10)  # 10 fields per page
        page_number = request.GET.get(
            "page"
        )  # Get the current page number from the request
        page_obj = paginator.get_page(
            page_number
        )  # Get the page object for the current page


        context = {
            "fields": fields,
            "crops": crops,
            "field_count": fields.count(),
            "active_user_count": active_users.count(),
            "total_acres": total_acres,
            "average_acres": average_acres,  
            # charts
            "labels": labels,
            "data": data,
            "labelsfield": labelsfield,
            "datafield": datafield,
            # pagination
            "page_obj": page_obj,
        }
        context.update(reviewrating_context)
        return render(request, "app_agrosavvy/dashboard.html", context)
    


    #  for brgy officers
    elif request.user.is_authenticated and request.user.roleuser.roleuser == "brgy_officer":
        user_address = request.user.useraddress.useraddress
        user_barangay = user_address.split(",")[0].strip() 
        fields = Field.objects.filter(
            Q(address__barangay__brgy_name=user_barangay, is_deleted=False)
        )
        total_acres = fields.aggregate(Sum("field_acres"))["field_acres__sum"] or 0
        active_users = CustomUser.objects.filter(
            useraddress__useraddress__startswith=user_barangay,  # Check for users in the same barangay
            active_status=True 
        )
        average_acres = fields.aggregate(Avg("field_acres"))["field_acres__avg"] or 0
        average_acres = round(average_acres, 2)
        reviewrating_context = reviewrating(request)

        # pagination
        paginator = Paginator(fields, 10)  
        page_number = request.GET.get(
            "page"
        )  
        page_obj = paginator.get_page(
            page_number
        ) 
        # pie chart
        # Filter FieldCropData by fields in the same barangay
        queryset = FieldCropData.objects.filter(
            field__is_deleted=False,  # Soft deletion check for Field
            is_deleted=False,  # Soft deletion check for FieldCropData
            field__address__barangay__brgy_name=user_barangay  # Filter fields by the user's barangay
        ).values("crop_planted__crop_type").annotate(
            total_acres=Sum("field__field_acres")  # Sum the acres for each crop type
        )

        # Prepare data for the pie chart
        labels = [entry["crop_planted__crop_type"] for entry in queryset]
        data = [entry["total_acres"] for entry in queryset]


        # line chart
        # Filter Field data for the line chart based on the same barangay
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)
        field_data = (
            Field.objects.filter(
                created_at__range=[start_date, end_date],  # Filter by date range
                is_deleted=False,  # Soft deletion check for Field
                address__barangay__brgy_name=user_barangay  # Filter by user's barangay
            )
            .extra(select={"month": "strftime('%%Y-%%m', created_at)"})  # Group by year and month
            .values("month")
            .annotate(count=Count("field_id"))  # Count the number of fields created per month
            .order_by("month")
        )
        # Prepare data for the line chart
        labelsfield = [data["month"] for data in field_data]
        datafield = [data["count"] for data in field_data]

        brgy_officer_context={
            "fields": fields,
            "field_count": fields.count(),
            "total_acres": total_acres,
            "active_user_count": active_users.count(),
            "average_acres": average_acres,
            "page_obj": page_obj,
            "labels": labels,
            "data": data,
            "labelsfield": labelsfield,
            "datafield": datafield,
        }
        brgy_officer_context.update(reviewrating_context)
        return render(request, "app_agrosavvy/dashboard.html", brgy_officer_context)
    else:
        return redirect("forbidden")



def ask_openai(message):
    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an helpful assistant."},
            {"role": "user", "content": message},
        ]
    )
    answer = response.choices[0].message.content.strip()
    return answer




# chat and creation of chatgroup
def chat(request, group_id=None):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer" ):
        chat_group = None
        if group_id:
            chat_group = get_object_or_404(ChatGroup, id=group_id, user=request.user, is_deleted=False)

        chats = Chat.objects.filter(user=request.user, chat_group=chat_group)

        if request.method == 'POST':
            message = request.POST.get('message', '').strip()

            # If the message is empty, create a new chat group without sending a message
            if not message:
                chat_group = ChatGroup.objects.create(user=request.user)  # Create a new chat group
                return JsonResponse({'group_id': chat_group.id, 'status': 'new_group_created'})

            # If a message is present, send it to the existing or newly created chat group
            if not chat_group:
                chat_group = ChatGroup.objects.create(user=request.user)  # Create a new chat group if none exists

            response = ask_openai(message)
            chat = Chat(user=request.user, chat_group=chat_group, message=message, response=response, created_at=timezone.now())
            chat.save()
            return JsonResponse({'message': message, 'response': response, 'group_id': chat_group.id, 'status': 'message_sent'})
        
        context = {
            "chats": chats,
            "chat_group": chat_group,
            "chat_groups": ChatGroup.objects.filter(user=request.user, is_deleted=False),
        }

        return render(request, 'app_agrosavvy/ai/chatai.html', context)
    else:
        return redirect("forbidden")




def delete_chat_group(request, group_id):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        if request.method == 'POST':
            chat_group = get_object_or_404(ChatGroup, id=group_id, user=request.user)
            
            if chat_group.user == request.user:
                chat_group.delete()
                messages.success(request, 'Chat group deleted successfully.')
            else:
                messages.error(request, 'You do not have permission to delete this chat group.')

        return redirect('chat')
    else:
        return redirect("forbidden")






THIS_MODEL = "gpt-4o-mini"


def encode_image(image_file):
    # with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# Main image analysis view
def image_analysis(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        analysis = None  # Initialize variable to store analysis

        if request.method == 'POST':
            form = ImageAnalysisForm(request.POST, request.FILES)
            if form.is_valid():
                analysis = form.save(commit=False)
                image = form.cleaned_data.get('image')  # Get the uploaded image

                if image:
                    # Encode the uploaded image as base64 (with size limit)
                    base64_image = encode_image(image)

                    # Send the request to the API
                    response = client.chat.completions.create(
                            model=THIS_MODEL,
                            messages=[
                                {
                                    "role": "system",
                                    "content": [
                                        {"type": "text",
                                        "text": "As an AI field analyst, your task is to analyze the attached image. Focus on identifying the health condition of the crops, and suggest possible improvements. Highlight any visible issues (e.g., diseases, pests) or potential growth opportunities based on the image."
                                        }
                                    ],
                                },
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type":"text",
                                            "text": "What is in this image?"
                                        },
                                        {
                                            "type": "image_url",
                                            "image_url": 
                                                {
                                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                                }
                                        }
                                    ]
                                }
                            ],
                            max_tokens=300
                    )

                    if response.choices:
                        ai_output = response.choices[0].message.content
                        # print(f"AI Response: {ai_output}")  # Debug output

                        # Clean and format AI output for display
                        cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', ai_output)  # Bold
                        cleaned_content = re.sub(r'^(#+)\s*(.*?)$', lambda m: f'<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>', cleaned_content, flags=re.MULTILINE)  # Headers
                        cleaned_content = cleaned_content.replace('\n', '<br>')  # Line breaks
                        # Save analysis result and image
                        analysis.image = image
                        analysis.analysis_output = mark_safe(cleaned_content)
                        analysis.save()
                        messages.success(request, "Analysis saved.")
                    else:
                        messages.error(request, "AI did not respond. Please try again later")
                else:
                    messages.error(request, "No Image provided")
            else:
                messages.error(request, 'Form is invalid.')
                # print(form.errors)
        else:
            form = ImageAnalysisForm()
        context = {
            "form": form,
            "analysis_output": analysis.analysis_output if analysis else None,
        }
        return render(request, "app_agrosavvy/ai/analysisai.html", context)
    else:
        return redirect("forbidden")









    

def predictionai(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        prediction = None  

        if request.method == 'POST':
            form = PredictionAIForm(request.POST)
            if form.is_valid():
                prediction = form.save(commit=False)

                selected_field = form.cleaned_data.get('field')

                latest_fieldsoildata = FieldSoilData.objects.filter(
                    field=selected_field, is_deleted=False
                    ).order_by('-record_date').first()
                
                if latest_fieldsoildata:
                    prompt = (f"As an AI field analyst, your task is to provide accurate predictions in the following areas: "
                        f"Crop Yield Prediction, Disease Risk Prediction, and Planting/Harvesting Prediction. "
                        f"Your analysis should be concise and actionable, tailored to the current field conditions.\n\n"
                        
                        f"Field Summary:\n"
                        f"  Role: Agriculturist\n"
                        f"  Task: Provide predictions and recommendations based on the field and soil data.\n\n"
                        
                        f"Field Details:\n"
                        f"  Field Name: {selected_field.field_name}\n"
                        f"  Field Acres: {selected_field.field_acres}\n"
                        f"  Location: {selected_field.address}\n\n"

                        f"Latest Soil Data (recorded on {latest_fieldsoildata.record_date}):\n"
                        f"  Nitrogen (N): {latest_fieldsoildata.nitrogen}\n"
                        f"  Phosphorous (P): {latest_fieldsoildata.phosphorous}\n"
                        f"  Potassium (K): {latest_fieldsoildata.potassium}\n"
                        f"  Soil pH: {latest_fieldsoildata.ph}\n\n"

                        f"Task: Based on the field and soil data provided, predict the following:\n"
                        
                        f"1. **Crop Yield Prediction**: Estimate the expected yield for the crops best suited to these conditions "
                        f"(e.g., Carrots, Potato, Garlic, Eggplant, Tomato, Squash, Bitter Gourd, Cabbage, Onion). "
                        f"Consider soil nutrient levels, pH balance, and field size in your prediction.\n"
                        
                        f"2. **Disease Risk Prediction**: Evaluate the risk of crop diseases based on soil health, environmental factors, and any vulnerabilities "
                        f"you observe. Identify potential disease risks and suggest preventive measures or treatments.\n"
                        
                        f"3. **Planting/Harvesting Prediction**: Provide recommendations on optimal planting and harvesting times for the suggested crops, "
                        f"considering field characteristics, soil conditions, and the region's climate.\n\n"

                        f"Ensure that your predictions and recommendations are practical, easy to understand, and provide clear action points to help the farmer "
                        f"improve yield, manage disease risks, and optimize planting and harvesting schedules."
                    )

                    messages = [
                        {"role": "user", "content": prompt}
                    ]

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=1,
                        max_tokens=500,
                        top_p=1,
                        frequency_penalty= 0,
                        presence_penalty= 0,
                        stream = False ,
                    )

                    if response.choices:
                        response = response.choices[0].message.content
                        # prediction.prediction = response
                        cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', response)  # Bold
                        # Replace headers (adjust for different levels if necessary)
                        cleaned_content = re.sub(r'^(#+)\s*(.*?)$', lambda m: f'<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>', cleaned_content, flags=re.MULTILINE)
                        # Replace newlines with <br>
                        cleaned_content = cleaned_content.replace('\n', '<br>')
                        prediction.prediction = mark_safe(cleaned_content)
                        prediction.save()
                    else:
                        messages.error(request, "AI did not respond. Please try again later.")
                else:
                    messages.error(request, 'No soil data available for the selected field.')
            else:
                messages.error(request, "Form is invalid.")
        else:
            form = PredictionAIForm()
        context = {
            "form":form,
            "prediction":prediction.prediction if form.is_valid() else None,
        }
        return render(request, "app_agrosavvy/ai/predictionai.html", context)
    else:
        return redirect("forbidden")





def tipsai(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        tips = None  
        if request.method == 'POST':
            form = TipsAIForm(request.POST)

            if form.is_valid():
                tips = form.save(commit=False)

                selected_field = form.cleaned_data.get('field')

                latest_fieldsoildata = FieldSoilData.objects.filter(
                    field=selected_field, is_deleted=False
                    ).order_by('-record_date').first()
                
                if latest_fieldsoildata:
                    prompt = (
                        f"As an AI field analyst, your task is to provide detailed and actionable tips specifically on soil health and pest management. "
                        f"Your recommendations should be practical and tailored to the current field conditions.\n\n"
                        
                        f"Field Summary:\n"
                        f"  Role: Agriculturist\n"
                        f"  Task: Provide insights and strategies based on the field and soil data.\n\n"
                        
                        f"Field Details:\n"
                        f"  Field Name: {selected_field.field_name}\n"
                        f"  Field Acres: {selected_field.field_acres}\n"
                        f"  Location: {selected_field.address}\n\n"

                        f"Latest Soil Data (recorded on {latest_fieldsoildata.record_date}):\n"
                        f"  Nitrogen (N): {latest_fieldsoildata.nitrogen}\n"
                        f"  Phosphorous (P): {latest_fieldsoildata.phosphorous}\n"
                        f"  Potassium (K): {latest_fieldsoildata.potassium}\n"
                        f"  Soil pH: {latest_fieldsoildata.ph}\n\n"

                        f"Task: Based on the provided soil data, generate tips on the following:\n"
                        
                        f"1. **Soil Health Tips**: Provide actionable recommendations for improving soil quality based on the nutrient levels and pH balance. "
                        f"Consider practices such as crop rotation, organic amendments, and soil conservation techniques.\n"
                        
                        f"2. **Pest Management Strategies**: Offer effective pest management tips tailored to the crops best suited to these conditions (e.g., Carrots, Potato, Garlic, Eggplant, Tomato, Squash, Bitter Gourd, Cabbage, Onion). "
                        f"Identify common pests in the region and suggest prevention, monitoring, and control measures that are environmentally friendly and sustainable.\n\n"

                        f"Ensure that your tips are easy to understand and provide clear action points to help the farmer enhance soil health and effectively manage pests."
                    )
                    messages = [
                        {"role": "user", "content": prompt}
                    ]

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=1,
                        max_tokens=500,
                        top_p=1,
                        frequency_penalty= 0,
                        presence_penalty= 0,
                        stream = False ,
                    )

                    if response.choices:
                        response = response.choices[0].message.content
                        cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', response)  # Bold
                        # Replace headers (adjust for different levels if necessary)
                        cleaned_content = re.sub(r'^(#+)\s*(.*?)$', lambda m: f'<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>', cleaned_content, flags=re.MULTILINE)
                        # Replace newlines with <br>
                        cleaned_content = cleaned_content.replace('\n', '<br>')
                        tips.tips = mark_safe(cleaned_content)
                        tips.save()
                    else:
                        messages.error(request, "AI did not respond. Please try again later")
                else:
                    messages.error(request, "No soil data available for the selected field.")
            else:
                messages.error(request, "Form is invalid")
        else:
            form = TipsAIForm()
        context = {
            "form":form,
            "tips":tips.tips if form.is_valid() else None,
        }
        return render(request, "app_agrosavvy/ai/tipsai.html", context)
    else:
        return redirect("forbidden")
















def map(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        fields_json = []

        # Fetches all field crop data (wrong)
        # add filters to show only the current crop planted. (not the history or all data)
        # field_crop_data = FieldCropData.objects.select_related("field", "crop_planted")

        field_crop_data = (
            FieldCropData.objects
            .select_related("field", "crop_planted")
            .filter(field__is_deleted=False)
        )


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
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        if request.method == "POST":
            field_form = FieldForm(request.POST)
            address_form = AddressForm(request.POST)
            if field_form.is_valid() and address_form.is_valid():
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
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
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
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        user = get_object_or_404(CustomUser, pk=request.user.pk)
        reviewrating_context = reviewrating(request)

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
        context.update(reviewrating_context)
        return render(request, "app_agrosavvy/settings.html", context)
    else:
        return redirect("forbidden")

#view profile
def view_profile(request):
    if request.user.is_authenticated:
        owner=request.user
        fields = Field.objects.filter(owner = request.user, is_deleted=False)
        user = get_object_or_404(CustomUser, pk=request.user.pk)
        reviewrating_context = reviewrating(request)

        context = {
            "field_count": fields.count(),
        }
        return render(request, "app_agrosavvy/view_profile.html", context)
    else:
        return redirect("forbidden")






def user_management(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
        # fields = Field.objects.filter(is_deleted=False)
        registered_users = CustomUser.objects.exclude(roleuser__roleuser="da_admin").exclude(is_superuser=True)
        pending_users = PendingUser.objects.exclude(roleuser__roleuser="da_admin") #.exclude(roleuser__roleuser="farmer")
        # logs for login and crud events
        login_events = LoginEvent.objects.all().order_by('-datetime')
        crud_events = CRUDEvent.objects.all().order_by('-datetime')


        # Set up the paginator
        paginator = Paginator(registered_users, 4)  
        page_number = request.GET.get("page") 
        registered_users_page_obj = paginator.get_page(page_number)  

        paginator = Paginator(pending_users, 4)
        page_number = request.GET.get("page")
        pending_users_page_obj = paginator.get_page(page_number)

        context = {
            # "fields": fields,
            "login_events": login_events,
            "crud_events": crud_events,
            "registered_users": registered_users,
            "registered_users_page_obj": registered_users_page_obj,
            "pending_users": pending_users,
            "pending_users_page_obj": pending_users_page_obj,
        }

        return render(request, "app_agrosavvy/user_management.html", context)
    


    if request.user.is_authenticated and request.user.roleuser.roleuser == 'brgy_officer':
        # Get the address from the user's user address model
        user_address = request.user.useraddress.useraddress

        # Extract the barangay part (removes the Cebu City)
        user_barangay = user_address.split(",")[0].strip() 
        
        # Assuming CustomUser has a ForeignKey to UserAddress named `useraddress`
        registered_users = CustomUser.objects.filter(
            useraddress__useraddress__startswith=user_barangay,  # Access barangay through the related UserAddress model
            roleuser__roleuser="farmer"  # Show only farmers
        )


        pending_users = PendingUser.objects.filter(
            useraddress__useraddress__startswith=user_barangay,
            roleuser__roleuser="farmer"
        )


        # Filter login events and CRUD events based on the barangay of users involved
        login_events = LoginEvent.objects.filter(
            user__useraddress__useraddress__startswith=user_barangay,
        ).order_by('-datetime')
        
        crud_events = CRUDEvent.objects.filter(
            user__useraddress__useraddress__startswith=user_barangay,
        ).order_by('-datetime')


         # Set up the paginator
        paginator = Paginator(registered_users, 4)  
        page_number = request.GET.get("page") 
        registered_users_page_obj = paginator.get_page(page_number)  

        paginator = Paginator(pending_users, 4)  
        page_number = request.GET.get("page") 
        pending_users_page_obj = paginator.get_page(page_number)  



        brgy_off_context= {
            "registered_users": registered_users,
            "registered_users_page_obj": registered_users_page_obj,
            "pending_users": pending_users,
            "pending_users_page_obj": pending_users_page_obj,
            "login_events": login_events,
            "crud_events":crud_events,
        }
        return render(request, "app_agrosavvy/user_management.html", brgy_off_context)
    else:
            return redirect("forbidden")















# user management for da admin and brgy officer
def admin_deactivate_account(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.user.is_authenticated:
        if request.method == "POST":
            # Deactivate the chosen account
            user.active_status = False
            user.save()
            messages.success(request, "The account is successfully deactivated.")
            return redirect("user_management")
        return render(request, "app_agrosavvy/user_management.html")
    else:
        return redirect("forbidden")


def admin_activate_account(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.user.is_authenticated:
        if request.method == "POST":
            # activate the chosen account
            user.active_status = True
            user.save()
            messages.success(request, "The account is successfully activated.")
            return redirect("user_management")
        return render(request, "app_agrosavvy/user_management.html")
    else:
        return redirect("forbidden")


def admin_approve_user(request, user_id):
    pending_user = get_object_or_404(PendingUser, id=user_id)

    if request.user.is_authenticated:
        if request.method == "POST":
            CustomUser.objects.create(
                username=pending_user.username,
                password=pending_user.password,
                email=pending_user.email,
                firstname=pending_user.firstname,
                lastname=pending_user.lastname,
                date_of_birth=pending_user.date_of_birth,
                gender=pending_user.gender,
                useraddress=pending_user.useraddress,
                roleuser=pending_user.roleuser,
                is_approved=True,
                approved_date=timezone.now(),
                approved_by=request.user,
            )
            pending_user.delete()
            messages.success(
                request, f"User {pending_user.username} has been approved successfully."
            )
            return redirect("user_management")
        return render(
            request,
            "app_agrosavvy/confirm_approve.html",
            {"pending_user": pending_user},
        )
    else:
        return redirect("forbidden")





















# field management
def manage_field(request, field_id):    
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or
        request.user.roleuser.roleuser == "brgy_officer"                                  
        ):
        field = get_object_or_404(
            Field, field_id=field_id
        )  # used for reference or select a specific field
        fieldsoildata = FieldSoilData.objects.filter(
            field=field, is_deleted=False
        )  # displays soil data history of a field
        fieldcropdata = FieldCropData.objects.filter(
            field=field, is_deleted=False
        )  # displays crop data history of a field

        # Create form instance for adding soil data
        asdform = FieldSoilDataForm()  # form for add soil data
        acdform = FieldCropForm()

        # Create a dictionary of forms for each soil and crop data instance
        fsdforms = {
            fsd.soil_id: FieldSoilDataForm(instance=fsd) for fsd in fieldsoildata
        }
        fcdforms = {
            fcd.fieldcrop_id: FieldCropForm(instance=fcd) for fcd in fieldcropdata
        }

        # paginator for fieldsoildata
        paginator = Paginator(fieldsoildata, 3)  # 3 fields per page
        page_number = request.GET.get(
            "page"
        )  # Get the current page number from the request
        fsdpage_obj = paginator.get_page(
            page_number
        )  # Get the page object for the current page

        # paginator for fieldcropdata
        paginator = Paginator(fieldcropdata, 3)
        page_number = request.GET.get("page")
        fcdpage_obj = paginator.get_page(page_number)

        # to make it accessible by the template
        context = {
            "field": field,
            "fieldsoildata": fieldsoildata,
            "fieldcropdata": fieldcropdata,
            "asdform": asdform,
            "acdform": acdform,
            "fsdforms": fsdforms,
            "fcdforms": fcdforms,
            "fsdpage_obj": fsdpage_obj,
            "fcdpage_obj": fcdpage_obj,
        }
        return render(request, "app_agrosavvy/manage_field.html", context)
    else:
        return redirect("forbidden")




def update_field(request, field_id):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or
        request.user.roleuser.roleuser =="brgy_officer"
    ):
        field = get_object_or_404(Field, field_id=field_id)
        if request.method == "POST":
            field_form = FieldForm(request.POST, instance=field)
            address_instance = field.address
            address_form = AddressForm(request.POST, instance=address_instance)
            if field_form.is_valid() and address_form.is_valid():
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
        # GET request (opening the page only)
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


def delete_field(request, field_id):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin"
        or request.user.roleuser.roleuser =="brgy_officer"):
        field = get_object_or_404(Field, pk=field_id)
        field.delete()
        messages.success(request, "Field is successfuly deleted")
        return redirect("dashboard")
    else:
        return redirect("forbidden")



















# Brgy officers and farmers pages
# main pages

def bofa_dashboard(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        owner = request.user
        fields = Field.objects.filter(owner=request.user, is_deleted=False)
        # crops = Crop.objects.all()
        total_acres = (
            Field.objects.filter(owner=request.user, is_deleted=False).aggregate(Sum("field_acres"))[
                "field_acres__sum"
            ]
            or 0
        )
        reviewwrating_context = reviewrating(request)
        

        # pie chart for the crops distribution
        labels = []
        data = []
        queryset = (
            FieldCropData.objects.filter(
                field__owner=owner,
                field__is_deleted=False,
                is_deleted=False
            )
            .values("crop_planted__crop_type")
            .annotate(total_acres=Sum("field__field_acres"))
        )

        # Prepare data for the chart
        labels = [entry["crop_planted__crop_type"] for entry in queryset]
        data = [entry["total_acres"] for entry in queryset]


        # paginator for fieldcropdata
        paginator = Paginator(fields, 3)  # 3 fields per page
        page_number = request.GET.get(
            "page"
        )  # Get the current page number from the request
        bofa_page_obj = paginator.get_page(
            page_number
        )  # Get the page object for the current page



        context = {
            "fields": fields,
            "field_count": fields.count(),
            "total_acres": total_acres,
            "labels": labels,
            "data": data,
            "bofa_page_obj": bofa_page_obj,
        }
        context.update(reviewwrating_context)
        return render(request, "bofa_pages/bofa_dashboard.html", context)
    else:
        return redirect("forbidden")










def bofa_ask_openai(message):
    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an helpful assistant."},
            {"role": "user", "content": message},
        ]
    )
    answer = response.choices[0].message.content.strip()
    return answer



def bofa_chat(request, group_id=None):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        chat_group = None
        if group_id:
            chat_group = get_object_or_404(ChatGroup, id=group_id, user=request.user, is_deleted=False)

        chats = Chat.objects.filter(user=request.user, chat_group=chat_group)

        if request.method == 'POST':
            message = request.POST.get('message', '').strip()

            # If the message is empty, create a new chat group without sending a message
            if not message:
                chat_group = ChatGroup.objects.create(user=request.user)  # Create a new chat group
                return JsonResponse({'group_id': chat_group.id, 'status': 'new_group_created'})

            # If a message is present, send it to the existing or newly created chat group
            if not chat_group:
                chat_group = ChatGroup.objects.create(user=request.user)  # Create a new chat group if none exists

            response = bofa_ask_openai(message)
            chat = Chat(user=request.user, chat_group=chat_group, message=message, response=response, created_at=timezone.now())
            chat.save()
            return JsonResponse({'message': message, 'response': response, 'group_id': chat_group.id, 'status': 'message_sent'})

        context = {
            "chats": chats,
            "chat_group": chat_group,
            "chat_groups": ChatGroup.objects.filter(user=request.user, is_deleted=False),
        }

        return render(request, 'bofa_pages/ai/bofa_chatai.html', context)
    else:
        return redirect('forbidden')



def bofa_delete_chat_group(request, group_id):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        if request.method == 'POST':
            chat_group = get_object_or_404(ChatGroup, id=group_id, user=request.user)
            
            if chat_group.user == request.user:
                chat_group.delete()
                messages.success(request, 'Chat group deleted successfully.')
            else:
                messages.error(request, 'You do not have permission to delete this chat group.')
        return redirect('bofa_chat')
    else:
        return redirect("forbidden")





THIS_MODEL = "gpt-4o-mini"


def bofa_encode_image(image_file):
    # with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


def bofa_image_analysis(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        analysis = None 

        if request.method == 'POST':
            form = ImageAnalysisForm(request.POST, request.FILES)
            if form.is_valid():
                analysis = form.save(commit=False)
                image = form.cleaned_data.get('image') 

                if image:
                    base64_image = bofa_encode_image(image)

                    # Send the request to the API
                    response = client.chat.completions.create(
                            model=THIS_MODEL,
                            messages=[
                                {
                                    "role": "system",
                                    "content": [
                                        {"type": "text",
                                        "text": "As an AI field analyst, your task is to analyze the attached image. Focus on identifying the health condition of the crops, and suggest possible improvements. Highlight any visible issues (e.g., diseases, pests) or potential growth opportunities based on the image."
                                        }
                                    ],
                                },
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type":"text",
                                            "text": "What is in this image?"
                                        },
                                        {
                                            "type": "image_url",
                                            "image_url": 
                                                {
                                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                                }
                                        }
                                    ]
                                }
                            ],
                            max_tokens=300
                    )

                    if response.choices:
                        ai_output = response.choices[0].message.content
                        # print(f"AI Response: {ai_output}") 

                        # Clean and format AI output for display
                        cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', ai_output)  # Bold
                        cleaned_content = re.sub(r'^(#+)\s*(.*?)$', lambda m: f'<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>', cleaned_content, flags=re.MULTILINE)  # Headers
                        cleaned_content = cleaned_content.replace('\n', '<br>')  # Line breaks
                        # Save analysis result and image
                        analysis.image = image
                        analysis.analysis_output = mark_safe(cleaned_content)
                        analysis.save()
                        messages.success(request, 'Analysis saved.')
                    else:
                        messages.error(request, "AI did not respond. Please try again later.")                
                else:
                    messages.error(request, "No image provided")
            else:
                messages.error(request, "Form is invalid.")
                # print(form.errors)
        else:
            form = ImageAnalysisForm()
        context = {
            "form": form,
            "analysis_output": analysis.analysis_output if analysis else None,
        }
        return render(request, "bofa_pages/ai/bofa_analysisai.html", context)
    else:
        return redirect("forbidden")









    

def bofa_predictionai(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        prediction = None  

        if request.method == 'POST':
            form = PredictionAIForm(request.POST)
            if form.is_valid():
                prediction = form.save(commit=False)

                selected_field = form.cleaned_data.get('field')

                latest_fieldsoildata = FieldSoilData.objects.filter(
                    field=selected_field, is_deleted=False
                    ).order_by('-record_date').first()
                
                if latest_fieldsoildata:
                    prompt = (f"As an AI field analyst, your task is to provide accurate predictions in the following areas: "
                        f"Crop Yield Prediction, Disease Risk Prediction, and Planting/Harvesting Prediction. "
                        f"Your analysis should be concise and actionable, tailored to the current field conditions.\n\n"
                        
                        f"Field Summary:\n"
                        f"  Role: Agriculturist\n"
                        f"  Task: Provide predictions and recommendations based on the field and soil data.\n\n"
                        
                        f"Field Details:\n"
                        f"  Field Name: {selected_field.field_name}\n"
                        f"  Field Acres: {selected_field.field_acres}\n"
                        f"  Location: {selected_field.address}\n\n"

                        f"Latest Soil Data (recorded on {latest_fieldsoildata.record_date}):\n"
                        f"  Nitrogen (N): {latest_fieldsoildata.nitrogen}\n"
                        f"  Phosphorous (P): {latest_fieldsoildata.phosphorous}\n"
                        f"  Potassium (K): {latest_fieldsoildata.potassium}\n"
                        f"  Soil pH: {latest_fieldsoildata.ph}\n\n"

                        f"Task: Based on the field and soil data provided, predict the following:\n"
                        
                        f"1. **Crop Yield Prediction**: Estimate the expected yield for the crops best suited to these conditions "
                        f"(e.g., Carrots, Potato, Garlic, Eggplant, Tomato, Squash, Bitter Gourd, Cabbage, Onion). "
                        f"Consider soil nutrient levels, pH balance, and field size in your prediction.\n"
                        
                        f"2. **Disease Risk Prediction**: Evaluate the risk of crop diseases based on soil health, environmental factors, and any vulnerabilities "
                        f"you observe. Identify potential disease risks and suggest preventive measures or treatments.\n"
                        
                        f"3. **Planting/Harvesting Prediction**: Provide recommendations on optimal planting and harvesting times for the suggested crops, "
                        f"considering field characteristics, soil conditions, and the region's climate.\n\n"

                        f"Ensure that your predictions and recommendations are practical, easy to understand, and provide clear action points to help the farmer "
                        f"improve yield, manage disease risks, and optimize planting and harvesting schedules."
                    )

                    messages = [
                        {"role": "user", "content": prompt}
                    ]

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=1,
                        max_tokens=500,
                        top_p=1,
                        frequency_penalty= 0,
                        presence_penalty= 0,
                        stream = False ,
                    )

                    if response.choices:
                        response = response.choices[0].message.content
                        # prediction.prediction = response
                        cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', response)  # Bold
                        # Replace headers (adjust for different levels if necessary)
                        cleaned_content = re.sub(r'^(#+)\s*(.*?)$', lambda m: f'<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>', cleaned_content, flags=re.MULTILINE)
                        # Replace newlines with <br>
                        cleaned_content = cleaned_content.replace('\n', '<br>')
                        prediction.prediction = mark_safe(cleaned_content)
                        prediction.save()
                        messages.success(request, "Output saved.")
                    else:
                        messages.error(request, "AI did not respond. Please try again later.")
                else:
                    messages.error(request, "No soil data available for the selected field.")
            else:
                messages.error(request, "Form is invalid.")
        else:
            form = PredictionAIForm()

        context = {
            "form":form,
            "prediction":prediction.prediction if form.is_valid() else None,
        }
        return render(request, "bofa_pages/ai/bofa_predictionai.html", context)
    else:
        return redirect("forbidden")





def bofa_tipsai(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        tips = None  
        if request.method == 'POST':
            form = TipsAIForm(request.POST)

            if form.is_valid():
                tips = form.save(commit=False)

                selected_field = form.cleaned_data.get('field')

                latest_fieldsoildata = FieldSoilData.objects.filter(
                    field=selected_field, is_deleted=False
                    ).order_by('-record_date').first()
                
                if latest_fieldsoildata:
                    prompt = (
                        f"As an AI field analyst, your task is to provide detailed and actionable tips specifically on soil health and pest management. "
                        f"Your recommendations should be practical and tailored to the current field conditions.\n\n"
                        
                        f"Field Summary:\n"
                        f"  Role: Agriculturist\n"
                        f"  Task: Provide insights and strategies based on the field and soil data.\n\n"
                        
                        f"Field Details:\n"
                        f"  Field Name: {selected_field.field_name}\n"
                        f"  Field Acres: {selected_field.field_acres}\n"
                        f"  Location: {selected_field.address}\n\n"

                        f"Latest Soil Data (recorded on {latest_fieldsoildata.record_date}):\n"
                        f"  Nitrogen (N): {latest_fieldsoildata.nitrogen}\n"
                        f"  Phosphorous (P): {latest_fieldsoildata.phosphorous}\n"
                        f"  Potassium (K): {latest_fieldsoildata.potassium}\n"
                        f"  Soil pH: {latest_fieldsoildata.ph}\n\n"

                        f"Task: Based on the provided soil data, generate tips on the following:\n"
                        
                        f"1. **Soil Health Tips**: Provide actionable recommendations for improving soil quality based on the nutrient levels and pH balance. "
                        f"Consider practices such as crop rotation, organic amendments, and soil conservation techniques.\n"
                        
                        f"2. **Pest Management Strategies**: Offer effective pest management tips tailored to the crops best suited to these conditions (e.g., Carrots, Potato, Garlic, Eggplant, Tomato, Squash, Bitter Gourd, Cabbage, Onion). "
                        f"Identify common pests in the region and suggest prevention, monitoring, and control measures that are environmentally friendly and sustainable.\n\n"

                        f"Ensure that your tips are easy to understand and provide clear action points to help the farmer enhance soil health and effectively manage pests."
                    )


                    messages = [
                        {"role": "user", "content": prompt}
                    ]

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=1,
                        max_tokens=500,
                        top_p=1,
                        frequency_penalty= 0,
                        presence_penalty= 0,
                        stream = False ,
                    )

                    if response.choices:
                        response = response.choices[0].message.content
                        cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', response)  # Bold
                        # Replace headers (adjust for different levels if necessary)
                        cleaned_content = re.sub(r'^(#+)\s*(.*?)$', lambda m: f'<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>', cleaned_content, flags=re.MULTILINE)
                        # Replace newlines with <br>
                        cleaned_content = cleaned_content.replace('\n', '<br>')
                        tips.tips = mark_safe(cleaned_content)
                        tips.save()
                        messages.successs(request, "Tip saved.")
                    else:
                        messages.error(request, "AI did not respond. Please try again later.")
                else:
                    messages.error(request, "No soil data available for the selected field.")
            else:
                messages.error(request, "Form is invalid.")
        else:
            form = TipsAIForm()

        context = {
            "form":form,
            "tips":tips.tips if form.is_valid() else None,
        }
        return render(request, "bofa_pages/ai/bofa_tipsai.html", context)
    else:
        return redirect("forbidden")







# no auth yet and filters
def bofa_map(request):
    fields_json = []

    # Fetch all field crop data
    # field_crop_data = FieldCropData.objects.select_related("field", "crop_planted")
    field_crop_data = (
        FieldCropData.objects
        .select_related("field", "crop_planted")
        .filter(field__is_deleted=False)
    )


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
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        if request.method == "POST":
            field_form = FieldForm(request.POST)
            address_form = AddressForm(request.POST)
            if field_form.is_valid() and address_form.is_valid(): #check here
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
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        user = get_object_or_404(CustomUser, pk=request.user.pk)
        reviewrating_context = reviewrating(request)

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
        context.update(reviewrating_context)
        return render(request, "bofa_pages/bofa_settings.html", context)
    else:
        return redirect("forbidden")














# bofa manage fields/ farms
def bofa_manage_field(request, field_id):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        field = get_object_or_404(Field, field_id=field_id)
        fieldsoildata = FieldSoilData.objects.filter(field=field, is_deleted=False)
        fieldcropdata = FieldCropData.objects.filter(field=field, is_deleted=False)

        asdform = FieldSoilDataForm()
        acdform = FieldCropForm()

        # Create a dictionary of forms for each soil and crop data instance
        fsdforms = {
            fsd.soil_id: FieldSoilDataForm(instance=fsd) for fsd in fieldsoildata
        }
        fcdforms = {
            fcd.fieldcrop_id: FieldCropForm(instance=fcd) for fcd in fieldcropdata
        }

        # paginator for fieldsoildata
        paginator = Paginator(fieldsoildata, 2)  # 3 fields per page
        page_number = request.GET.get(
            "page"
        )  # Get the current page number from the request
        fsdpage_obj = paginator.get_page(
            page_number
        )  # Get the page object for the current page

        # paginator for fieldcropdata
        paginator = Paginator(fieldcropdata, 2)
        page_number = request.GET.get("page")
        fcdpage_obj = paginator.get_page(page_number)

        context = {
            "field": field,
            "fieldsoildata": fieldsoildata,
            "fieldcropdata": fieldcropdata,
            "asdform": asdform,
            "acdform": acdform,
            "fsdforms": fsdforms,
            "fcdforms": fcdforms,
            "fsdpage_obj": fsdpage_obj,
            "fcdpage_obj": fcdpage_obj,
        }
        return render(request, "bofa_pages/bofa_manage_field.html", context)
    else:
        return redirect("forbidden")


def bofa_update_field(request, field_id):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        field = get_object_or_404(Field, pk=field_id)

        if field.owner != request.user:
            return redirect("forbidden")

        if request.method == "POST":
            field_form = FieldForm(request.POST, instance=field)
            address_instance = field.address
            address_form = AddressForm(request.POST, instance=address_instance)
            if field_form.is_valid() and address_form.is_valid():
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


def bofa_delete_field(request, field_id):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        field = get_object_or_404(Field, pk=field_id)

        if field.owner != request.user:
            return redirect("forbidden")

        field.delete()
        return redirect("bofa_dashboard")
    else:
        return redirect("forbidden")





















# callable functions (used in da admin and bofa)
def reviewrating(request):
    if request.method == "POST":
        rform = ReviewratingForm(request.POST)
        if rform.is_valid():
            rrform = rform.save(commit=False)
            rrform.rate_date = now()
            rrform.reviewer = request.user
            rrform.save()
            messages.success(request, "Thank you for submitting feedback.")
            if request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer":
                return redirect("dashboard")
            elif request.user.roleuser.roleuser == "farmer":
                return redirect("bofa_dashboard")
        else:
            print("Please correct the errors below.")
    else:
        rform = ReviewratingForm()

    return {"rform": rform}


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
                if request.user.roleuser.roleuser == "da_admin" or  request.user.roleuser.roleuser == "brgy_officer":
                    return redirect(
                        reverse("manage_field", kwargs={"field_id": field_id})
                    )
                elif request.user.roleuser.roleuser == "farmer":
                    return redirect(
                        reverse("bofa_manage_field", kwargs={"field_id": field_id})
                    )
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
        if request.method == "POST":
            acdform = FieldCropForm(request.POST)
            if acdform.is_valid():
                crop_data = acdform.save(commit=False)
                crop_data.field = field
                crop_data.save()
                messages.success(request, "Crop data successfully saved.")
                if request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer":
                    return redirect(
                        reverse("manage_field", kwargs={"field_id": field_id})
                    )
                elif request.user.roleuser.roleuser == "farmer":
                    return redirect(
                        reverse("bofa_manage_field", kwargs={"field_id": field_id})
                    )
            else:
                messages.error(request, "Form invalid")
        else:
            acdform = FieldCropForm()
        
        context={"acdform": acdform, "field": field}
        return context
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
                if request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer":
                    return redirect(
                        reverse("manage_field", kwargs={"field_id": field_id})
                    )
                elif request.user.roleuser.roleuser =="farmer":
                    return redirect(
                        reverse("bofa_manage_field", kwargs={"field_id": field_id})
                    )
            else:
                messages.error(request, "Error updating soil data.")
        else:
            # Show the current values in the form
            fsdform = FieldSoilDataForm(instance=soil)
        return {"fsdform": fsdform, "soil": soil}
    else:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect("forbidden")


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
                if request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer":
                    return redirect(
                        reverse("manage_field", kwargs={"field_id": field_id})
                    )
                elif request.user.roleuser.roleuser == "farmer":
                    return redirect(
                        reverse("bofa_manage_field", kwargs={"field_id": field_id})
                    )
            else:
                messages.error(request, "Error updating crop data.")
        else:
            # Show the current values in the form
            fcdform = FieldCropForm(instance=crop)
        return {"fcdform": fcdform, "crop": crop}

    else:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect("forbidden")


def delete_soil_data(request, soil_id):
    soil_data = get_object_or_404(FieldSoilData, soil_id=soil_id)
    field_id = soil_data.field.field_id
    if request.user.is_authenticated:
        if request.method == "POST":
            soil_data.delete()
            messages.success(request, "Soil data deleted successfully.")
            if request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer":
                return redirect(reverse("manage_field", kwargs={"field_id": field_id}))
            elif request.user.roleuser.roleuser =="farmer":
                return redirect(
                    reverse("bofa_manage_field", kwargs={"field_id": field_id})
                )
        else:
            messages.error(request, "Invalid request.")

    else:
        return redirect("forbidden")


def delete_crop_data(request, fieldcrop_id):
    crop_data = get_object_or_404(FieldCropData, fieldcrop_id=fieldcrop_id)
    field_id = crop_data.field.field_id
    if request.user.is_authenticated:
        if request.method == "POST":
            crop_data.delete()
            messages.success(request, "Crop data deleted successfully.")
            if request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer":
                return redirect(reverse("manage_field", kwargs={"field_id": field_id}))
            elif request.user.roleuser.roleuser =="farmer":
                return redirect(
                    reverse("bofa_manage_field", kwargs={"field_id": field_id})
                )
        else:
            messages.error(request, "Invalid request.")

    else:
        return redirect("forbidden")





















# authentication related codes
def landing_page(request):
    return render(request, "auth_pages/landing_page.html", {})


def register_da_admin(request):
    if request.method == "POST":
        form = PendingUserForm(request.POST)
        if form.is_valid():
            pending_user = form.save(commit=False)
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
    
    context = {
        "form": form,
    }
    return render(request, "auth_pages/register_da_admin.html", context)



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
    return render(
        request,
        "auth_pages/register_barangay_officer.html",
        {
            "form": form,
        },
    )


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
    return render(
        request,
        "auth_pages/register_farmer.html",
        {"form": form,
        },
    )


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
                    if user.roleuser.roleuser == "da_admin" or  user.roleuser.roleuser == "brgy_officer":
                        login(request, user)
                        messages.success(request, "Account logged in successfully")
                        return redirect("dashboard")
                    elif (
                        user.roleuser.roleuser == "farmer"
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
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
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
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
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
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
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
    return render(request, "error_pages/forbidden.html")
