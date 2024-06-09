from django.urls import path, include
from django.contrib import admin
from app_agrosavvy import views


urlpatterns = [
    #main pages
    path('dashboard', views.dashboard, name='dashboard'),
    path('ai', views.ai, name='ai'),
    path('map', views.map, name='map'),
    path('add_field', views.add_field, name='add_field'),
    path('weather', views.weather, name='weather'),
    path('settings', views.settings, name='settings'),


    #field management
    path('update_field/<int:field_id>/', views.update_field, name='update_field'),
    path('delete_field/<int:field_id>/', views.delete_field, name='delete_field'),

    #auth urls
    path('', views.landing_page, name='landing_page'),
    path('my_login', views.my_login, name='my_login'),
    path('register', views.register, name='register'),
    path('my_logout', views.my_logout, name='my_logout'),
]