# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Crop, Field, Address, SoilData


class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # @admin.action(description="Approve selected users")
    # def approve_users(modeladmin, request, queryset):
    #     queryset.update(is_approved=True, approved_date=now(), approved_by=request.user)

    # format in viewing user details in django admin
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {"fields": ("firstname", "lastname", "email", "date_of_birth")},
        ),
        ("Roles", {"fields": ("is_farmer", "is_barangay_officer", "is_da_admin")}),
        (
            "Registration | Approval | Active Status - Info",
            {"fields": ("request_date", "is_approved", "approved_date", "approved_by", "active_status")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    # "is_active",
                    "is_staff",
                    "is_superuser",
                    # "groups",
                    # "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )

    # format when adding new user in django admin
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "firstname",
                    "lastname",
                    "email",
                    # "is_active",
                    # "active_status",
                    "is_staff",
                    "is_superuser",
                    "is_farmer",
                    "is_barangay_officer",
                    "is_da_admin",
                    "request_date",
                    "is_approved",
                    "approved_date",
                    "approved_by",
                ),
            },
        ),
    )

    # format in viewing all users
    list_display = (
        "username",
        "email",
        # "firstname",
        # "lastname",
        # "is_farmer",
        # "is_barangay_officer",
        # "is_da_admin",
        # "is_staff",
        "active_status",
        "is_approved",
    )

    # fields that can be searched
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )
    ordering = "username",

    # Optionally, exclude request_date from readonly_fields if it's automatically set
    readonly_fields = ("request_date",)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Crop)
admin.site.register(Field)
admin.site.register(Address)
admin.site.register(SoilData)
