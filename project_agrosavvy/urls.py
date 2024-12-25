from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls import handler404
from django.shortcuts import render


# Custom 404 View
def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

# Set the handler for 404 errors
handler404 = 'project_agrosavvy.urls.custom_404_view'


urlpatterns = [
    path('agroADMINsavvyCGLR/', admin.site.urls),
    path('',include('app_agrosavvy.urls')),
    path('datawizard/', include('data_wizard.urls')),
]



# Fallback for DEBUG=True to handle unknown paths
from django.conf import settings as heysettings
if heysettings.DEBUG:
    urlpatterns += [
        re_path(r'^.*$', custom_404_view),
    ]


# note: 404 ovveride is only used for development stage
# change to debug false and static and media server(aws) to serve static files on production stage