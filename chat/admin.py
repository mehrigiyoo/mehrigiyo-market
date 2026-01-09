from admin_auto_filters.filters import AutocompleteFilter

from django.contrib import admin
from .models import ChatRoom, Message, FileMessage


class OwnerFilter(AutocompleteFilter):
    title = "Owner"
    field_name = 'owner'


class AdminFilter(AutocompleteFilter):
    title = "Admin"
    field_name = 'admin'


class ClientFilter(AutocompleteFilter):
    title = "Client"
    field_name = 'client'


class DoktorFilter(AutocompleteFilter):
    title = "Doktor"
    field_name = 'doktor'


class FileMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'image', 'file', 'size', 'video', ]
    list_filter = ['video', ]
    search_fields = ['id', ]


class MessageAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ['id', 'owner', 'text', 'file_message', 'created_at', ]
    list_filter = [OwnerFilter, ]
    search_fields = ['id', 'text',]
    autocomplete_fields = ['owner', 'file_message',]


class ChatRoomAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ['id', 'admin', 'client', 'doktor', 'token', 'created_at', ]
    list_filter = [AdminFilter, ClientFilter, DoktorFilter, ]
    search_fields = ['id', 'token', ]
    autocomplete_fields = ['admin', 'client', 'doktor', ]
    filter_horizontal = ['messages', ]


admin.site.register(ChatRoom, ChatRoomAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(FileMessage, FileMessageAdmin)
