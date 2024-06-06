from django.shortcuts import render


def dashboard(request):
    return render(request, 'dashboard.html', {})

def ai(request):
    return render(request, 'ai.html', {})


def map(request):
    return render(request, 'map.html', {})

def contribute(request):
    return render(request, 'contribute.html', {})


def weather(request):
    return render(request, 'weather.html', {})

def settings(request):
    return render(request, 'settings.html', {})

