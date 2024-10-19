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
    Notification,
    Barangay,
    ImageAnalysis,
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
    CreateNotificationForm,
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
from django.db.models import Sum, Count, Avg, Max, Subquery, OuterRef, Q
from django.utils import timezone
from datetime import timedelta
from easyaudit.models import LoginEvent, CRUDEvent
from django.utils.safestring import mark_safe
import re, base64


# AI
from PIL import Image
from io import BytesIO
import os
from openai import OpenAI
client = OpenAI()
OpenAI.api_key = os.environ["OPENAI_API_KEY"]


#  Password:                PRAgab19-5158-794 





# Main pages for da_admin and brgy officers
def dashboard(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
        # Search, Filter, and Sort
        search_query = request.GET.get('search', '')
        filter_type = request.GET.get('filter', '')
        sort_by = request.GET.get('sort', '')

        fields = Field.objects.filter(is_deleted=False)

        if search_query:
            fields = fields.filter(
                Q(field_name__icontains=search_query) |
                Q(owner__username__icontains=search_query) |
                Q(address__barangay__brgy_name__icontains=search_query)
            )

        if filter_type:
            fields = fields.filter(owner__roleuser__roleuser=filter_type)

        if sort_by == 'name':
            fields = fields.order_by('field_name')
        elif sort_by == 'acres':
            fields = fields.order_by('field_acres')


        # retrieve data
        crops = Crop.objects.all()
        active_users = CustomUser.objects.filter(active_status=True)
        total_acres = fields.aggregate(Sum("field_acres"))["field_acres__sum"] or 0
        average_acres = fields.aggregate(Avg("field_acres"))["field_acres__avg"] or 0
        average_acres = round(average_acres, 2)
        reviewrating_context = reviewrating(request)

        # Pie Chart Data
        labels = []
        data = []

        # queryset = FieldCropData.objects.filter(field__is_deleted=False, is_deleted=False
        #     ).values("crop_planted__crop_type").annotate(
        #     total_acres=Sum("field__field_acres")
        # )

        # latest field crop data per field only
        queryset =  FieldCropData.objects.filter(
                planting_date=Subquery(
                    FieldCropData.objects.filter(
                        field=OuterRef('field'),
                        field__is_deleted=False,
                        is_deleted=False
                    ).order_by('-planting_date').values('planting_date')[:1]
                )
            ).values("crop_planted__crop_type").annotate(
                total_acres=Sum("field__field_acres")
            )


        labels = [entry["crop_planted__crop_type"] for entry in queryset]
        data = [entry["total_acres"] for entry in queryset]

        # Line Chart Data
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

        # Pagination
        paginator = Paginator(fields, 5)  
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "notifications": notifications,
            "notifications_unread_count": notifications_unread_count,
            "fields": fields,
            "crops": crops,
            "field_count": fields.count(),
            "active_user_count": active_users.count(),
            "total_acres": total_acres,
            "average_acres": average_acres,
            # Charts
            "labels": labels,
            "data": data,
            "labelsfield": labelsfield,
            "datafield": datafield,
            # Pagination
            "page_obj": page_obj,
            # Search, Filter, and Sort Context
            "search_query": search_query,
            "filter_type": filter_type,
            "sort_by": sort_by,
        }
        context.update(reviewrating_context)
        return render(request, "app_agrosavvy/dashboard.html", context)
    


    #  for brgy officers
    elif request.user.is_authenticated and request.user.roleuser.roleuser == "brgy_officer":
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
        # Search, Filter, and Sort
        search_query = request.GET.get('search', '')
        filter_type = request.GET.get('filter', '')
        sort_by = request.GET.get('sort', '')

        # Retrieve user's barangay information
        user_address = request.user.useraddress.useraddress
        user_barangay = user_address.split(",")[0].strip()

        # Initial queryset to include fields from the user's barangays
        fields = Field.objects.filter(
            Q(address__barangay__brgy_name=user_barangay, is_deleted=False)
        )

        # Apply search filter if a search query is provided
        if search_query:
            fields = fields.filter(
                Q(field_name__icontains=search_query) |
                Q(owner__username__icontains=search_query) |
                Q(address__barangay__brgy_name__icontains=search_query)
            )

        # Apply additional filtering if a filter type is provided
        if filter_type:
            fields = fields.filter(owner__roleuser__roleuser=filter_type)

        # Apply sorting if a sort option is provided
        if sort_by == 'name':
            fields = fields.order_by('field_name')
        elif sort_by == 'acres':
            fields = fields.order_by('field_acres')


        total_acres = fields.aggregate(Sum("field_acres"))["field_acres__sum"] or 0
        active_users = CustomUser.objects.filter(
            useraddress__useraddress__startswith=user_barangay,  # Check for users in the same barangay
            active_status=True 
        )
        average_acres = fields.aggregate(Avg("field_acres"))["field_acres__avg"] or 0
        average_acres = round(average_acres, 2)


        reviewrating_context = reviewrating(request)

        # pie chart
        # Filter FieldCropData by fields in the same barangay
        # queryset = FieldCropData.objects.filter(
        #     field__is_deleted=False, 
        #     is_deleted=False, 
        #     field__address__barangay__brgy_name=user_barangay  
        # ).values("crop_planted__crop_type").annotate(
        #     total_acres=Sum("field__field_acres") 
        # )

        # pie chart
        # retrieves the latest field crop data for each crop type from non-deleted fields
        #  in a specified barangay, aggregating the total acres for each crop type.
        queryset = FieldCropData.objects.filter(
            field__is_deleted=False, 
            is_deleted=False,
            field__address__barangay__brgy_name=user_barangay
        ).filter(
            planting_date=Subquery(
                FieldCropData.objects.filter(
                    field=OuterRef('field'),
                    field__is_deleted=False,
                    is_deleted=False,
                    field__address__barangay__brgy_name=user_barangay  # Ensure the same barangay filter is applied
                ).order_by('-planting_date').values('planting_date')[:1]
            )
        ).values("crop_planted__crop_type").annotate(
            total_acres=Sum("field__field_acres")
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

        # print(labelsfield)
        # print(datafield)



        # pagination
        paginator = Paginator(fields, 5)  
        page_number = request.GET.get(
            "page"
        )  
        page_obj = paginator.get_page(
            page_number
        )

        brgy_officer_context={
            "notifications": notifications,
            "notifications_unread_count": notifications_unread_count,
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
            # Search, Filter, and Sort Context
            "search_query": search_query,
            "filter_type": filter_type,
            "sort_by": sort_by,
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
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
        fields_json = []

        # Subquery to get the latest crop data for each field
        latest_crop = FieldCropData.objects.filter(
            field=OuterRef('field_id'),
            is_deleted=False
        ).order_by('-planting_date')

        # Fetch fields with their latest crop data
        fields = Field.objects.filter(is_deleted=False).annotate(
            latest_crop_id=Subquery(latest_crop.values('fieldcrop_id')[:1]),
            latest_crop_type=Subquery(latest_crop.values('crop_planted__crop_type')[:1])
        )

        for field in fields:
            if field.address:
                fields_json.append({
                    "name": field.field_name,
                    "acres": field.field_acres,
                    "latitude": field.address.latitude,
                    "longitude": field.address.longitude,
                    "crop": field.latest_crop_type or "No crop data",
                })

        context = {
            "notifications": notifications,
            "notifications_unread_count": notifications_unread_count,
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
            if field_form.is_valid() and address_form.is_valid():
                address = address_form.save()
                field = field_form.save(commit=False)
                field.address = address
                field.owner = request.user
                field.save()
                messages.success(request, "Field saved successfully.")
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
    

    elif request.user.is_authenticated and request.user.roleuser.roleuser == "brgy_officer": 
        if request.method == "POST":
            # Retrieve user's barangay information
            bo_user_address = request.user.useraddress.useraddress
            bo_user_barangay = bo_user_address.split(",")[0].strip()


            field_form = FieldForm(request.POST)
            address_form = AddressForm(request.POST)
            if field_form.is_valid() and address_form.is_valid():
                address = address_form.save()
                field = field_form.save(commit=False)
                field.address = address
                field.owner = request.user
                field.save()
                messages.success(request, "Field saved successfully.")
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
            # Retrieve user's barangay information
            bo_user_address = request.user.useraddress.useraddress
            bo_user_barangay = bo_user_address.split(",")[0].strip()
            field_form = FieldForm()
            address_form = AddressForm()
        context = {
            "field_form": field_form,
            "address_form": address_form,
            "bo_user_barangay": bo_user_barangay,
        }
        return render(request, "app_agrosavvy/brgy_add_field.html", context)
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
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
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

        context = {"updateprofileform": updateprofileform,
                    "notifications":  notifications,
                    "notifications_unread_count": notifications_unread_count,
                    }
        return render(request, "app_agrosavvy/settings.html", context)
    else:
        return redirect("forbidden")




def view_profile(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser=='da_admin' or request.user.roleuser.roleuser=='brgy_officer'):
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
        owner=request.user
        fields = Field.objects.filter(owner = request.user, is_deleted=False)
        user = get_object_or_404(CustomUser, pk=request.user.pk)

        context = {
            "field_count": fields.count(),
            "notifications": notifications,
            "notifications_unread_count": notifications_unread_count,
        }
        return render(request, "app_agrosavvy/view_profile.html", context)
    else:
        return redirect("forbidden")











def user_management(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser in ["da_admin", "brgy_officer"]:
        user_role = request.user.roleuser.roleuser
        user_barangay = request.user.useraddress.useraddress.split(',')[0].strip() if user_role == "brgy_officer" else None

        # Registered Users
        registered_search_query = request.GET.get('registered_search', '')
        registered_filter_type = request.GET.get('registered_filter', '')
        registered_sort_by = request.GET.get('registered_sort', '')

        if user_role == "da_admin":
            registered_users = CustomUser.objects.exclude(roleuser__roleuser="da_admin").exclude(is_superuser=True)
        else:  # brgy_officer
            registered_users = CustomUser.objects.filter(
                useraddress__useraddress__startswith=user_barangay,
                roleuser__roleuser="farmer"
            )

        if registered_search_query:
            registered_users = registered_users.filter(
                Q(username__icontains=registered_search_query) |
                Q(email__icontains=registered_search_query) |
                Q(firstname__icontains=registered_search_query) |
                Q(lastname__icontains=registered_search_query)
            )

        if registered_filter_type and user_role == "da_admin":
            registered_users = registered_users.filter(roleuser__roleuser=registered_filter_type)

        if registered_sort_by:
            registered_users = registered_users.order_by(registered_sort_by)

        # Pending Users
        pending_search_query = request.GET.get('pending_search', '')
        pending_filter_type = request.GET.get('pending_filter', '')
        pending_sort_by = request.GET.get('pending_sort', '')

        if user_role == "da_admin":
            pending_users = PendingUser.objects.exclude(roleuser__roleuser="da_admin").filter(is_disapproved=False)
        else:  # brgy_officer
            pending_users = PendingUser.objects.filter(
                useraddress__useraddress__startswith=user_barangay,
                roleuser__roleuser="farmer", is_disapproved=False   
            )

        if pending_search_query:
            pending_users = pending_users.filter(
                Q(username__icontains=pending_search_query) |
                Q(email__icontains=pending_search_query) |
                Q(firstname__icontains=pending_search_query) |
                Q(lastname__icontains=pending_search_query)
            )

        if pending_filter_type and user_role == "da_admin":
            pending_users = pending_users.filter(roleuser__roleuser=pending_filter_type, is_disapproved=False)

        if pending_sort_by:
            pending_users = pending_users.order_by(pending_sort_by)

        # Pagination for registered users
        registered_paginator = Paginator(registered_users, 4)
        registered_page_number = request.GET.get("registered_page")
        registered_users_page_obj = registered_paginator.get_page(registered_page_number)

        # Pagination for pending users
        pending_paginator = Paginator(pending_users, 4)
        pending_page_number = request.GET.get("pending_page")
        pending_users_page_obj = pending_paginator.get_page(pending_page_number)

        # Login and CRUD events
        if user_role == "da_admin":
            login_events = LoginEvent.objects.all().order_by('-datetime')
            crud_events = CRUDEvent.objects.all().order_by('-datetime')
        else:  # brgy_officer
            login_events = LoginEvent.objects.filter(
                user__useraddress__useraddress__startswith=user_barangay,
            ).order_by('-datetime')
            crud_events = CRUDEvent.objects.filter(
                user__useraddress__useraddress__startswith=user_barangay,
            ).order_by('-datetime')

        context = {
            "registered_users": registered_users,
            "registered_users_page_obj": registered_users_page_obj,
            "pending_users": pending_users,
            "pending_users_page_obj": pending_users_page_obj,
            "login_events": login_events,
            "crud_events": crud_events,
            "registered_search_query": registered_search_query,
            "registered_filter_type": registered_filter_type,
            "registered_sort_by": registered_sort_by,
            "pending_search_query": pending_search_query,
            "pending_filter_type": pending_filter_type,
            "pending_sort_by": pending_sort_by,
            "user_role": user_role,
        }

        return render(request, "app_agrosavvy/user_management.html", context)
    else:
        return redirect("forbidden")







# Create notification based on the selected option
def create_notification(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
        if request.method == 'POST':
            form = CreateNotificationForm(request.POST)
            if form.is_valid():
                notification_type = form.cleaned_data['notification_type']
                subject = form.cleaned_data['subject']
                message = form.cleaned_data['message']

                # Handle notification based on the selected type
                if notification_type == 'all':
                    users = CustomUser.objects.all()

                elif notification_type == 'single_user':
                    user_receiver = form.cleaned_data['user_receiver']
                    users = [user_receiver]

                elif notification_type == 'role':
                    role = form.cleaned_data['role']
                    users = CustomUser.objects.filter(roleuser=role)

                elif notification_type == 'useraddress':
                    useraddress = form.cleaned_data['useraddress']
                    users = CustomUser.objects.filter(useraddress=useraddress)

                # Create notifications for the selected users
                for user in users:
                    Notification.objects.create(
                        user_sender=request.user,
                        user_receiver=user,
                        subject=subject,
                        message=message
                    )

                messages.success(request, "Notifications successfully sent.")
                return redirect('create_notification')
            else:
                messages.error(request, "Form is invalid.")
        else:
            form = CreateNotificationForm()
        context = {
            "form": form,
            "notifications": notifications,
            "notifications_unread_count": notifications_unread_count,
        }
        return render(request, "app_agrosavvy/create_notification.html", context)
    return redirect("forbidden")




def mark_notifications_as_read(request):
    # Mark all unread notifications as read for the current user
    Notification.objects.filter(user_receiver = request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})



def view_notification(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()

        paginator = Paginator(notifications, 4)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            'notifications': notifications,
            'page_obj': page_obj,
            'notifications_unread_count': notifications_unread_count,  # Pass unread notification count
        }
        return render(request, 'app_agrosavvy/view_notification.html', context)
    else:
        return redirect("forbidden")
    



def bofa_view_notification(request):
    print("bofa_view_notification called")
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()

        paginator = Paginator(notifications, 4)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            'notifications': notifications,
            'page_obj': page_obj,
            'notifications_unread_count': notifications_unread_count,  
        }
        return render(request, 'bofa_pages/bofa_view_notification.html', context)
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


def admin_disapprove_user(request, user_id):
    pending_user = get_object_or_404(PendingUser, id=user_id)

    if request.user.is_authenticated:
        if request.method == "POST":
            pending_user.is_disapproved = True
            pending_user.save()
            messages.success(request, "The pending user is disapproved.")
            return redirect("user_management")
        return render(request, "app_agrosavvy/user_management.html")
    else:
        return redirect("forbidden")
    



def admin_approve_user(request, user_id):
    pending_user = get_object_or_404(PendingUser, id=user_id)

    if request.user.is_authenticated:
        if request.method == "POST":
            CustomUser.objects.create(
                official_user_id= pending_user.official_user_id,
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
        field = get_object_or_404(Field, field_id=field_id)

        # Soil Data
        soil_filter_type = request.GET.get('soil_filter', '')
        soil_sort_by = request.GET.get('soil_sort', '')

        fieldsoildata = FieldSoilData.objects.filter(field=field, is_deleted=False)

        if soil_filter_type:
            if soil_filter_type == 'acidic':
                fieldsoildata = fieldsoildata.filter(ph__lt=7)
            elif soil_filter_type == 'neutral':
                fieldsoildata = fieldsoildata.filter(ph=7)
            elif soil_filter_type == 'alkaline':
                fieldsoildata = fieldsoildata.filter(ph__gt=7)

        if soil_sort_by:
            if soil_sort_by == 'date_asc':
                fieldsoildata = fieldsoildata.order_by('record_date')
            elif soil_sort_by == 'date_desc':
                fieldsoildata = fieldsoildata.order_by('-record_date')
            elif soil_sort_by == 'ph_asc':
                fieldsoildata = fieldsoildata.order_by('ph')
            elif soil_sort_by == 'ph_desc':
                fieldsoildata = fieldsoildata.order_by('-ph')

        # Crop Data
        crop_filter_type = request.GET.get('crop_filter', '')
        crop_sort_by = request.GET.get('crop_sort', '')

        fieldcropdata = FieldCropData.objects.filter(field=field, is_deleted=False)

        if crop_filter_type:
            fieldcropdata = fieldcropdata.filter(crop_planted_id=crop_filter_type)

        if crop_sort_by:
            if crop_sort_by == 'planting_asc':
                fieldcropdata = fieldcropdata.order_by('planting_date')
            elif crop_sort_by == 'planting_desc':
                fieldcropdata = fieldcropdata.order_by('-planting_date')
            # elif crop_sort_by == 'harvest_asc':
            #     fieldcropdata = fieldcropdata.order_by('harvest_date')
            # elif crop_sort_by == 'harvest_desc':
            #     fieldcropdata = fieldcropdata.order_by('-harvest_date')

        # Create form instance for adding soil data
        asdform = FieldSoilDataForm()
        acdform = FieldCropForm()

        # Create a dictionary of forms for each soil and crop data instance
        fsdforms = {fsd.soil_id: FieldSoilDataForm(instance=fsd) for fsd in fieldsoildata}
        fcdforms = {fcd.fieldcrop_id: FieldCropForm(instance=fcd) for fcd in fieldcropdata}

        # Pagination for fieldsoildata
        soil_paginator = Paginator(fieldsoildata, 3)
        soil_page_number = request.GET.get("soil_page")
        fsdpage_obj = soil_paginator.get_page(soil_page_number)

        # Pagination for fieldcropdata
        crop_paginator = Paginator(fieldcropdata, 3)
        crop_page_number = request.GET.get("crop_page")
        fcdpage_obj = crop_paginator.get_page(crop_page_number)

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
            "soil_filter_type": soil_filter_type,
            "soil_sort_by": soil_sort_by,
            "crop_filter_type": crop_filter_type,
            "crop_sort_by": crop_sort_by,
            "crops": Crop.objects.all(),
        }
        return render(request, "app_agrosavvy/manage_field.html", context)
    else:
        return redirect("forbidden")




def update_field(request, field_id):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
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
                messages.success(request, "Field updated successfully.")
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
    

    if request.user.is_authenticated and request.user.roleuser.roleuser == "brgy_officer":
        field = get_object_or_404(Field, field_id=field_id)
        if request.method == "POST":
            # Retrieve user's barangay information
            bo_user_address = request.user.useraddress.useraddress
            bo_user_barangay = bo_user_address.split(",")[0].strip()
            field_form = FieldForm(request.POST, instance=field)
            address_instance = field.address
            address_form = AddressForm(request.POST, instance=address_instance)
            if field_form.is_valid() and address_form.is_valid():
                updated_field = field_form.save(commit=False)
                updated_field.owner = field.owner
                updated_field.save()
                updated_address = address_form.save()
                messages.success(request, "Field updated successfully.")
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
            # Retrieve user's barangay information
            bo_user_address = request.user.useraddress.useraddress
            bo_user_barangay = bo_user_address.split(",")[0].strip()
            field_form = FieldForm(instance=field)
            address_form = AddressForm(instance=field.address)
        context = {
            "field_form": field_form,
            "address_form": address_form,
            "bo_user_barangay": bo_user_barangay,
        }
        return render(request, "app_agrosavvy/brgy_update_field.html", context)
    

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



















# farmers pages
# main pages

def bofa_dashboard(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
        owner = request.user
        fields = Field.objects.filter(owner=request.user, is_deleted=False)

         # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            fields = fields.filter(
                Q(field_name__icontains=search_query) |
                Q(address__barangay__brgy_name__icontains=search_query)
            )

        # Filter functionality
        filter_type = request.GET.get('filter', '')
        if filter_type:
            fields = fields.filter(address__barangay__brgy_name=filter_type)

        # Sort functionality
        sort_by = request.GET.get('sort', '')
        if sort_by == 'name':
            fields = fields.order_by('field_name')
        elif sort_by == 'acres':
            fields = fields.order_by('field_acres')
        elif sort_by == 'location':
            fields = fields.order_by('address__barangay__brgy_name')



        total_acres = (
            Field.objects.filter(owner=request.user, is_deleted=False).aggregate(Sum("field_acres"))[
                "field_acres__sum"
            ]
            or 0
        )
        reviewwrating_context = reviewrating(request)

        numberOfRecommendations = (
            ImageAnalysis.objects.filter(owner=request.user)
        )

        numberOfChatGroups = (
            ChatGroup.objects.filter(user=request.user, is_deleted=False)
        )
        

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
        paginator = Paginator(fields, 5)  # 5 fields per page
        page_number = request.GET.get(
            "page"
        )  # Get the current page number from the request
        bofa_page_obj = paginator.get_page(
            page_number
        )  # Get the page object for the current page



        context = {
            "notifications": notifications,
            "notifications_unread_count": notifications_unread_count,
            "fields": fields,
            "field_count": fields.count(),
            "total_acres": total_acres,
            "labels": labels,
            "data": data,
            "bofa_page_obj": bofa_page_obj,
            # search
            "filter_type": filter_type,
            "search_query": search_query,
            "sort_by": sort_by,
            "barangays": Barangay.objects.all(),
            "numberOfRecommendations": numberOfRecommendations.count(),
            "numberOfChatGroups" : numberOfChatGroups.count(),
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
                        analysis.owner = request.user
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







def bofa_map(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
        fields_json = []

        # Subquery to get the latest crop data for each field
        latest_crop = FieldCropData.objects.filter(
            field=OuterRef('field_id'),
            is_deleted=False
        ).order_by('-planting_date')

        # Fetch fields with their latest crop data
        fields = Field.objects.filter(is_deleted=False).annotate(
            latest_crop_id=Subquery(latest_crop.values('fieldcrop_id')[:1]),
            latest_crop_type=Subquery(latest_crop.values('crop_planted__crop_type')[:1])
        )

        for field in fields:
            if field.address:
                fields_json.append({
                    "name": field.field_name,
                    "acres": field.field_acres,
                    "latitude": field.address.latitude,
                    "longitude": field.address.longitude,
                    "crop": field.latest_crop_type or "No crop data",
                })

        context = {
            "fields_json": json.dumps(fields_json, cls=DjangoJSONEncoder),
            "crops": Crop.objects.all(),
            "notifications": notifications,
            "notifications_unread_count": notifications_unread_count,
        }
        return render(request, "bofa_pages/bofa_map.html", context)
    else:
        return redirect("forbidden")




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
                messages.success(request, "Field saved successfully.")
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
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
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

        context = {"updateprofileform": updateprofileform, 
                   "notifications": notifications,
                   'notifications_unread_count': notifications_unread_count,
                   }
        return render(request, "bofa_pages/bofa_settings.html", context)
    else:
        return redirect("forbidden")





def bofa_view_profile(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser =='farmer':
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
        owner=request.user
        fields = Field.objects.filter(owner = request.user, is_deleted=False)
        user = get_object_or_404(CustomUser, pk=request.user.pk)

        context = {
            "field_count": fields.count(),
            "notifications": notifications,
            'notifications_unread_count': notifications_unread_count,
        }
        return render(request, "bofa_pages/bofa_view_profile.html", context)
    else:
        return redirect("forbidden")





# bofa manage fields/ farms
def bofa_manage_field(request, field_id):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        field = get_object_or_404(Field, field_id=field_id)

        # Soil Data
        soil_filter_type = request.GET.get('soil_filter', '')
        soil_sort_by = request.GET.get('soil_sort', '')

        fieldsoildata = FieldSoilData.objects.filter(field=field, is_deleted=False)

        if soil_filter_type:
            if soil_filter_type == 'acidic':
                fieldsoildata = fieldsoildata.filter(ph__lt=7)
            elif soil_filter_type == 'neutral':
                fieldsoildata = fieldsoildata.filter(ph=7)
            elif soil_filter_type == 'alkaline':
                fieldsoildata = fieldsoildata.filter(ph__gt=7)

        if soil_sort_by:
            if soil_sort_by == 'date_asc':
                fieldsoildata = fieldsoildata.order_by('record_date')
            elif soil_sort_by == 'date_desc':
                fieldsoildata = fieldsoildata.order_by('-record_date')
            elif soil_sort_by == 'ph_asc':
                fieldsoildata = fieldsoildata.order_by('ph')
            elif soil_sort_by == 'ph_desc':
                fieldsoildata = fieldsoildata.order_by('-ph')

        # Crop Data
        crop_filter_type = request.GET.get('crop_filter', '')
        crop_sort_by = request.GET.get('crop_sort', '')

        fieldcropdata = FieldCropData.objects.filter(field=field, is_deleted=False)

        if crop_filter_type:
            fieldcropdata = fieldcropdata.filter(crop_planted_id=crop_filter_type)

        if crop_sort_by:
            if crop_sort_by == 'planting_asc':
                fieldcropdata = fieldcropdata.order_by('planting_date')
            elif crop_sort_by == 'planting_desc':
                fieldcropdata = fieldcropdata.order_by('-planting_date')
            # elif crop_sort_by == 'harvest_asc':
            #     fieldcropdata = fieldcropdata.order_by('harvest_date')
            # elif crop_sort_by == 'harvest_desc':
            #     fieldcropdata = fieldcropdata.order_by('-harvest_date')

        # Create form instance for adding soil data
        asdform = FieldSoilDataForm()
        acdform = FieldCropForm()

        # Create a dictionary of forms for each soil and crop data instance
        fsdforms = {fsd.soil_id: FieldSoilDataForm(instance=fsd) for fsd in fieldsoildata}
        fcdforms = {fcd.fieldcrop_id: FieldCropForm(instance=fcd) for fcd in fieldcropdata}

        # Pagination for fieldsoildata
        soil_paginator = Paginator(fieldsoildata, 3)
        soil_page_number = request.GET.get("soil_page")
        fsdpage_obj = soil_paginator.get_page(soil_page_number)

        # Pagination for fieldcropdata
        crop_paginator = Paginator(fieldcropdata, 3)
        crop_page_number = request.GET.get("crop_page")
        fcdpage_obj = crop_paginator.get_page(crop_page_number)

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
            "soil_filter_type": soil_filter_type,
            "soil_sort_by": soil_sort_by,
            "crop_filter_type": crop_filter_type,
            "crop_sort_by": crop_sort_by,
            "crops": Crop.objects.all(),
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
                messages.success(request, "Field updated successfully.")
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


def get_nutrient_data(request):
    field_id = request.GET.get('field_id')
    nutrient = request.GET.get('nutrient')
    
    data = FieldSoilData.objects.filter(field_id=field_id).order_by('record_date')
    
    labels = [d.record_date.strftime('%Y-%m-%d') for d in data]
    values = [getattr(d, nutrient) for d in data]
    
    return JsonResponse({'labels': labels, 'values': values})





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
            # if user exist in the custom user
            if user is not None:
                if user.is_subscribed:
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
                    messages.error(request, "Organization is unsubscribed.")
            else:
                messages.error(
                    request,
                    "Invalid username or password",
                )
        else:
            messages.error(request, "Error validating form")
    return render(request, "auth_pages/my_login.html", {"form": form})





# def my_login(request):
#     form = LoginForm(request.POST or None)
#     if request.method == "POST":
#         if form.is_valid():
#             official_user_id = form.cleaned_data.get("official_user_id")
#             password = form.cleaned_data.get("password")

#             # Check if the user is in the PendingUser table
#             try:
#                 pending_user = PendingUser.objects.get(official_user_id=official_user_id)
#                 if check_password(password, pending_user.password):
#                     messages.info(
#                         request, "Your registration request is awaiting approval."
#                     )
#                     return render(request, "auth_pages/my_login.html", {"form": form})
#                 else:
#                     messages.error(request, "Invalid username or password")
#                     return render(request, "auth_pages/my_login.html", {"form": form})
#             except PendingUser.DoesNotExist:
#                 pass

#             user = authenticate(official_user_id=official_user_id, password=password)

#             if user is not None:
#                 if user.active_status:
#                     if user.roleuser.roleuser == "da_admin" or  user.roleuser.roleuser == "brgy_officer":
#                         login(request, user)
#                         messages.success(request, "Account logged in successfully")
#                         return redirect("dashboard")
#                     elif (
#                         user.roleuser.roleuser == "farmer"
#                     ):
#                         login(request, user)
#                         messages.success(request, "Account logged in successfully")
#                         return redirect("bofa_dashboard")
#                     else:
#                         messages.error(request, "Invalid credentials")
#                 else:
#                     messages.error(request, "Account is deactivated")
#                     # redirect to a page that handles account reactivation request
#             else:
#                 messages.error(
#                     request,
#                     "Invalid username or password",
#                 )
#         else:
#             messages.error(request, "Error validating form")
#     return render(request, "auth_pages/my_login.html", {"form": form})


def my_logout(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Account logged out successfully")
        return redirect("my_login")
    else:
        return redirect("forbidden")


def password_change(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
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

        context = {"passwordchangeform": passwordchangeform,
                   "notifications": notifications,
                   "notifications_unread_count": notifications_unread_count,
                   }
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




def billing(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        return render(request, 'app_agrosavvy/settings_section/billing.html')
    else:
        return redirect("forbidden")

def bofa_billing(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer" :
        return render(request, 'bofa_pages/bofa_settings_section/bofa_billing.html')
    else:
        return redirect("forbidden")





def bofa_password_change(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
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

        context = {"passwordchangeform": passwordchangeform,
                   "notifications": notifications,
                   "notifications_unread_count": notifications_unread_count,
                   }
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







