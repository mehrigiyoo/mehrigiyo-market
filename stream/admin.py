from django.contrib import admin
from .models import LiveStream, StreamViewer, StreamChat, StreamReaction


@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'host', 'status', 'viewer_count',
        'peak_viewers', 'duration', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'recording_enabled']
    search_fields = ['title', 'host__phone', 'host__first_name']
    readonly_fields = [
        'livekit_room_name', 'viewer_count', 'peak_viewers',
        'total_views', 'duration', 'created_at', 'started_at', 'ended_at'
    ]

    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'host', 'status', 'thumbnail')
        }),
        ('LiveKit', {
            'fields': ('livekit_room_name',)
        }),
        ('Schedule', {
            'fields': ('scheduled_at', 'started_at', 'ended_at', 'duration')
        }),
        ('Metrics', {
            'fields': ('viewer_count', 'peak_viewers', 'total_views')
        }),
        ('Settings', {
            'fields': ('recording_enabled', 'recording_url', 'chat_enabled', 'reactions_enabled')
        }),
    )


@admin.register(StreamViewer)
class StreamViewerAdmin(admin.ModelAdmin):
    list_display = ['id', 'stream', 'user', 'joined_at', 'watch_duration']
    list_filter = ['joined_at']
    search_fields = ['stream__title', 'user__phone']
    readonly_fields = ['joined_at', 'watch_duration']


@admin.register(StreamChat)
class StreamChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'stream', 'user', 'message_preview', 'created_at', 'is_deleted']
    list_filter = ['created_at', 'is_pinned', 'is_deleted']
    search_fields = ['message', 'user__phone', 'stream__title']
    readonly_fields = ['created_at']

    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message

    message_preview.short_description = 'Message'


@admin.register(StreamReaction)
class StreamReactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'stream', 'user', 'reaction_type', 'created_at']
    list_filter = ['reaction_type', 'created_at']
    search_fields = ['stream__title', 'user__phone']
    readonly_fields = ['created_at']