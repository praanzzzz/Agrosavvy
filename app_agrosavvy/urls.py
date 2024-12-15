from django.urls import path, include
from django.contrib import admin
from app_agrosavvy import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.landing_page, name='landing_page'),

    #authentication
    path('my_login', views.my_login, name='my_login'),
    path('register/farmer/', views.register_farmer, name='register_farmer'),
    path('register/barangay_officer/', views.register_barangay_officer, name='register_barangay_officer'),
    path('register/da_admin/', views.register_da_admin, name='register_da_admin'),
    path('my_logout', views.my_logout, name='my_logout'),


    # forgot and change password thru email
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='auth_pages/password_reset_form.html',
        email_template_name='auth_pages/password_reset_email.html', 
        subject_template_name='auth_pages/password_reset_subject.txt'),
        name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
          template_name='auth_pages/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
         template_name='auth_pages/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
         template_name='auth_pages/password_reset_complete.html'
    ), name='password_reset_complete'),

    # main pages for da admin
    path('dashboard/', views.dashboard, name='dashboard'),

    # ai
    path('chat/', views.chat, name='chat'),
    path('chat/group/<int:group_id>/', views.chat, name='chat_group'),
    path('chat/delete_group/<int:group_id>/', views.delete_chat_group, name='delete_chat_group'),
    path('image_analysis', views.image_analysis, name='image_analysis'),
    path('delete_image_analysis/<int:pk>/', views.delete_image_analysis, name = 'delete_image_analysis'),


    path('map', views.map, name='map'),
    path('add_field', views.add_field, name='add_field'),
    path('weather', views.weather, name='weather'),
    path('settings/', views.settings, name='settings'), # update profile
    path('user_management', views.user_management, name='user_management'),

    # notifications
    path('create_notification', views.create_notification, name='create_notification'),
    path('view_notification', views.view_notification, name='view_notification'),
    path('mark_as_read/', views.mark_notifications_as_read, name='mark_notifications_as_read'),
    path('bofa_view_notification', views.bofa_view_notification, name='bofa_view_notification'),
    # path('delete_notification/<int:notif_id>/', views.delete_notification, name='delete_notification'),
    # path('bofa_delete_notification', views.bofa_delete_notification, name='bofa_delete_notification'),

    # user management
    path('admin_deactivate_account/<int:user_id>', views.admin_deactivate_account, name="admin_deactivate_account"),
    path('admin_activate_account/<int:user_id>', views.admin_activate_account, name='admin_activate_account'),
    path('admin_approve_user/<int:user_id>', views.admin_approve_user, name='admin_approve_user'),
    path('admin_disapprove_user/<int:user_id>', views.admin_disapprove_user, name='admin_disapprove_user'),
    path('admin_approve_disapproved_user/<int:user_id>', views.admin_approve_disapproved_user, name='admin_approve_disapproved_user'),


    #settings section urls
    path('view_profile', views.view_profile, name='view_profile'),
    path('settings/password_change', views.password_change, name='password_change'),
    path('settings/billing', views.billing, name='billing'),
    path('deactivate_account/', views.deactivate_account, name='deactivate_account'),
  


    #field management for da admin
    path('dashboard/manage_field/update_field/<int:field_id>/', views.update_field, name='update_field'),
    path('dashboard/manage_field/delete_field/<int:field_id>/', views.delete_field, name='delete_field'),
    path('dashboard/manage_field/<int:field_id>/', views.manage_field, name='manage_field'),


    # crop and soil data management for da and bofa
    path('add_soil_data/<int:field_id>/', views.add_soil_data, name='add_soil_data'),
    path('delete_soil_data/<int:soil_id>/', views.delete_soil_data, name='delete_soil_data'),
    path('add_crop_data/<int:field_id>/', views.add_crop_data, name='add_crop_data'),
    path('delete_crop_data/<int:fieldcrop_id>/', views.delete_crop_data, name='delete_crop_data'),
    path('update_soil_data<int:soil_id>/<int:field_id>/', views.update_soil_data, name='update_soil_data'),
    path('update_crop_data/<int:fieldcrop_id>/<int:field_id>', views.update_crop_data, name='update_crop_data'),




    # callable function urls
    path('reviewrating/', views.reviewrating, name='reviewrating'),
    path('classify_intent/', views.classify_intent, name='classify_intent'),



    #barangay officers and farmers page
    path('bofa_dashboard/', views.bofa_dashboard, name='bofa_dashboard'),


    # bofa ai
    path('bofa_chat/', views.bofa_chat, name='bofa_chat'),
    path('bofa_chat/group/<int:group_id>/', views.bofa_chat, name='bofa_chat_group'),
    path('bofa_chat/delete_group/<int:group_id>/', views.bofa_delete_chat_group, name='bofa_delete_chat_group'),
    path('bofa_image_analysis', views.bofa_image_analysis, name='bofa_image_analysis'),
    path('bofa_delete_image_analysis/<int:pk>/', views.bofa_delete_image_analysis, name = 'bofa_delete_image_analysis'),


    path('bofa_map', views.bofa_map, name='bofa_map'),
    path('bofa_add_field', views.bofa_add_field, name='bofa_add_field'),
    path('bofa_weather', views.bofa_weather, name='bofa_weather'),
    path('bofa_settings/', views.bofa_settings, name='bofa_settings'),


    #settings section urls
    path('bofa_view_profile', views.bofa_view_profile, name='bofa_view_profile'),
    path('bofa_settings/bofa_password_change', views.bofa_password_change, name='bofa_password_change'),
    path('bofa_deactivate_account/', views.bofa_deactivate_account, name='bofa_deactivate_account'),
    path('bofa_settings/bofa_billing', views.bofa_billing, name='bofa_billing'),

    #field management for Brgy officers and farmers
    path('bofa_dashboard/bofa_manage_field/bofa_update_field/<int:field_id>/', views.bofa_update_field, name='bofa_update_field'),
    path('bofa_dashboard/bofa_delete_field/<int:field_id>/', views.bofa_delete_field, name='bofa_delete_field'),
    path('bofa_dashboard/bofa_manage_field/<int:field_id>/', views.bofa_manage_field, name="bofa_manage_field"),

    #forbidden
    path('forbidden', views.forbidden, name='forbidden'),
]



# it enables django to fetch static files during developmemt phase.
# on production stage, must use static and media file server
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)