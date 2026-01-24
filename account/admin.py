from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin
from .models import CountyModel, RegionModel, OfferModel, Referrals, SmsCode
from modeltranslation.admin import TabbedTranslationAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from account.models import UserModel


class CountryFilter(AutocompleteFilter):
    title = "Country"
    field_name = 'country'


class RegionFilter(AutocompleteFilter):
    title = "Region"
    field_name = 'region'

# class AddressFilter(AutocompleteFilter):
#     title = "Region"
#     field_name = 'region'

class UserFilter(AutocompleteFilter):
    title = "User"
    field_name = 'user'


@admin.register(UserModel)
class CustomUserAdmin(BaseUserAdmin):
    model = UserModel
    list_display = ('phone','role','language','theme_mode','is_staff','is_active')
    list_filter = ('role','language','theme_mode','is_staff','is_active')
    search_fields = ('phone','email','id')
    ordering = ('phone',)
    filter_horizontal = ['favorite_medicine',]

    fieldsets = (
        (None, {'fields': ('phone','email','avatar','language','theme_mode','favorite_medicine', 'is_approved')}),
        ('Permissions', {'fields': ('is_staff','is_active','is_superuser')}),
    )
    add_fieldsets = (
        (None, {'classes':('wide',),
                'fields':('phone','password1','password2','is_staff', 'is_active', 'is_approved')}),
    )

    def save_model(self, request, obj, form, change):
        if not change and obj.role in [UserModel.Roles.DOCTOR, UserModel.Roles.OPERATOR]:
            obj.set_unusable_password()
            obj.is_active = False
        super().save_model(request, obj, form, change)


class CountryAdmin(TabbedTranslationAdmin):
    list_display = ['id', 'name']
    search_fields = ['id', 'name']


class RegionAdmin(TabbedTranslationAdmin):
    list_display = ['id', 'country', 'name', 'delivery_price']
    list_filter = [CountryFilter]
    search_fields = ['id', 'name']
    autocomplete_fields = ['country']


class OfferModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'phone_number', 'offer']
    search_fields = ['id', 'name', 'email', 'phone_number', 'offer']


class ReferralModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'invited_user']

@admin.register(SmsCode)
class SmsCodeAdmin(admin.ModelAdmin):
    list_display = (
        'phone',
        'code',
        'ip',
        'confirmed',
        'expire_at',
    )

    list_filter = (
        'confirmed',
        'expire_at',
    )

    search_fields = (
        'phone',
        'code',
        'ip',
    )

    readonly_fields = (
        'phone',
        'code',
        'ip',
        'expire_at',
    )

    ordering = ('-expire_at',)

    list_per_page = 25


admin.site.register(CountyModel, CountryAdmin)
admin.site.register(RegionModel, RegionAdmin)
admin.site.register(OfferModel, OfferModelAdmin)
admin.site.register(Referrals, ReferralModelAdmin)
