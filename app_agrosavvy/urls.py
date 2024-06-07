from django.urls import path, include
from django.contrib import admin
from app_agrosavvy import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('ai', views.ai, name='ai'),
    path('map', views.map, name='map'),
    path('add_field', views.add_field, name='add_field'),
    path('weather', views.weather, name='weather'),
    path('settings', views.settings, name='settings'),



    path('update_field/<int:field_id>/', views.update_field, name='update_field'),
    path('delete_field/<int:field_id>/', views.delete_field, name='delete_field'),

]