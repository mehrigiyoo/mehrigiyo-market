from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin
from django import forms
from modeltranslation.admin import TabbedTranslationAdmin
from .models import Doctor, TypeDoctor, RateDoctor, AdviceTime, Advertising, DoctorView, DoctorVerification, \
    DoctorRating


class TypeDoctorFilter(AutocompleteFilter):
    title = "Type doctor"
    field_name = 'type_doctor'


class ClientFilter(AutocompleteFilter):
    title = "Client"
    field_name = 'client'


class DoctorFilter(AutocompleteFilter):
    title = "Doctor"
    field_name = 'doctor'


class TypeDoctorAdmin(TabbedTranslationAdmin):
    list_display = ('id', 'name', 'image', )
    search_fields = ['id', 'name', ]

@admin.register(RateDoctor)
class RateDoctorAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'client', 'rate', 'feedback', 'created_at')
    list_filter = ('rate', 'feedback')
    search_fields = ('doctor__full_name', 'client__username')

@admin.register(DoctorRating)
class DoctorRatingAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('doctor__full_name', 'user__phone')

@admin.register(DoctorView)
class DoctorViewAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'user', 'created_at')


@admin.register(DoctorVerification)
class DoctorVerificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'doctor', 'status', 'created_at']
    list_filter = ['status']

    fieldsets = (
        ('Doctor', {
            'fields': ('doctor',)
        }),
        ('Documents', {
            'fields': ('diploma', 'license_number', 'license_expire_date', 'workplace')
        }),
        ('Verification', {
            'fields': ('status', 'admin_comment')
        }),
    )

    actions = ['approve_verifications']

    def approve_verifications(self, request, queryset):
        """
        Approve doctor verifications

        This also approves the Doctor
        """
        count = 0
        for verification in queryset:
            verification.status = 'approved'
            verification.save()

            # Approve doctor
            doctor = verification.doctor
            doctor.is_verified = True
            doctor.save()

            # Approve user
            doctor.user.is_approved = True
            doctor.user.save()

            count += 1

        self.message_user(request, f"{count} verifications approved")

    approve_verifications.short_description = "✅ Approve verifications"




@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'full_name', 'type_doctor',
        'consultation_price_display',  # ← Show price
        'is_verified',  # ← Approval status
        'created_at'
    ]

    list_filter = ['is_verified', 'type_doctor', 'gender']
    search_fields = ['full_name', 'user__phone']

    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'full_name', 'gender', 'birthday')
        }),
        ('Professional', {
            'fields': ('type_doctor', 'experience', 'description', 'image')
        }),
        ('Consultation', {
            'fields': ('consultation_price', 'is_verified', 'top'),  # ← Admin sets price here
            'description': 'Admin sets consultation price and approves doctor'
        }),
        ('Stats', {
            'fields': ('average_rating', 'rating_count', 'view_count'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['average_rating', 'rating_count', 'view_count', 'created_at']

    def consultation_price_display(self, obj):
        return f"{obj.consultation_price:,.0f} so'm"

    consultation_price_display.short_description = 'Price'

    actions = ['approve_doctors', 'reject_doctors']

    def approve_doctors(self, request, queryset):
        """
        Approve selected doctors

        Admin workflow:
        1. Review doctor verification
        2. Set consultation_price (if needed)
        3. Click "Approve doctors"
        """
        count = queryset.update(is_verified=True)

        # Also update UserModel
        for doctor in queryset:
            doctor.user.is_approved = True
            doctor.user.save()

        self.message_user(request, f"{count} doctors approved")

    approve_doctors.short_description = " Approve selected doctors"

    def reject_doctors(self, request, queryset):
        """Reject doctors"""
        count = queryset.update(is_verified=False)

        for doctor in queryset:
            doctor.user.is_approved = False
            doctor.user.save()

        self.message_user(request, f"{count} doctors rejected")

    reject_doctors.short_description = "❌ Reject selected doctors"


# @admin.register(Doctor)
# class DoctorAdmin(admin.ModelAdmin):
#     form = DoctorAdminForm
#
#     list_display = (
#         'full_name',
#         'type_doctor',
#         'consultation_price_display',
#         'is_verified',
#         'user_is_approved',
#     )
#
#     list_filter = ('is_verified',)
#     search_fields = ('full_name', 'user__phone')
#     readonly_fields = ('created_at',)
#
#     def user_is_approved(self, obj):
#         return obj.user.is_approved
#     user_is_approved.boolean = True
#     user_is_approved.short_description = "Approved"
#
#     def save_model(self, request, obj, form, change):
#         super().save_model(request, obj, form, change)
#
#         if obj.user:
#             obj.user.is_approved = form.cleaned_data.get('is_approved', False)
#             obj.user.is_active = obj.user.is_approved
#             obj.user.save()

class AdviceTimeAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_time'
    list_display = ['id', 'doctor', 'client', 'start_time', 'end_time' ]
    list_filter = [DoctorFilter, ClientFilter,]
    search_fields = ['id', ]
    autocomplete_fields = ['client', 'doctor', ]


class AdvertisingAdmin(admin.ModelAdmin):
    list_display = ['id', 'doctor', 'title', 'text', 'image', ]
    list_filter = [DoctorFilter, ]
    search_fields = ['id', 'title', 'text', ]


admin.site.register(TypeDoctor, TypeDoctorAdmin)
admin.site.register(AdviceTime, AdviceTimeAdmin)
admin.site.register(Advertising, AdvertisingAdmin)
