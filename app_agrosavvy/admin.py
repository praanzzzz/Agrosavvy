from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.contrib.admin.models import LogEntry
from django.utils.translation import gettext_lazy as _
import data_wizard
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
    UserAddress,
    ChatGroup,
    Chat,
    ImageAnalysis,
    Notification,
    SoilDataSFM,
    BannedIP,
    FailedLoginAttempt,
)





@admin.action(description="Unsubscribe users")
def unsubscribe_users(modeladmin, request, queryset):
    queryset.update(is_subscribed=False)



@admin.action(description="Subscribe users")
def subscribe_users(modeladmin, request, queryset):
    queryset.update(is_subscribed=True)


class CustomUserAdmin(UserAdmin):
    model = CustomUser

    actions = [unsubscribe_users, subscribe_users]

    fieldsets = (
        (None, {"fields": ("official_user_id", "username", "password", "profile_picture")}),
        (
            "Personal info",
            {"fields": ("firstname", "middle_initial", "lastname", "email", "contact_number", "date_of_birth", "gender", "useraddress",)}, 
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
                    "is_subscribed",
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

    list_display = (
        "id",
        "official_user_id",
        "firstname",
        "lastname",
        "username",
        "email",
        "active_status",
        "is_subscribed",
        "roleuser",
        "approved_date",
    )

    search_fields = (
        "official_user_id",
        "username",
        "email",
        "firstname",
        "lastname",
    )
    ordering = ("username",)
    readonly_fields = ("request_date",)



    # Prevent adding new pending users directly from admin
    def has_add_permission(self, request):
        return False
    

    def has_delete_permission(self, request, obj=None):
        return False






@admin.action(description='Disapprove selected users')
def disapprove_users(modeladmin, request, queryset):
    queryset.update(is_disapproved = True)


@admin.action(description="Approve selected users")
def approve_users(modeladmin, request, queryset):
    for pending_user in queryset: # to add filter to da admin only
        CustomUser.objects.create(
            official_user_id = pending_user.official_user_id,
            username=pending_user.username,
            password=pending_user.password,
            email=pending_user.email,
            contact_number=pending_user.contact_number,
            firstname=pending_user.firstname,
            middle_initial=pending_user.middle_initial,
            lastname=pending_user.lastname,
            date_of_birth=pending_user.date_of_birth,
            gender=pending_user.gender, 
            useraddress=pending_user.useraddress,
            roleuser = pending_user.roleuser,
            is_approved=True,
            approved_date=timezone.now(),
            approved_by=request.user,
        )
        pending_user.delete()



class PendingUserAdmin(admin.ModelAdmin):
    # model = PendingUser

    list_display = (
        "official_user_id",
        "username",
        "firstname",
        "lastname",
        "email",
        "roleuser",
        'useraddress',
        "is_pending",
        "is_disapproved",
        "request_date",
    )
    actions = [approve_users, disapprove_users]

    readonly_fields = (
        "official_user_id",
        "request_date",
        "username",
        "email",
        "contact_number",
        "firstname",
        "middle_initial",
        "lastname",
        "gender", 
        "date_of_birth",
        "useraddress",
        "roleuser",
        "is_pending",
        "is_disapproved",   
    )

    search_fields = (
        "official_user_id",
        "username",
        "email",
        "firstname",
        "lastname",
    )

    # # Prevent deletion of pending users directly from admin
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
    common_fields = (
        "reviewrating_id",
        "reviewer",
        "rating",
        "review_header",
        "rate_date",
    )

    list_display = common_fields
    search_fields = ("rating", "review_header",)
    ordering = common_fields
    readonly_fields = common_fields + ("review_body",)

    def has_delete_permission(self, request, obj=None):
        return False


class FieldAdmin(admin.ModelAdmin):
    common_fields = (
        "field_id",
        "field_name",
        "owner",
        "address",
        "created_at",
    )

    list_display = common_fields
    search_fields = ("field_name", "owner", "address",)
    ordering = common_fields
    readonly_fields = ("field_id",)
    list_filter = ("is_deleted",)

    def has_delete_permission(self, request, obj=None):
        return False



class FieldCropDataAdmin(admin.ModelAdmin):
    common_fields = (
        "fieldcrop_id",
        "field",
        "crop_planted",
        "planting_date",
    )

    list_display = common_fields
    search_fields = ("crop_planted",)
    ordering = common_fields
    list_filter = ("is_deleted",)

    def has_delete_permission(self, request, obj=None):
        return False


class FieldSoilDataAdmin(admin.ModelAdmin):
    common_fields = (
        "soil_id",
        "field",
        "nitrogen",
        "phosphorous",
        "potassium",
        "ph",
        "record_date",
    )

    list_display = common_fields
    search_fields = ("record_date",)
    ordering = common_fields
    list_filter = ("is_deleted",)

    def has_delete_permission(self, request, obj=None):
        return False


class ChatGroupAdmin(admin.ModelAdmin):
    common_fields = (
        "title",
        "user",
        "created_at",
    )

    list_display = common_fields
    search_fields = ("title",)
    ordering = common_fields
    list_filter = ("is_deleted",)

    def has_delete_permission(self, request, obj=None):
        return False


class ChatAdmin(admin.ModelAdmin):
    common_fields = (
        "chat_group",
        "user",
        "created_at",
    )

    list_display = common_fields
    search_fields = ("created_at",)
    ordering = common_fields

    def has_delete_permission(self, request, obj=None):
        return False


class ImageAnalysisAdmin(admin.ModelAdmin):
    common_fields = (
        "analysis_id",
        "owner",
        "created_at",
    )

    list_display = common_fields
    search_fields = ("owner", "created_at")
    ordering = common_fields
    # list_filter = ("is_deleted",)

    def has_delete_permission(self, request, obj=None):
        return False


class NotificationAdmin(admin.ModelAdmin):
    common_fields = (
        "id",
        "subject",
        "created_at",
        "is_read",
    )

    list_display = common_fields
    search_fields = ("subject", "created_at",)
    ordering = common_fields
    # list_filter = ("is_deleted",)

    def has_delete_permission(self, request, obj=None):
        return False
    







# to monitor agrosavvy team actions
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_time', 'content_type', 'object_repr', 'change_message')
    list_filter = ('action_time', 'user', 'content_type')
    search_fields = ('object_repr', 'change_message')
    readonly_fields = ('user', 'action_time', 'content_type', 'object_repr', 'change_message', 'object_id', 'action_flag')

    def get_model_perms(self, request):
        """
        Allow only superusers to access the log entries.
        """
        if request.user.is_superuser:
            return super().get_model_perms(request)
        return {}
    
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
    



class BannedIPAdmin(admin.ModelAdmin):
    common_fields = (
        "id",
        "ip_address",
        "created_at",
    )

    list_display = common_fields
    search_fields = ("ip_address", "created_at",)
    ordering = common_fields


class FailedLoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('username', 'ip_address', 'timestamp')
    search_fields = ('username', 'ip_address')
    list_filter = ('timestamp',)






admin.site.register(LogEntry, LogEntryAdmin)
data_wizard.register(SoilDataSFM)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(PendingUser, PendingUserAdmin)
admin.site.register(Field, FieldAdmin)
admin.site.register(ReviewRating, ReviewRatingAdmin)
admin.site.register(FieldCropData, FieldCropDataAdmin)
admin.site.register(FieldSoilData, FieldSoilDataAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(ImageAnalysis, ImageAnalysisAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(SoilDataSFM)
admin.site.register(BannedIP, BannedIPAdmin)
admin.site.register(FailedLoginAttempt, FailedLoginAttemptAdmin)



admin.site.register(ChatGroup, ChatGroupAdmin)
admin.site.register(Address)
admin.site.register(Crop)
admin.site.register(RoleUser)
admin.site.register(Barangay)
admin.site.register(Gender)
admin.site.register(UserAddress)








