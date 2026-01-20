from django.contrib import admin

from client.models import ClientProfile


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'gender', 'birthday')
    search_fields = ('full_name', 'user__phone')
    list_filter = ('gender',)