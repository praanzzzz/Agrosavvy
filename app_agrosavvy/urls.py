from django.urls import path, include
from django.contrib import admin
from app_agrosavvy import views


urlpatterns = [
    #auth urls
    path('my_login', views.my_login, name='my_login'),
    # path('register', views.register, name='register'),
    path('register/farmer/', views.register_farmer, name='register_farmer'),
    path('register/barangay_officer/', views.register_barangay_officer, name='register_barangay_officer'),
    path('register/da_admin/', views.register_da_admin, name='register_da_admin'),
    path('my_logout', views.my_logout, name='my_logout'),


    #main pages for da admin
    path('', views.landing_page, name='landing_page'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('ai', views.ai, name='ai'),
    path('map', views.map, name='map'),
    path('add_field', views.add_field, name='add_field'),
    path('weather', views.weather, name='weather'),
    path('settings', views.settings, name='settings'),

    #field management for da admin
    path('update_field/<int:field_id>/', views.update_field, name='update_field'),
    path('delete_field/<int:field_id>/', views.delete_field, name='delete_field'),



    #barangay officers and farmers page
    path('bofa_dashboard', views.bofa_dashboard, name='bofa_dashboard'),
    path('bofa_ai', views.bofa_ai, name='bofa_ai'),
    path('bofa_map', views.bofa_map, name='bofa_map'),
    path('bofa_add_field', views.bofa_add_field, name='bofa_add_field'),
    path('bofa_weather', views.bofa_weather, name='bofa_weather'),
    path('bofa_settings', views.bofa_settings, name='bofa_settings'),

    #field management for Brgy officers and farmers
    path('bofa_update_field/<int:field_id>/', views.bofa_update_field, name='bofa_update_field'),
    path('bofa_delete_field/<int:field_id>/', views.bofa_delete_field, name='bofa_delete_field'),



    #forbidden, 404 chuchu
    path('forbidden', views.forbidden, name='forbidden'),
]