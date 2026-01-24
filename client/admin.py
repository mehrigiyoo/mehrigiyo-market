from django.contrib import admin
from client.models import ClientProfile, ClientAddress


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'gender', 'birthday')
    search_fields = ('full_name', 'user__phone')
    list_filter = ('gender',)


@admin.register(ClientAddress)
class ClientAddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'address_line', 'is_default', 'is_active']
    search_fields = ['address_line', 'user__username', 'user__phone']
    autocomplete_fields = ['user']  # field nomi, model nomi emas
