from django.contrib import admin
from .models import Call, CallEvent


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'call_type', 'status', 'caller', 'receiver',
        'duration', 'formatted_duration', 'created_at'
    ]
    list_filter = ['call_type', 'status', 'created_at']
    search_fields = ['caller__phone', 'receiver__phone', 'livekit_room_name']
    readonly_fields = [
        'livekit_room_name', 'duration', 'formatted_duration',
        'created_at', 'initiated_at', 'ringing_at', 'answered_at', 'ended_at'
    ]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Call Info', {
            'fields': ('call_type', 'status', 'room')
        }),
        ('Participants', {
            'fields': ('caller', 'receiver')
        }),
        ('LiveKit', {
            'fields': ('livekit_room_name',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'initiated_at', 'ringing_at',
                'answered_at', 'ended_at'
            )
        }),
        ('Metrics', {
            'fields': ('duration', 'formatted_duration', 'quality_score')
        }),
        ('Recording', {
            'fields': ('recording_enabled', 'recording_url'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CallEvent)
class CallEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'call', 'event_type', 'user', 'timestamp']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['call__id', 'user__phone']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'