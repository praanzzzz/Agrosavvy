from .models import (
    Field,
    get_weather_data,
    get_weather_data_with_minutely_hourly,
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
    SoilDataSFM,
    Address,
    FailedLoginAttempt,
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
    ImageAnalysisForm,
    CreateNotificationForm,
)

# others
# from django_ratelimit.decorators import ratelimit
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
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Avg, Max, Subquery, OuterRef, Q
from django.utils import timezone
from datetime import timedelta
from easyaudit.models import LoginEvent, CRUDEvent
from django.utils.safestring import mark_safe
import re, base64
from django.conf import settings as django_settings
from django.core.serializers import serialize
from django.core.mail import send_mail
from django.views.decorators.cache import cache_control
from django.db.models.functions import TruncMonth
from openai import OpenAI, APIConnectionError, OpenAIError
OpenAI.api_key = django_settings.OPENAI_API_KEY
client = OpenAI()





# Main pages for da_admin and brgy officers
@cache_control(no_cache=True, must_revalidate=True, no_store=True)   # prevents cache on data-sensitive pages
def dashboard(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
        # Search, Filter, and Sort functions for list of farms table
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
        active_users = CustomUser.objects.filter(active_status=True).exclude(roleuser__roleuser="super_admin")
        total_acres_wo_rounds = fields.aggregate(Sum("field_acres"))["field_acres__sum"] or 0
        total_acres = round(total_acres_wo_rounds, 2)
        average_acres = fields.aggregate(Avg("field_acres"))["field_acres__avg"] or 0
        average_acres = round(average_acres, 2)
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()


        # Pie Chart
        labels = []
        data = []
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



        # Line Chart
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)
        field_data = (
            Field.objects.filter(
                created_at__range=[start_date, end_date], 
                is_deleted=False
            )
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('field_id'))
            .order_by('month')
        )
        labelsfield = [data['month'].strftime('%Y-%m') for data in field_data]
        datafield = [data['count'] for data in field_data]



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
            "labels": labels,
            "data": data,
            "labelsfield": labelsfield,
            "datafield": datafield,
            "page_obj": page_obj,
            "search_query": search_query,
            "filter_type": filter_type,
            "sort_by": sort_by,
        }
        return render(request, "app_agrosavvy/dashboard.html", context)
    


    #  for brgy officers
    elif request.user.is_authenticated and request.user.roleuser.roleuser == "brgy_officer":
        # Search, Filter, and Sort
        search_query = request.GET.get('search', '')
        filter_type = request.GET.get('filter', '')
        sort_by = request.GET.get('sort', '')

        # retrieve users barangay and query the field that belongs to the same barangay on user's barangay
        user_address = request.user.useraddress.useraddress
        user_barangay = user_address.split(",")[0].strip()
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
        if filter_type:
            fields = fields.filter(owner__roleuser__roleuser=filter_type)
        if sort_by == 'name':
            fields = fields.order_by('field_name')
        elif sort_by == 'acres':
            fields = fields.order_by('field_acres')

        # retrieve data
        total_acres_wo_rounds = fields.aggregate(Sum("field_acres"))["field_acres__sum"] or 0
        total_acres = round(total_acres_wo_rounds, 2)
        active_users = CustomUser.objects.filter(
            useraddress__useraddress__startswith=user_barangay,  # Check for users in the same barangay
            active_status=True, 
        ).exclude(roleuser__roleuser="da_admin").exclude(roleuser__roleuser="super_admin")
        average_acres = fields.aggregate(Avg("field_acres"))["field_acres__avg"] or 0
        average_acres = round(average_acres, 2)
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()

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
                    field__address__barangay__brgy_name=user_barangay 
                ).order_by('-planting_date').values('planting_date')[:1]
            )
        ).values("crop_planted__crop_type").annotate(
            total_acres=Sum("field__field_acres")
        )
        labels = [entry["crop_planted__crop_type"] for entry in queryset]
        data = [entry["total_acres"] for entry in queryset]


        # line chart
        # Filter Field data for the line chart based on the same barangay
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)
        field_data = (
            Field.objects.filter(
                created_at__range=[start_date, end_date], 
                is_deleted=False,
                address__barangay__brgy_name=user_barangay
            )
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('field_id'))
            .order_by('month')
        )
        labelsfield = [data['month'].strftime('%Y-%m') for data in field_data]
        datafield = [data['count'] for data in field_data]

        # pagination
        paginator = Paginator(fields, 5)  
        page_number = request.GET.get("page")  
        page_obj = paginator.get_page(page_number)

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
            "search_query": search_query,
            "filter_type": filter_type,
            "sort_by": sort_by,
        }
        return render(request, "app_agrosavvy/dashboard.html", brgy_officer_context)
    else:
        return redirect("forbidden")





















THIS_MODEL = "gpt-4o-mini"

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
# @ratelimit(key='ip', rate='5/m', method='POST', block=True)
def chat(request, group_id=None):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        chat_group = None

        if group_id:
            chat_group = get_object_or_404(ChatGroup, id=group_id, user=request.user, is_deleted=False)
        chats = Chat.objects.filter(user=request.user, chat_group=chat_group)

        if request.method == 'POST':
            message = request.POST.get('message', '').strip()
            if not message:
                chat_group = ChatGroup.objects.create(user=request.user)
                return JsonResponse({'group_id': chat_group.id, 'status': 'new_group_created'})

            if not chat_group:
                chat_group = ChatGroup.objects.create(user=request.user)

            if not chat_group.title:
                title = chatgroup_title_generator(message)
                chat_group.title = title
                chat_group.save()

            previous_messages = chats.order_by('-created_at')[:10]
            # conversation_history = "\n".join([f"User: {chat.message}\nAI Context: {chat.ai_context}\nAI: {chat.response}" for chat in previous_messages])
            conversation_history = "\n".join([f"\n\nUser: {chat.message}\nAI response: {chat.response}" for chat in previous_messages])
            full_conversation = conversation_history + f"\nUser: {message}\nAI:"


            # barangay memory
            # Extract previously mentioned barangay or sitio if any
            if any("barangay" in message or "brgy" in message for message in conversation_history.split("\n")):
                barangay = extract_brgy_name_conv_history(conversation_history)
            else:
                barangay = extract_brgy_name(message)

            # If the user explicitly mentions for a different barangay, override the barangay value
            if "barangay" in message or "brgy" in message:
                barangay = extract_brgy_name(message)
            elif barangay is not None:
                pass 
            else:
                barangay = None
            


            intent = classify_intent(message)
            ai_context = ""

          
            # USING OBJECT TECHNIQUE
            if intent == "ask_help":
                if barangay is not None:
                    soil_data_entries = SoilDataSFM.objects.filter(barangay__iexact=barangay)
                    total_area = soil_data_entries.aggregate(total_area=Sum('total_area'))['total_area']
                    crops = soil_data_entries.values_list('crops_planted', flat=True)
                    ai_context = ""

                    # Keep track of processed sitios
                    processed_sitios = set()

                    # Loop through all sitios in the barangay
                    for soil_data in soil_data_entries:
                        if soil_data.sitio not in processed_sitios:
                            ai_context += (
                                f"In {barangay}, Sitio {soil_data.sitio}: "
                                f"Nitrogen level is {soil_data.get_nitrogen_level_display()}, "
                                f"Phosphorus level is {soil_data.get_phosphorus_level_display()}, "
                                f"and Potassium level is {soil_data.get_potassium_level_display()}. "
                                f"pH level is {soil_data.get_ph_level_display()}, "
                                f"indicating that it is {'acidic' if soil_data.ph_level in ['L', 'ML', 'MH'] else 'alkaline'}. "
                                f"Crops planted in Sitio {soil_data.sitio}: {soil_data.crops_planted}. "
                                f"These nutrient levels may be ideal for crops that thrive in {'low' if soil_data.nitrogen_level == 'L' else 'moderate' if soil_data.nitrogen_level in ['ML', 'MH'] else 'high'} nutrient environments.\n"
                            )
                            # Mark this sitio as processed
                            processed_sitios.add(soil_data.sitio)

                    # Whole Barangay data
                    ai_context += (
                        f"\nThe total farming area within {barangay} spans {total_area} hectares.\n"
                        f"Crops currently planted across all sitios in {barangay} include: {', '.join(set(crops))}."
                    )
                    # If there's no data for the barangay
                    if not soil_data_entries:
                        ai_context = "Soil data is not available for this barangay. You may check the spelling of barangay and make sure it's correct."
                else:
                    ai_context = "Say this: 'Please provide the barangay name in a full sentence.'"



            elif intent == "conversational":
                ai_context = "Ask me questions about agriculture specially in Cebu City."


            # openweathermap api
            elif intent == "weather":
                location = extract_location_with_openai(message)
                print(location)
                if location is not None:
                    weather_data = get_weather_data(location)
                    if weather_data:
                        ai_context = f"weather forecast for {location}:\n{weather_data}."
                    else:
                        ai_context = f"Sorry, no weather data available in that area. Try searching for a city."
                else:
                    ai_context = "Say this: 'Can you please specify the location for the weather forecast? For example: What is the weather for location X?'"


            # handling if no intent is processed
            else:
                ai_context = "I'm sorry, but I couldn't process your request right now. Please try again later."
    
            full_conversation_with_context = full_conversation + f"\nAI Context: {ai_context}"
            openai_response = ask_openai(full_conversation_with_context)

            cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', openai_response)
            cleaned_content = re.sub(r'^(#+)\s*(.*?)$', lambda m: f'<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>', cleaned_content, flags=re.MULTILINE)
            cleaned_content = cleaned_content.replace('\n', '<br>')
            final_response = cleaned_content


            # # debugging
            # print("Processed Intent:" , intent)
            # if barangay:
            #     print("barangay:" + barangay)
            # else:
            #     print("brgy not found")
            # print("Full Conversation with Context to OpenAI:", full_conversation_with_context)
            
    

            chat = Chat(
                user=request.user, 
                chat_group=chat_group, 
                message=message, 
                response=final_response, 
                ai_context=ai_context,
                created_at=timezone.now(),
                intent=intent,
            )
            chat.save()

            return JsonResponse({
                'message': message, 
                'response': final_response, 
                'group_id': chat_group.id, 
                'status': 'message_sent',
                'title': chat_group.title,
            })
        reviewrating_context = reviewrating(request)
        context = {
            "chats": chats,
            "chat_group": chat_group,
            "chat_groups": ChatGroup.objects.filter(user=request.user, is_deleted=False),
        }
        context.update(reviewrating_context)
        return render(request, 'app_agrosavvy/ai/chatai.html', context)
    else:
        return redirect("forbidden")





@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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









@cache_control(no_cache=True, must_revalidate=True, no_store=True)
# @ratelimit(key='ip', rate='5/m', method='POST', block=True)
def image_analysis(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        analysis = None
        history = ImageAnalysis.objects.filter(owner=request.user, is_deleted=False).order_by('-created_at')[:5] #increase to 10
        history_json = json.loads(serialize('json', history))
        reviewrating_context = reviewrating(request)

        if request.method == 'POST':
            form = ImageAnalysisForm(request.POST, request.FILES)
            if form.is_valid():
                analysis = form.save(commit=False)
                image = form.cleaned_data.get('image')  # Get the uploaded image

                if image:
                    # Encode the uploaded image as base64 (with size limit)
                    base64_image = encode_image(image)

                    try:
                        # Send the request to the API
                        response = client.chat.completions.create(
                                model=THIS_MODEL,
                                messages=[
                                    {
                                        "role": "system",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": "As an AI field analyst, analyze the attached image to assess crop health conditions. Identify any visible issues such as diseases or pests, and suggest actionable improvements for optimal crop growth. Provide the description in a more professional way and describe it well. Do not provide analysis on images that is unrelated to agriculture, crops, plants. This model is unable to answer questions. "
                                            }
                                        ]
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
                                max_tokens=500
                        )

                        if response.choices:
                            ai_output = response.choices[0].message.content
                            # print(f"AI Response: {ai_output}")  # Debug output

                            # Clean and format AI output for display
                            cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', ai_output)  # Bold
                            cleaned_content = re.sub(r'^(#+)\s*(.*?)$', lambda m: f'<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>', cleaned_content, flags=re.MULTILINE)  # Headers
                            cleaned_content = cleaned_content.replace('\n', '<br>')  # Line breaks
                            cleaned_content = translate_to_bisaya(cleaned_content)
                            # Save analysis result and image
                            analysis.image = image
                            analysis.analysis_output = mark_safe(cleaned_content)
                            analysis.owner = request.user
                            analysis.title = image_analysis_title_generator(cleaned_content)
                            analysis.save()
                            # messages.success(request, "Analysis saved.")
                            return redirect("image_analysis")
                        else:
                            messages.error(request, "AI did not respond. Please try again later")

                    # the reason we can use backend try catch handling and not the fetch api catch is that
                    # the page refreshes when output or no output. unlike in the chat ai page where its dynamic
                    except APIConnectionError as e:         
                        messages.error(request, "There was a connection issue with the AI service. Please try again later.")
                    except OpenAIError as e:
                        messages.error(request, "An error occurred with the AI service. Please try again later.")
                    except Exception as e:
                        messages.error(request, "An unexpected error occurred. Please try again later.")


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
            "history": history,
            "history_json": json.dumps(history_json),
        }
        context.update(reviewrating_context)
        return render(request, "app_agrosavvy/ai/analysisai.html", context)
    else:
        return redirect("forbidden")




@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
def delete_image_analysis(request, pk):
    if request.user.is_authenticated and request.user.roleuser.roleuser in ["da_admin", "brgy_officer"]:
        if request.method == "POST":
            analysis = get_object_or_404(ImageAnalysis, pk=pk, owner=request.user)
            if analysis.owner == request.user:
                analysis.delete()
                messages.success(request, "Image analysis successfully deleted.")
                return redirect("image_analysis")
            else:
                messages.error(request, "You do not have permission to delete this analysis.")
        return render(request, "app_agrosavvy/ai/analysisai.html")
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
                    "address": f"{field.address.barangay}, {field.address.city_municipality}" if field.address else "No address",
                    "latitude": field.address.latitude,
                    "longitude": field.address.longitude,
                    "crop": field.latest_crop_type or "No crop data",
                    "owner_name": field.owner.get_full_name() if field.owner else "No owner",
                    "owner_contact": str(field.owner.contact_number) if field.owner and field.owner.contact_number else "No contact info",
                })

        context = {
            "notifications": notifications,
            "notifications_unread_count": notifications_unread_count,
            "fields_json": json.dumps(fields_json, cls=DjangoJSONEncoder),
            "crops": Crop.objects.all(),
            "MAPBOX_API_KEY" : django_settings.MAPBOX_API_KEY,
        }
        return render(request, "app_agrosavvy/map.html", context)
    else:
        return redirect("forbidden")



# add server side validation on address and coordinates, check if the is_valid refers to the forms.py. 
# para didto nalang ibutang ang logic and serverside validation.
# add rate limits
@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
# @ratelimit(key='ip', rate='3/m', method='POST', block=True)
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
            "MAPBOX_API_KEY" : django_settings.MAPBOX_API_KEY,
        }
        return render(request, "app_agrosavvy/add_field.html", context)
    

    elif request.user.is_authenticated and request.user.roleuser.roleuser == "brgy_officer": 
        if request.method == "POST":
            # Retrieve user's barangay information - used as context for client side validation
            bo_user_address = request.user.useraddress.useraddress
            bo_user_barangay = bo_user_address.split(",")[0].strip()

            # # # Check if the field belongs to the same barangay - server side validation
            # if field.address.barangay.brgy_name != bo_user_barangay:
            #     return redirect("forbidden")

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
            "MAPBOX_API_KEY" : django_settings.MAPBOX_API_KEY,
        }
        return render(request, "app_agrosavvy/brgy_add_field.html", context)
    else:
        return redirect("forbidden")
    




def weather(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        weather_data = get_weather_data_with_minutely_hourly("Cebu City")
        context = {
            
            "weather_data": weather_data,
        }
        return render(request, "app_agrosavvy/weather.html", context)
    else:
        return redirect("forbidden")


@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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
                return redirect("view_profile")
            else:
                # messages.error(
                #     request, "Error updating profile. Please check the form."
                # )
                pass
        else:
             # Pre-process the user's contact number to remove +63 before displaying it in the form
            user_contact_number = user.contact_number
            if user_contact_number and user_contact_number.startswith("+63"):
                user.contact_number = user_contact_number[3:]

            updateprofileform = CustomUserUpdateForm(instance=user)

        context = {"updateprofileform": updateprofileform,
                    "notifications":  notifications,
                    "notifications_unread_count": notifications_unread_count,
                    }
        return render(request, "app_agrosavvy/settings.html", context)
    else:
        return redirect("forbidden")



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def view_profile(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser=='da_admin' or request.user.roleuser.roleuser=='brgy_officer'):
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
        fields = Field.objects.filter(owner = request.user, is_deleted=False)
        # user = get_object_or_404(CustomUser, pk=request.user.pk)

        context = {
            "field_count": fields.count(),
            "notifications": notifications,
            "notifications_unread_count": notifications_unread_count,
        }
        return render(request, "app_agrosavvy/view_profile.html", context)
    else:
        return redirect("forbidden")









@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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
            pending_users = PendingUser.objects.filter(is_pending=True).exclude(roleuser__roleuser="da_admin").order_by('-request_date')
        else:  # brgy_officer
            pending_users = PendingUser.objects.filter(
                useraddress__useraddress__startswith=user_barangay,
                roleuser__roleuser="farmer", is_pending=True
            ).order_by('-request_date')

        if pending_search_query:
            pending_users = pending_users.filter(
                Q(username__icontains=pending_search_query) |
                Q(email__icontains=pending_search_query) |
                Q(firstname__icontains=pending_search_query) |
                Q(lastname__icontains=pending_search_query)
            )

        if pending_filter_type and user_role == "da_admin":
            pending_users = pending_users.filter(roleuser__roleuser=pending_filter_type,)

        if pending_sort_by:
            pending_users = pending_users.order_by(pending_sort_by)


        # Disapproved Users
        disapproved_search_query = request.GET.get('disapproved_search', '')
        disapproved_filter_type = request.GET.get('disapproved_filter', '')
        disapproved_sort_by = request.GET.get('disapproved_sort', '')

        if user_role =="da_admin":
            disapproved_users = PendingUser.objects.filter(is_disapproved=True).exclude(roleuser__roleuser="da_admin").order_by('-request_date')
        else:
            disapproved_users = PendingUser.objects.filter(
                useraddress__useraddress__startswith=user_barangay,
                roleuser__roleuser="farmer", is_disapproved=True
            ).order_by('-request_date')

        
        if disapproved_search_query:
            disapproved_users = disapproved_users.filter(
                Q(username__icontains=disapproved_search_query) |
                Q(email__icontains=disapproved_search_query) |
                Q(firstname__icontains=disapproved_search_query) |
                Q(lastname__icontains=disapproved_search_query)
            )
        if disapproved_filter_type and user_role == "da_admin":
            disapproved_users = disapproved_users.filter(roleuser__roleuser=disapproved_filter_type,)
        if disapproved_sort_by:
            disapproved_users = disapproved_users.order_by(disapproved_sort_by)



        # Pagination for registered users
        registered_paginator = Paginator(registered_users, 4)
        registered_page_number = request.GET.get("registered_page")
        registered_users_page_obj = registered_paginator.get_page(registered_page_number)

        # Pagination for pending users
        pending_paginator = Paginator(pending_users, 4)
        pending_page_number = request.GET.get("pending_page")
        pending_users_page_obj = pending_paginator.get_page(pending_page_number)

        # pagination for disapproved users
        disapproved_paginator = Paginator(disapproved_users, 4)
        disapproved_page_number = request.GET.get("disapproved_page")
        disapproved_users_page_obj = disapproved_paginator.get_page(disapproved_page_number)

        # Login and CRUD events (LOGS)
        if user_role == "da_admin":
            login_events = LoginEvent.objects.filter(user__is_superuser=False).order_by('-datetime')
            # crud_events = CRUDEvent.objects.filter(user__is_superuser=False).order_by('-datetime')
        else:  # brgy_officer
            login_events = LoginEvent.objects.filter(
                user__useraddress__useraddress__startswith=user_barangay, user__is_superuser=False
            )
            # crud_events = CRUDEvent.objects.filter(
            #     user__useraddress__useraddress__startswith=user_barangay, user__is_superuser=False
            # ).order_by('-datetime')


        
        # reports for da_admin

        farmers_list = CustomUser.objects.filter(roleuser__roleuser="farmer")
        # if brgy officer
        if user_role == "brgy_officer":
            farmers_list = farmers_list.filter(useraddress__useraddress__startswith=user_barangay)

        farmers_data = {}
        for farmer in farmers_list:
            barangay = farmer.useraddress.useraddress.split(',')[0].strip()
            fields = Field.objects.filter(owner=farmer, is_deleted=False)
            crops_planted = set()
            total_hectares = fields.aggregate(total=Sum('field_acres'))['total'] or 0
            
            for field in fields:
                field_crops = FieldCropData.objects.filter(field=field, is_deleted=False).values_list('crop_planted__crop_type', flat=True)
                crops_planted.update(field_crops)
            
            if barangay not in farmers_data:
                farmers_data[barangay] = []

            farmers_data[barangay].append({
                'name': f"{farmer.firstname} {farmer.lastname}",
                'crops_planted': ", ".join(crops_planted),
                'total_hectares': round(total_hectares, 2)
            })

        # Sort the barangays
        sorted_barangays = sorted(farmers_data.keys())
        farmers_data = {barangay: farmers_data[barangay] for barangay in sorted_barangays}




        context = {
            "registered_users": registered_users,
            "registered_users_page_obj": registered_users_page_obj,
            "pending_users": pending_users,
            "pending_users_page_obj": pending_users_page_obj,
            "disapproved_users": disapproved_users,
            "disapproved_users_page_obj": disapproved_users_page_obj,
            "login_events": login_events,
            # "crud_events": crud_events,
            "registered_search_query": registered_search_query,
            "registered_filter_type": registered_filter_type,
            "registered_sort_by": registered_sort_by,
            "pending_search_query": pending_search_query,
            "pending_filter_type": pending_filter_type,
            "pending_sort_by": pending_sort_by,
            "disapproved_search_query": disapproved_search_query,
            "disapproved_filter_type": disapproved_filter_type,
            "disapproved_sort_by": disapproved_sort_by,
            # reports
            "user_role": user_role,
            "farmers_data": farmers_data,
            "sorted_barangays": sorted_barangays,
        }

        return render(request, "app_agrosavvy/user_management.html", context)
    else:
        return redirect("forbidden")







@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
# @ratelimit(key='ip', rate='1/m', method='POST', block=True)
def create_notification(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
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




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def view_notification(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        notifications = Notification.objects.filter(user_receiver=request.user, is_deleted=False).order_by('-created_at')
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
    




# def delete_notification(request, notif_id):
#     if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
#         if request.method == 'POST':
#             notification = get_object_or_404(Notification, id=notif_id, user_receiver=request.user)
            
#             if notification.user_receiver == request.user:
#                 notification.delete()
#                 messages.success(request, 'Notification deleted successfully.')
#                 return redirect("view_notofication")
#             else:
#                 messages.error(request, 'You do not have permission to delete this chat group.')
#         return redirect('view_notification')
#     else:
#         return redirect("forbidden")





    






# user management for da admin and brgy officer
def admin_deactivate_account(request, user_id):
    if not request.user.is_authenticated:
        return redirect("forbidden")
    
    if request.user.roleuser.roleuser not in ["da_admin", "brgy_officer"]:
        return redirect("forbidden")
    
    user = get_object_or_404(CustomUser, id=user_id)

    if request.user.roleuser.roleuser == "brgy_officer" and user.useraddress.useraddress != request.user.useraddress.useraddress:
        return redirect("forbidden")
    
    if request.method == "POST":
        user.active_status = False
        user.save()
        messages.success(request, "The account has been successfully deactivated.")
        return redirect("user_management")

    return render(request, "app_agrosavvy/user_management.html")




def admin_activate_account(request, user_id):
    if not request.user.is_authenticated:
        return redirect("forbidden")
    
    if request.user.roleuser.roleuser not in ["da_admin", "brgy_officer"]:
        return redirect("forbidden")
    
    user = get_object_or_404(CustomUser, id=user_id)

    if request.user.roleuser.roleuser == "brgy_officer" and user.useraddress.useraddress != request.user.useraddress.useraddress:
        return redirect("forbidden")
    
    if request.method == "POST":
        user.active_status = True
        user.save()
        messages.success(request, "The account is successfully activated.")
        return redirect("user_management")
    return render(request, "app_agrosavvy/user_management.html")





def admin_disapprove_user(request, user_id):
    if not request.user.is_authenticated:
        return redirect("forbidden")
    
    if request.user.roleuser.roleuser not in ["da_admin", "brgy_officer"]:
        return redirect("forbidden")
    
    pending_user = get_object_or_404(PendingUser, id=user_id)

    if request.user.roleuser.roleuser == "brgy_officer" and pending_user.useraddress.useraddress != request.user.useraddress.useraddress:
        return redirect("forbidden")
    
    if request.method == "POST":
        pending_user.is_disapproved = True
        pending_user.is_pending = False
        pending_user.save()

        # Send email notification to the pending user
        subject = "Agrosavvy Account Request is Disapproved"
        message = f"""
            Dear {pending_user.firstname} {pending_user.lastname},

            This is to inform you that your request for agrosavvy account has been disapproved.
            
            If you think that this is a mistake, feel free to reach out to us at any time. 

            Best regards,
            The Agrosavvy Team
        """
        recipient_list = [pending_user.email]
        
        send_mail(
            subject,
            message,
            django_settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=True,
        )

        messages.success(request, "The pending user is disapproved.")
        return redirect("user_management")
    return render(request, "app_agrosavvy/user_management.html")





def admin_approve_user(request, user_id):
    if not request.user.is_authenticated:
        return redirect("forbidden")
    
    if request.user.roleuser.roleuser not in ["da_admin", "brgy_officer"]:
        return redirect("forbidden")
    
    pending_user = get_object_or_404(PendingUser, id=user_id)

    if request.user.roleuser.roleuser == "brgy_officer" and pending_user.useraddress.useraddress != request.user.useraddress.useraddress:
        return redirect("forbidden")

    if request.method == "POST":
        CustomUser.objects.create(
            official_user_id= pending_user.official_user_id,
            username=pending_user.username,
            password=pending_user.password,
            email=pending_user.email,
            firstname=pending_user.firstname,
            middle_initial=pending_user.middle_initial,
            lastname=pending_user.lastname,
            date_of_birth=pending_user.date_of_birth,
            gender=pending_user.gender,
            contact_number=pending_user.contact_number,
            useraddress=pending_user.useraddress,
            roleuser=pending_user.roleuser,
            is_approved=True,
            approved_date=timezone.now(),
            approved_by=request.user,
        )

        login_url = request.build_absolute_uri(reverse('my_login'))
        # Send email notification to the pending user
        subject = "Agrosavvy Account Has Been Approved"
        message = f"""
            Dear {pending_user.firstname} {pending_user.lastname},

            We are pleased to inform you that your account has been successfully approved by {request.user.firstname} {request.user.lastname}. Congratulations! 🎉

            You now have full access to our system and all its features. We're excited to have you on board and look forward to your contributions. 
            Should you have any questions or need assistance, feel free to reach out to us at any time. 

            You can now login your account here:
            {login_url}

            Welcome to the team, and thank you for being a valued member of our community!

            Best regards,
            The Agrosavvy Team
        """
        recipient_list = [pending_user.email]
        
        send_mail(
            subject,
            message,
            django_settings.DEFAULT_FROM_EMAIL,  # Ensure this is set in your settings
            recipient_list,
            fail_silently=True,
        )


        pending_user.delete()
        messages.success(
            request, f"User has been approved successfully."
        )
        return redirect("user_management")
    return render(
        request,
        "app_agrosavvy/confirm_approve.html",
        {"pending_user": pending_user},
    )





def admin_approve_disapproved_user(request, user_id):

    if not request.user.is_authenticated:
        return redirect("forbidden")
    
    if request.user.roleuser.roleuser not in ["da_admin", "brgy_officer"]:
        return redirect("forbidden")
    
    disapproved_user = get_object_or_404(PendingUser, id=user_id)

    if request.user.roleuser.roleuser == "brgy_officer" and disapproved_user.useraddress.useraddress != request.user.useraddress.useraddress:
        return redirect("forbidden")

    if request.method == "POST":
        CustomUser.objects.create(
            official_user_id= disapproved_user.official_user_id,
            username=disapproved_user.username,
            password=disapproved_user.password,
            email=disapproved_user.email,
            firstname=disapproved_user.firstname,
            middle_initial=disapproved_user.middle_initial,
            lastname=disapproved_user.lastname,
            date_of_birth=disapproved_user.date_of_birth,
            gender=disapproved_user.gender,
            contact_number=disapproved_user.contact_number,
            useraddress=disapproved_user.useraddress,
            roleuser=disapproved_user.roleuser,
            is_approved=True,
            approved_date=timezone.now(),
            approved_by=request.user,
        )

        login_url = request.build_absolute_uri(reverse('my_login'))

        subject = "Agrosavvy Account Has Been Approved"
        message = f"""
            Dear {disapproved_user.firstname} {disapproved_user.lastname},

            We are pleased to inform you that your account has been successfully approved by {request.user.firstname} {request.user.lastname}. Congratulations! 🎉

            You now have full access to our system and all its features. We're excited to have you on board and look forward to your contributions. 
            Should you have any questions or need assistance, feel free to reach out to us at any time. 

            You can now login your account here:
            {login_url}

            Welcome to the team, and thank you for being a valued member of our community!

            Best regards,
            The Agrosavvy Team
        """
        recipient_list = [disapproved_user.email]
        
        send_mail(
            subject,
            message,
            django_settings.DEFAULT_FROM_EMAIL,  # Ensure this is set in your settings
            recipient_list,
            fail_silently=True,
        )

        disapproved_user.delete()
        messages.success(
            request, f"User has been approved successfully."
        )
        return redirect("user_management")
    return render(
        request,
        "app_agrosavvy/confirm_approve.html",
        {"disapproved_user": disapproved_user},
    )





@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
def manage_field(request, field_id):    
    if request.user.is_authenticated and request.user.roleuser.roleuser in ["da_admin", "brgy_officer"]:
        user_role = request.user.roleuser.roleuser
        field = get_object_or_404(Field, field_id=field_id, is_deleted=False)

        # ownership validation and RBAC
        if user_role == "brgy_officer":
            # Retrieve the user's barangay information
            user_address = request.user.useraddress.useraddress
            user_barangay = user_address.split(",")[0].strip()

            # Check if the field belongs to the same barangay
            if field.address.barangay.brgy_name != user_barangay:
                return redirect("forbidden")
        
        elif user_role !="da_admin":
            return redirect("forbidden")

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





@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def update_field(request, field_id):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "da_admin":
        field = get_object_or_404(Field, field_id=field_id, is_deleted=False)
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
            "MAPBOX_API_KEY" : django_settings.MAPBOX_API_KEY,
        }
        return render(request, "app_agrosavvy/update_field.html", context)
    

    if request.user.is_authenticated and request.user.roleuser.roleuser == "brgy_officer":
        field = get_object_or_404(Field, field_id=field_id, is_deleted=False)
        # Retrieve user's barangay information
        bo_user_address = request.user.useraddress.useraddress
        bo_user_barangay = bo_user_address.split(",")[0].strip()
        # Check if the field belongs to the same barangay
        if field.address.barangay.brgy_name != bo_user_barangay:
            return redirect("forbidden")
        
        if request.method == "POST":
            field_form = FieldForm(request.POST, instance=field)
            address_instance = field.address
            address_form = AddressForm(request.POST, instance=address_instance)
            if field_form.is_valid() and address_form.is_valid():
                updated_field = field_form.save(commit=False)
                updated_field.owner = field.owner
                updated_field.save()
                updated_address= address_form.save()
                # maybe we can directly save like this:
                # address_form.save()
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
            # Retrieve user's barangay information
            bo_user_address = request.user.useraddress.useraddress
            bo_user_barangay = bo_user_address.split(",")[0].strip()
            field_form = FieldForm(instance=field)
            address_form = AddressForm(instance=field.address)


        context = {
            "field_form": field_form,
            "address_form": address_form,
            "bo_user_barangay": bo_user_barangay,
            "MAPBOX_API_KEY" : django_settings.MAPBOX_API_KEY,
        }
        return render(request, "app_agrosavvy/brgy_update_field.html", context)
    else:
        return redirect("forbidden")




@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
def delete_field(request, field_id):
    if not request.user.is_authenticated:
        return redirect("forbidden")
    
    if request.user.roleuser.roleuser not in ["da_admin", "brgy_officer"]:
        return redirect("forbidden")
    
    field = get_object_or_404(Field, pk=field_id, is_deleted=False)

    if request.user.roleuser.roleuser == "brgy_officer":
        bo_user_address = request.user.useraddress.useraddress
        bo_user_barangay = bo_user_address.split(",")[0].strip()
        # Check if the field belongs to the same barangay
        if field.address.barangay.brgy_name != bo_user_barangay:
            return redirect("forbidden")
        
    field.delete()
    messages.success(request, "Field is successfuly deleted")
    return redirect("dashboard")

























# farmers pages
@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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
            ImageAnalysis.objects.filter(owner=request.user, is_deleted=False)
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
            ).order_by('-planting_date').values('planting_date')[:1]
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










@cache_control(no_cache=True, must_revalidate=True, no_store=True)
# @ratelimit(key='ip', rate='5/m', method='POST', block=True)
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

           # Generate title only if it does not already exist
            if not chat_group.title:
                title = chatgroup_title_generator(message)  # Generate title based on the message
                chat_group.title = title  # Assign the generated title
                chat_group.save()  # Save the updated chat group



            # Get the previous messages from the chat group (limit to the last 10 messages)
            previous_messages = chats.order_by('-created_at')[:10]
            # Format the messages into a single string for context
            conversation_history = "\n".join([f"\n\nUser: {chat.message}\nAI response: {chat.response}" for chat in previous_messages])
            # Combine history with the new message
            full_conversation = conversation_history + f"\nUser: {message}\nAI:"

           

            # barangay memory
            # Extract previously mentioned barangay or sitio if any
            if any("barangay" in message or "brgy" in message for message in conversation_history.split("\n")):
                barangay = extract_brgy_name_conv_history(conversation_history)
            else:
                barangay = extract_brgy_name(message)

            # If the user explicitly mentions for a different barangay, override the barangay value
            if "barangay" in message or "brgy" in message:
                barangay = extract_brgy_name(message)
            elif barangay is not None:
                pass 
            else:
                barangay = None
            

            intent = classify_intent(message)
            ai_context = ""




            # USING OBJECT TECHNIQUE
            if intent == "ask_help":
                if barangay is not None:
                    soil_data_entries = SoilDataSFM.objects.filter(barangay__iexact=barangay)
                    total_area = soil_data_entries.aggregate(total_area=Sum('total_area'))['total_area']
                    crops = soil_data_entries.values_list('crops_planted', flat=True)
                    ai_context = ""

                    # Keep track of processed sitios
                    processed_sitios = set()

                    # Loop through all sitios in the barangay
                    for soil_data in soil_data_entries:
                        if soil_data.sitio not in processed_sitios:
                            ai_context += (
                                f"In {barangay}, Sitio {soil_data.sitio}: "
                                f"Nitrogen level is {soil_data.get_nitrogen_level_display()}, "
                                f"Phosphorus level is {soil_data.get_phosphorus_level_display()}, "
                                f"and Potassium level is {soil_data.get_potassium_level_display()}. "
                                f"pH level is {soil_data.get_ph_level_display()}, "
                                f"indicating that it is {'acidic' if soil_data.ph_level in ['L', 'ML', 'MH'] else 'alkaline'}. "
                                f"Crops planted in Sitio {soil_data.sitio}: {soil_data.crops_planted}. "
                                f"These nutrient levels may be ideal for crops that thrive in {'low' if soil_data.nitrogen_level == 'L' else 'moderate' if soil_data.nitrogen_level in ['ML', 'MH'] else 'high'} nutrient environments.\n"
                            )
                            # Mark this sitio as processed
                            processed_sitios.add(soil_data.sitio)

                    # Add total area and crops for the whole barangay
                    ai_context += (
                        f"\nThe total farming area within {barangay} spans {total_area} hectares.\n"
                        f"Crops currently planted across all sitios in {barangay} include: {', '.join(set(crops))}."
                    )

                    # If there's no data for the barangay
                    if not soil_data_entries:
                        ai_context = "Soil data is not available for this barangay. You may check the spelling of barangay and make sure it's correct."
                else:
                    ai_context = "Say this: 'Please provide the barangay name in a full sentence.'"



            elif intent == "conversational":
                ai_context == "Ask me questions about agriculture specially in Cebu City."

           # openweathermap api
            elif intent == "weather":
                location = extract_location_with_openai(message)
                if location is not None:
                    weather_data = get_weather_data(location)
                    if weather_data:
                        ai_context = f"weather forecast for {location}:\n{weather_data}."
                    else:
                        ai_context = f"Sorry, no weather data available in that area. Try searching for a city."
                else:
                    ai_context = "Say this: 'Can you please specify the location for the weather forecast? For example: What is the weather for location X?'"

            
            # handling if no intent is processed
            else:
                ai_context = "I'm sorry, but I couldn't process your request right now. Please try again later."
            

            full_conversation_with_context = full_conversation + f"\nAI Context: {ai_context}"
            openai_response = ask_openai(full_conversation_with_context)

            cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', openai_response)
            cleaned_content = re.sub(r'^(#+)\s*(.*?)$', lambda m: f'<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>', cleaned_content, flags=re.MULTILINE)
            cleaned_content = cleaned_content.replace('\n', '<br>')
            final_response = cleaned_content


            # debugging
            print("Processed Intent:" , intent)
            # if barangay:
            #     print("barangay:" + barangay)
            # else:
            #     print("brgy not found")
            print("Full Conversation with Context to OpenAI:", full_conversation_with_context)
        
        
            # Regardless of intent, continue to enhance the response with OpenAI
            full_conversation_with_context = full_conversation + f"\nAI Context: {ai_context}"
            openai_response = ask_openai(full_conversation_with_context)


            # Clean and format AI output for display
            cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', openai_response)  # Bold
            cleaned_content = re.sub(r'^(#+)\s*(.*?)$', lambda m: f'<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>', cleaned_content, flags=re.MULTILINE)  # Headers
            cleaned_content = cleaned_content.replace('\n', '<br>')  # Line breaks

            # Combine both the context and OpenAI's general response
            final_response = cleaned_content


            # Save the chat and response
            chat = Chat(
                user=request.user, 
                chat_group=chat_group, 
                message=message, 
                response=final_response, 
                ai_context=ai_context,
                created_at=timezone.now()
            )
            chat.save()

            return JsonResponse({
                'message': message, 
                'response': final_response, 
                'group_id': chat_group.id, 
                'status': 'message_sent',
                'title': chat_group.title,
            })
        reviewrating_context = reviewrating(request)
        context = {
            "chats": chats,
            "chat_group": chat_group,
            "chat_groups": ChatGroup.objects.filter(user=request.user, is_deleted=False),
        }
        context.update(reviewrating_context)
        return render(request, 'bofa_pages/ai/bofa_chatai.html', context)
    else:
        return redirect("forbidden")




@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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









@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
# @ratelimit(key='ip', rate='1/m', method='POST', block=True)
def bofa_image_analysis(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        analysis = None 
        history = ImageAnalysis.objects.filter(owner=request.user, is_deleted=False).order_by('-created_at')[:5]  # Get the 5 most recent analyses
        history_json = json.loads(serialize('json', history))
        reviewrating_context = reviewrating(request)

        if request.method == 'POST':
            form = ImageAnalysisForm(request.POST, request.FILES)
            if form.is_valid():
                analysis = form.save(commit=False)
                image = form.cleaned_data.get('image') 

                if image:
                    base64_image = encode_image(image)

                    try:
                        # Send the request to the API
                        response = client.chat.completions.create(
                                model=THIS_MODEL,
                                messages=[
                                    {
                                        "role": "system",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": "As an AI field analyst, analyze the attached image to assess crop health conditions. Identify any visible issues such as diseases or pests, and suggest actionable improvements for optimal crop growth. Provide the description in a more professional way and describe it well. Do not provide analysis on images that is unrelated to agriculture, crops, plants. This model is unable to answer questions."
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
                                max_tokens=500
                        )

                        if response.choices:
                            ai_output = response.choices[0].message.content
                            # print(f"AI Response: {ai_output}") 

                            # Clean and format AI output for display
                            cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', ai_output)  # Bold
                            cleaned_content = re.sub(r'^(#+)\s*(.*?)$', lambda m: f'<h{len(m.group(1))}>{m.group(2)}</h{len(m.group(1))}>', cleaned_content, flags=re.MULTILINE)  # Headers
                            cleaned_content = cleaned_content.replace('\n', '<br>')  # Line breaks
                            cleaned_content = translate_to_bisaya(cleaned_content)
                            # Save analysis result and image
                            analysis.image = image
                            analysis.analysis_output = mark_safe(cleaned_content)
                            analysis.owner = request.user
                            analysis.title = image_analysis_title_generator(cleaned_content)
                            analysis.save()
                            # messages.success(request, 'Analysis saved.')
                            return redirect("bofa_image_analysis")
                        else:
                            messages.error(request, "AI did not respond. Please try again later.")

                    except APIConnectionError as e:
                        messages.error(request, "There was a connection issue with the AI service. Please try again later.")
                    except OpenAIError as e:
                        messages.error(request, "An error occurred with the AI service. Please try again later.")
                    except Exception as e:
                        messages.error(request, "An unexpected error occurred. Please try again later.")
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
            "history": history,
            "history_json": json.dumps(history_json),
        }
        context.update(reviewrating_context)
        return render(request, "bofa_pages/ai/bofa_analysisai.html", context)
    else:
        return redirect("forbidden")



@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
def bofa_delete_image_analysis(request, pk):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        if request.method == "POST":
            analysis= get_object_or_404(ImageAnalysis, pk=pk, owner=request.user)
            if analysis.owner == request.user:
                analysis.delete()
                messages.success(request, "Image analysis successfully deleted.")
                return redirect("bofa_image_analysis")
            else:
                messages.error(request, "You do not have permission to delete this analysis.")
        return render(request, "bofa_pages/ai/bofa_analysisai.html")
    else:
        return redirect("forbidden")



def bofa_map(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == 'farmer':
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
                    "address": f"{field.address.barangay}, {field.address.city_municipality}" if field.address else "No address",
                    "latitude": field.address.latitude,
                    "longitude": field.address.longitude,
                    "crop": field.latest_crop_type or "No crop data",
                    "owner_name": field.owner.get_full_name() if field.owner else "No owner",
                    "owner_contact": str(field.owner.contact_number) if field.owner and field.owner.contact_number else "No contact info",
                })

        context = {
            "fields_json": json.dumps(fields_json, cls=DjangoJSONEncoder),
            "crops": Crop.objects.all(),
            "notifications": notifications,
            "notifications_unread_count": notifications_unread_count,
            "MAPBOX_API_KEY" : django_settings.MAPBOX_API_KEY,
        }
        return render(request, "bofa_pages/bofa_map.html", context)

    else:
        return redirect("forbidden")



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
# @ratelimit(key='ip', rate='3/m', method='POST', block=True) 
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
            "MAPBOX_API_KEY" : django_settings.MAPBOX_API_KEY,
        }
        return render(request, "bofa_pages/bofa_add_field.html", context)
    else:
        return redirect("forbidden")




def bofa_weather(request):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        weather_data = get_weather_data_with_minutely_hourly("Cebu City")
        context = {
            "weather_data": weather_data,
        }
        return render(request, "bofa_pages/bofa_weather.html", context)
    else:
        return redirect("forbidden")




@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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
                return redirect("bofa_view_profile")
            else:
                pass
        else:
            # Pre-process the user's contact number to remove +63 before displaying it in the form
            user_contact_number = user.contact_number
            if user_contact_number and user_contact_number.startswith("+63"):
                user.contact_number = user_contact_number[3:]

            updateprofileform = CustomUserUpdateForm(instance=user)

        context = {"updateprofileform": updateprofileform, 
                   "notifications": notifications,
                   'notifications_unread_count': notifications_unread_count,
                   }
        return render(request, "bofa_pages/bofa_settings.html", context)
    else:
        return redirect("forbidden")




@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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
    

    
@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
def bofa_view_notification(request):
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
    





@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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





@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
def bofa_update_field(request, field_id):
    if request.user.is_authenticated and request.user.roleuser.roleuser == "farmer":
        field = get_object_or_404(Field, field_id=field_id)

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
            "MAPBOX_API_KEY" : django_settings.MAPBOX_API_KEY,
        }
        return render(request, "bofa_pages/bofa_update_field.html", context)
    else:
        return redirect("forbidden")



@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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
# @cache_control(no_cache=True, must_revalidate=True, no_store=True) 
# @ratelimit(key='ip', rate='2/m', method='POST', block=True)
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
                return redirect("image_analysis")
            elif request.user.roleuser.roleuser == "farmer":
                return redirect("bofa_image_analysis")
        else:
            # messages.error(request, "Please check the errors below.")
            pass
    else:
        rform = ReviewratingForm()

    return {"rform": rform}


@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
def mark_notifications_as_read(request):
    # Mark all unread notifications as read for the current user
    Notification.objects.filter(user_receiver = request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})



# check security on field ownership if ma deny or approve
@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
# @ratelimit(key='ip', rate='1/m', method='POST', block=True)
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
                errors = asdform.errors.get_json_data()
                all_errors = []
                # Loop through form errors
                for field, errors in asdform.errors.items():
                    for error in errors:
                        all_errors.append(f"{field.capitalize()}: {error}")
                # Concatenate all errors into a single message
                error_message = " | ".join(all_errors)
                # Display the concatenated error message
                messages.error(request, error_message)
                # go back to the old page
                if request.user.roleuser.roleuser == "da_admin" or  request.user.roleuser.roleuser == "brgy_officer":
                    return redirect(
                        reverse("manage_field", kwargs={"field_id": field_id})
                    )
                elif request.user.roleuser.roleuser == "farmer":
                    return redirect(
                        reverse("bofa_manage_field", kwargs={"field_id": field_id})
                    ) 
        else:
            asdform = FieldSoilDataForm()
        return {"asdform": asdform, "field": field}
    else:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect("forbidden")



@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
# @ratelimit(key='ip', rate='1/m', method='POST', block=True)
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
                errors = acdform.errors.get_json_data()
                all_errors = []
                # Loop through form errors
                for field, errors in acdform.errors.items():
                    for error in errors:
                        all_errors.append(f"{field.capitalize()}: {error}")
                error_message = " | ".join(all_errors)
                messages.error(request, error_message)
                # go back to old page
                if request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer":
                    return redirect(
                        reverse("manage_field", kwargs={"field_id": field_id})
                    )
                elif request.user.roleuser.roleuser == "farmer":
                    return redirect(
                        reverse("bofa_manage_field", kwargs={"field_id": field_id})
                    )
        else:
            acdform = FieldCropForm()
        
        context={"acdform": acdform, "field": field}
        return context
    else:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect("forbidden")



@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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
                errors = fsdform.errors.get_json_data()
                all_errors = []
                # Loop through form errors
                for field, errors in fsdform.errors.items():
                    for error in errors:
                        all_errors.append(f"{field.capitalize()}: {error}")
                # Concatenate all errors into a single message
                error_message = " | ".join(all_errors)
                # Display the concatenated error message
                messages.error(request, error_message)
                # go back to the old page
                if request.user.roleuser.roleuser == "da_admin" or  request.user.roleuser.roleuser == "brgy_officer":
                    return redirect(
                        reverse("manage_field", kwargs={"field_id": field_id})
                    )
                elif request.user.roleuser.roleuser == "farmer":
                    return redirect(
                        reverse("bofa_manage_field", kwargs={"field_id": field_id})
                    ) 
        else:
            # Show the current values in the form
            fsdform = FieldSoilDataForm(instance=soil)
        return {"fsdform": fsdform, "soil": soil}
    else:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect("forbidden")



@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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
                errors = fcdform.errors.get_json_data()
                all_errors = []
                # Loop through form errors
                for field, errors in fcdform.errors.items():
                    for error in errors:
                        all_errors.append(f"{field.capitalize()}: {error}")
                error_message = " | ".join(all_errors)
                messages.error(request, error_message)
                # go back to old page
                if request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer":
                    return redirect(
                        reverse("manage_field", kwargs={"field_id": field_id})
                    )
                elif request.user.roleuser.roleuser == "farmer":
                    return redirect(
                        reverse("bofa_manage_field", kwargs={"field_id": field_id})
                    )
        else:
            # Show the current values in the form
            fcdform = FieldCropForm(instance=crop)
        return {"fcdform": fcdform, "crop": crop}
    else:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect("forbidden")



@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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



@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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























# AI FEATURES
# for weather
def extract_location_with_openai(message):
    prompt = (
        f"The user asked about the weather. Please extract and return only the location name if there is any in the message below. \n\n"
        f"Message: '{message}'\n\n"
        f"Location:"
    )
    response = ask_openai(prompt)
    location = response.strip() if response else None
    return location


# checks for 2 words
def extract_brgy_name(message, brgy_list=None):
    brgy_list = [
        "Adlaon", "Agsungot", "Babag", "Binaliw", "Bonbon", "Budlaan", "Buhisan", "Buot-Taup", "Busay", 
        "Cambinocot", "Guba", "Kalunasan", "Lusaran", "Mabini", "Malubog", "Pamutan", "Paril", "Pung-ol Sibugay",  
        "Pulangbato", "Sapangdaku", "Sinsin", "Sirao", "Sudlon I", "Sudlon II", "Tabunan", "Tagba-o",  
        "Taptap", "Toong",
    ]
    # match the word in the sentence with brgy_list
    for brgy_name in brgy_list:
        if brgy_name.lower() in message.lower():  
            return brgy_name
    # match by finding words after the word "Barangay"
    # brgy is not part of captured group because of ? symbol.
    matched_brgy_name = re.search(r'\b(?:barangay|brgy)\s+([A-Za-z0-9-]+(?:\s+[A-Za-z0-9-]+)?)', message, re.IGNORECASE)
    if matched_brgy_name:
        return matched_brgy_name.group(1).strip()
    
    # If no barangay found, return None
    return None


# reversed conversation history = get the latest brgy 
def extract_brgy_name_conv_history(conversation_history, brgy_list=None):
    brgy_list = [
        "Adlaon", "Agsungot", "Babag", "Binaliw", "Bonbon", "Budlaan", "Buhisan", "Buot-Taup", "Busay", 
        "Cambinocot", "Guba", "Kalunasan", "Lusaran", "Mabini", "Malubog", "Pamutan", "Paril", "Pung-ol Sibugay",  
        "Pulangbato", "Sapangdaku", "Sinsin", "Sirao", "Sudlon I", "Sudlon II", "Tabunan", "Tagba-o",  
        "Taptap", "Toong",
    ]

    # Split conversation history into individual lines
    conversation_lines = conversation_history.split("\n")
    # Look for the most recent occurrence of barangay name from brgy_list (in reverse)
    for line in reversed(conversation_lines):
        for brgy_name in brgy_list:
            if brgy_name.lower() in line.lower():
                return brgy_name
    # If no barangay found in the brgy_list, search for the word "barangay" or "brgy"
    matched_brgy_name = re.search(r'\b(?:barangay|brgy)\s+([A-Za-z0-9-]+(?:\s+[A-Za-z0-9-]+)?)', conversation_history, re.IGNORECASE)
    
    if matched_brgy_name:
        return matched_brgy_name.group(1).strip()
    
    # If no barangay found, return None
    return None


def classify_intent(message):
    prompt = f"""
    You are an AI that classifies user intents. 
    Here are the possible intents:
  
    1. weather: Questions related to weather, including current conditions, forecasts, or specific weather events.
    2. ask_help: Questions asking data like soil nutrients, best crops, area.
    3. conversational: About greetings, some questions that dont need specific data.
    User: {message}
    Choose only one intent. Choose the best one that fits.
    """
    # 14. RAG technique for pdf and documents

    response = client.chat.completions.create(
        model=THIS_MODEL,
        messages=[
            {"role": "system", "content": "You are an intent classification assistant."},
            {"role": "user", "content": prompt},
        ]
    )
    
    # Retrieve and clean the response
    intent = response.choices[0].message.content.strip()
    if not intent:
        return None
    return intent

# main prompt for chat
def ask_openai(message):
    response = client.chat.completions.create(
        model = THIS_MODEL,
        messages=[
             {
                "role": "system", 
                "content": (
                    "You are an agriculture expert. "
                    "Do not use 'I' or 'we' in your answers."
                    "Respond in the same language the user is using."
                    "Only provide information if the data is confirmed and available in the database."
                    "Ensure your answers are consistent."
                    "Always refer to the full chat history to maintain context and give relevant responses."
                )
            },
            {"role": "user", "content": message},
        ]
    )
    answer = response.choices[0].message.content.strip()
    if not answer:
        return None
    return answer   



def chatgroup_title_generator(message):
    response = client.chat.completions.create(
        model=THIS_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an assistant specialized in generating titles for chat groups."
                    "Base the first message or question to generate the title, and avoid using first-person references."
                    "The title should be descriptive of the message. 3 words maximum."
                )
            },
            {"role": "user", "content": message},
        ]
    )
    title = response.choices[0].message.content.strip()
    if not title:
        return None
    return title




def image_analysis_title_generator(firstline_output):
    response = client.chat.completions.create(
        model=THIS_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an assistant specialized in generating titles for image analysis."
                    "Base the first line of the output to generate the title, and avoid using first-person references."
                    "The title should be descriptive. 3 words maximum."
                )
            },
            {"role": "user", "content": firstline_output},
        ]
    )
    title = response.choices[0].message.content.strip()
    if not title:
        return None
    return title




def translate_to_bisaya(cleaned_content):
    response = client.chat.completions.create(
        model=THIS_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                   "As an bisaya translator, act as the best bisaya translator. Translate this to bisaya dialect."
                )
            },
            {"role": "user", "content": cleaned_content},
        ]
    )
    translated_content = response.choices[0].message.content.strip()
    if not translated_content:
        return None
    return translated_content




def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')





















# authentication related codes
def landing_page(request):
    return render(request, "auth_pages/landing_page.html", {})

@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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
                "Your account is pending for approval. Please check your email.",
            )
            return redirect("my_login")
        else:
           return render(request, 'auth_pages/register_da_admin.html', {'form': form})
    else:
        form = PendingUserForm()
    context = {
        "form": form,
    }
    return render(request, "auth_pages/register_da_admin.html", context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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
                "Your account is pending for approval. Please check your email.",
            )
            return redirect("my_login")
        else:
            return render(request, 'auth_pages/register_barangay_officer.html', {'form': form})
    else:
        form = PendingUserForm()
    return render(
        request,
        "auth_pages/register_barangay_officer.html",
        {
            "form": form,
        },
    )

@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
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
                "Your account is pending for approval. Please check your email.",
            )
            return redirect("my_login")
        else:
            return render(request, 'auth_pages/register_farmer.html', {'form': form})
    else:
        form = PendingUserForm()
    return render(
        request,
        "auth_pages/register_farmer.html",
        {"form": form,
        },
    )






def get_client_ip(request):
    """Extract the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip





@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
def my_login(request):
    form = LoginForm(request.POST or None)
    ip_address = get_client_ip(request)

    # Check if IP or username is blocked
    if request.method == "POST":
        username = request.POST.get("username")
        if FailedLoginAttempt.is_blocked(ip_address=ip_address, username=username):
            messages.error(request,"Too many failed login attempts. Please try again after 30 minutes.")
            return render(request, "auth_pages/my_login.html", {"form": form})
        

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
                    return redirect("my_login")
                else:
                    messages.error(request, "Invalid username or password")
            except PendingUser.DoesNotExist:
                pass

            user = authenticate(request, username=username, password=password)
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
                messages.error(request, "Invalid username or password")
                # Log failed login attempt
                FailedLoginAttempt.objects.create(ip_address=ip_address, username=username)
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






def password_change(request):
    if request.user.is_authenticated and (request.user.roleuser.roleuser == "da_admin" or request.user.roleuser.roleuser == "brgy_officer"):
        notifications = Notification.objects.filter(user_receiver=request.user).order_by('-created_at')
        notifications_unread_count = notifications.filter(is_read=False).count()
        user = get_object_or_404(CustomUser, pk=request.user.pk)

        if request.method == "POST":
            passwordchangeform = CustomPasswordChangeForm(request.user, request.POST)
            if passwordchangeform.is_valid():
                user = passwordchangeform.save()
                # Maintain the user's session, we can remove this kay this wont make sense 
                # since we need to logout users after password change
                update_session_auth_hash(request, user) 
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






def forbidden(request):
    return render(request, "error_pages/forbidden.html")


def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)







