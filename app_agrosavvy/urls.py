from django.urls import path, include
from django.contrib import admin
from app_agrosavvy import views
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('ai', views.ai, name='ai'),
    path('map', views.map, name='map'),
    path('contibute', views.contribute, name='contribute'),
    path('weather', views.weather, name='weather'),
    path('settings', views.settings, name='settings'),
]