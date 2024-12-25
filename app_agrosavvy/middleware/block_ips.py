from django.http import HttpResponseForbidden
from django.shortcuts import render
from app_agrosavvy.models import BannedIP

class BlockBannedIPsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip_address = self.get_client_ip(request)
        if BannedIP.objects.filter(ip_address=ip_address).exists():
            return HttpResponseForbidden(render(request, '403.html'))
        return self.get_response(request)

    # # for testing - hardcode ip address
    # def __call__(self, request):
    #     banned_ips = ['127.0.0.1', '192.168.1.1']  # List of banned IPs
    #     ip = request.META.get('REMOTE_ADDR')
    #     if ip in banned_ips:
    #         return HttpResponseForbidden(render(request, '403.html'))
    #     response = self.get_response(request)
    #     return response



    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
