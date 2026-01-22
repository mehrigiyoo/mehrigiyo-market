from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin
from django import forms
from modeltranslation.admin import TabbedTranslationAdmin
from .models import Doctor, TypeDoctor, RateDoctor, AdviceTime, Advertising, DoctorView


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

class DoctorAdminForm(forms.ModelForm):
    phone = forms.CharField(max_length=20, disabled=True)
    is_approved = forms.BooleanField(required=False)

    class Meta:
        model = Doctor
        exclude = ('user',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk and self.instance.user:
            self.fields['phone'].initial = self.instance.user.phone
            self.fields['is_approved'].initial = self.instance.user.is_approved

@admin.register(RateDoctor)
class RateDoctorAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'user', 'rate', 'feedback', 'created_at')
    list_filter = ('rate', 'feedback')
    search_fields = ('doctor__full_name', 'user__username')

@admin.register(DoctorView)
class DoctorViewAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'user', 'created_at')


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    form = DoctorAdminForm

    list_display = (
        'full_name',
        'type_doctor',
        'is_verified',
        'user_is_approved',
    )

    list_filter = ('is_verified',)
    search_fields = ('full_name', 'user__phone')
    readonly_fields = ('created_at',)

    def user_is_approved(self, obj):
        return obj.user.is_approved
    user_is_approved.boolean = True
    user_is_approved.short_description = "Approved"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.user:
            obj.user.is_approved = form.cleaned_data.get('is_approved', False)
            obj.user.is_active = obj.user.is_approved
            obj.user.save()

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
