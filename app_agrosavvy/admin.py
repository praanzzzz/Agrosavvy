from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .models import (
    CustomUser,
    Field,
    Address,
    FieldSoilData,
    PendingUser,
    ReviewRating,
    FieldSoilData,
    FieldCropData,
    RoleUser,
    Crop,
    Barangay,
    Gender,
)


class CustomUserAdmin(UserAdmin):
    model = CustomUser

    fieldsets = (
        (None, {"fields": ("username", "password", "profile_picture")}),
        (
            "Personal info",
            {"fields": ("firstname", "lastname", "email", "date_of_birth", "gender")}, # added gender here
        ),
        ("Roles", {"fields": ("roleuser",)}),
        (
            "Registration | Approval | Active Status - Info",
            {
                "fields": (
                    "request_date",
                    "is_approved",
                    "approved_date",
                    "approved_by",
                    "active_status",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )

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
                    "gender", # added gender
                    "is_staff",
                    "is_superuser",
                    "roleuser",
                    "request_date",
                    "is_approved",
                    "approved_date",
                    "approved_by",
                ),
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "active_status",
        "is_approved",
        "roleuser",
    )

    search_fields = (
        "username",
        "email",
        "firstname",
        "lastname",
    )
    ordering = ("username",)
    readonly_fields = ("request_date",)


@admin.action(description="Approve selected users")
def approve_users(modeladmin, request, queryset):
    for pending_user in queryset: # add filter to da admin only
        CustomUser.objects.create(
            username=pending_user.username,
            password=pending_user.password,
            email=pending_user.email,
            firstname=pending_user.firstname,
            lastname=pending_user.lastname,
            date_of_birth=pending_user.date_of_birth,
            gender=pending_user.gender,  # added gender here
            # useraddress=pending_user.useraddress,
            roleuser = pending_user.roleuser,
            is_approved=True,
            approved_date=timezone.now(),
            approved_by=request.user,
        )
        pending_user.delete()


class PendingUserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "email",
        "roleuser",
        "request_date",
    )
    actions = [approve_users]

    readonly_fields = (
        "request_date",
        "username",
        "email",
        "firstname",
        "lastname",
        "gender", # added gender here
        "date_of_birth",
        "roleuser"
    )

    # Prevent deletion of pending users directly from admin
    def has_delete_permission(self, request, obj=None):
        return False

    # Prevent adding new pending users directly from admin
    def has_add_permission(self, request):
        return False

    # hide password in admin interface
    def get_exclude(self, request, obj=None):

        exclude = super().get_exclude(request, obj) or []
        return exclude + ["password"]

    # pending user order by request_date
    def get_queryset(self, request):
        # Override queryset to order by request_date in descending order
        return super().get_queryset(request).order_by("-request_date")


class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = (
        "reviewrating_id",
        "reviewer",
        "rating",
        "review_header",
        "rate_date",
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(PendingUser, PendingUserAdmin)
admin.site.register(Field)
admin.site.register(Address)
admin.site.register(ReviewRating, ReviewRatingAdmin)
admin.site.register(FieldCropData)
admin.site.register(FieldSoilData)
admin.site.register(Crop)
admin.site.register(RoleUser)
admin.site.register(Barangay)
admin.site.register(Gender)
