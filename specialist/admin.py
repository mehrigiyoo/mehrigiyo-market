from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin
from .models import Doctor, TypeDoctor, RateDoctor, AdviceTime, Advertising


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


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'type_doctor', 'is_verified')
    readonly_fields = ('created_at', 'user')
    search_fields = ('full_name', 'user__phone')


class RateDoctorAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ['id', 'client', 'doctor', 'rate', 'feedback', 'created_at', ]
    list_filter = [ClientFilter, DoctorFilter, 'rate', ]
    search_fields = ['id', 'feedback', ]
    autocomplete_fields = ['client', 'doctor', ]


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
admin.site.register(RateDoctor, RateDoctorAdmin)
admin.site.register(AdviceTime, AdviceTimeAdmin)
admin.site.register(Advertising, AdvertisingAdmin)
