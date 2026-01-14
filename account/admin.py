from admin_auto_filters.filters import AutocompleteFilter

from django.contrib import admin
from .models import UserModel, CountyModel, RegionModel, DeliveryAddress, OfferModel, Referrals, SmsCode
from modeltranslation.admin import TabbedTranslationAdmin
from django.contrib.auth.admin import UserAdmin


class CountryFilter(AutocompleteFilter):
    title = "Country"
    field_name = 'country'


class RegionFilter(AutocompleteFilter):
    title = "Region"
    field_name = 'region'


class AddressFilter(AutocompleteFilter):
    title = "Region"
    field_name = 'address'


class UserFilter(AutocompleteFilter):
    title = "User"
    field_name = 'user'


class CustomUserAdmin(UserAdmin):
    # add_form = CustomUserCreationForm
    # form = CustomUserChangeForm
    model = UserModel
    list_display = ('username', 'email', 'address', 'language', 'theme_mode', 'specialist_doctor', 'notificationKey', 'is_staff', 'is_active',)
    list_filter = (AddressFilter, 'language', 'theme_mode', 'is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('username', 'password', 'first_name', 'last_name', 'email', 'avatar', 'address', 'language',
                'favorite_medicine', 'favorite_doctor', 'theme_mode', 'specialist_doctor')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'password1', 'password2',
                       'is_staff',
                       'is_active')}
         ),
    )
    search_fields = ('username', 'email', 'id', 'notificationKey',)
    autocomplete_fields = ['address', 'specialist_doctor']
    filter_horizontal = ['favorite_medicine', 'favorite_doctor',]
    ordering = ('username',)


class CountryAdmin(TabbedTranslationAdmin):
    list_display = ['id', 'name']
    search_fields = ['id', 'name']


class RegionAdmin(TabbedTranslationAdmin):
    list_display = ['id', 'country', 'name', 'delivery_price']
    list_filter = [CountryFilter]
    search_fields = ['id', 'name']
    autocomplete_fields = ['country']


class DeliveryAddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'region', 'full_address', 'apartment_office', 'floor', 'door_or_phone', 'instructions']
    list_filter = [UserFilter, RegionFilter]
    search_fields = ['id', 'name', 'full_address', 'apartment_office', 'floor', 'door_or_phone', 'instructions']
    autocomplete_fields = ['user', 'region']


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


admin.site.register(UserModel, CustomUserAdmin)
admin.site.register(CountyModel, CountryAdmin)
admin.site.register(RegionModel, RegionAdmin)
admin.site.register(DeliveryAddress, DeliveryAddressAdmin)
admin.site.register(OfferModel, OfferModelAdmin)
admin.site.register(Referrals, ReferralModelAdmin)
