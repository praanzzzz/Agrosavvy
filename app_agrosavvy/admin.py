# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Crop, Field, Address, SoilData

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('firstname', 'lastname', 'email')}),
        ('Roles', {'fields': ('is_farmer', 'is_barangay_officer', 'is_da_admin')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'firstname', 'lastname', 'email', 'is_active', 'is_staff', 'is_superuser', 'is_farmer', 'is_barangay_officer', 'is_da_admin')}
        ),
    )
    list_display = ('username', 'email', 'firstname', 'lastname', 'is_farmer', 'is_barangay_officer', 'is_da_admin', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Crop)
admin.site.register(Field)
admin.site.register(Address)
admin.site.register(SoilData)
