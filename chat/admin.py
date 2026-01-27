from django.contrib import admin
from admin_auto_filters.filters import AutocompleteFilter
from .models import ChatRoom, Message, MessageAttachment


# Filters for admin
class ParticipantFilter(AutocompleteFilter):
    title = "Participant"
    field_name = 'participants'


class SenderFilter(AutocompleteFilter):
    title = "Sender"
    field_name = 'sender'


# MessageAttachment Admin
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'file', 'file_type', 'size', 'created_at']
    list_filter = ['file_type']
    search_fields = ['id', 'file']
    autocomplete_fields = ['message']


# Message Admin
class MessageAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ['id', 'room', 'sender', 'text', 'created_at']
    list_filter = [SenderFilter]
    search_fields = ['text', 'id']
    autocomplete_fields = ['room', 'sender']
    inlines = []  # Agar inline qilmoqchi bo'lsang MessageAttachment uchun


# ChatRoom Admin
class ChatRoomAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ['id', 'get_participants',  'created_at']
    list_filter = [ParticipantFilter]
    search_fields = ['id']
    filter_horizontal = ['participants']

    def get_participants(self, obj):
        return ", ".join([p.phone for p in obj.participants.all()])
    get_participants.short_description = "Participants"


# Register models
admin.site.register(ChatRoom, ChatRoomAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(MessageAttachment, MessageAttachmentAdmin)
