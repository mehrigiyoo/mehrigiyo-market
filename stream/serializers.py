from rest_framework import serializers
from .models import LiveStream, StreamViewer, StreamChat, StreamReaction
from account.models import UserModel


class StreamUserMiniSerializer(serializers.ModelSerializer):
    """Minimal user info"""

    class Meta:
        model = UserModel
        fields = ['id', 'phone', 'first_name', 'last_name', 'role', 'avatar']


class LiveStreamSerializer(serializers.ModelSerializer):
    """Complete stream serializer"""
    host = StreamUserMiniSerializer(read_only=True)
    is_live = serializers.SerializerMethodField()
    active_viewers = serializers.SerializerMethodField()

    class Meta:
        model = LiveStream
        fields = [
            'id', 'title', 'description', 'host', 'status',
            'livekit_room_name', 'created_at', 'started_at', 'ended_at',
            'scheduled_at', 'duration', 'viewer_count', 'peak_viewers',
            'total_views', 'recording_enabled', 'recording_url',
            'thumbnail', 'chat_enabled', 'reactions_enabled',
            'is_live', 'active_viewers'
        ]
        read_only_fields = [
            'livekit_room_name', 'viewer_count', 'peak_viewers',
            'total_views', 'duration'
        ]

    def get_is_live(self, obj):
        return obj.status == 'live'

    def get_active_viewers(self, obj):
        return obj.get_active_viewers()


class LiveStreamListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views"""
    host = StreamUserMiniSerializer(read_only=True)
    active_viewers = serializers.SerializerMethodField()

    class Meta:
        model = LiveStream
        fields = [
            'id', 'title', 'host', 'status', 'thumbnail',
            'viewer_count', 'created_at', 'duration', 'active_viewers'
        ]

    def get_active_viewers(self, obj):
        return obj.get_active_viewers()


class LiveStreamCreateSerializer(serializers.ModelSerializer):
    """Create stream serializer"""

    class Meta:
        model = LiveStream
        fields = [
            'title', 'description', 'scheduled_at',
            'recording_enabled', 'thumbnail', 'chat_enabled',
            'reactions_enabled'
        ]


class StreamChatSerializer(serializers.ModelSerializer):
    """Chat message serializer"""
    user = StreamUserMiniSerializer(read_only=True)

    class Meta:
        model = StreamChat
        fields = [
            'id', 'user', 'message', 'created_at',
            'is_pinned', 'is_deleted'
        ]
        read_only_fields = ['user', 'created_at']


class StreamReactionSerializer(serializers.ModelSerializer):
    """Reaction serializer"""
    user = StreamUserMiniSerializer(read_only=True)

    class Meta:
        model = StreamReaction
        fields = ['id', 'user', 'reaction_type', 'created_at']
        read_only_fields = ['user', 'created_at']


class StreamViewerSerializer(serializers.ModelSerializer):
    """Viewer serializer"""
    user = StreamUserMiniSerializer(read_only=True)

    class Meta:
        model = StreamViewer
        fields = [
            'id', 'user', 'joined_at', 'left_at',
            'watch_duration'
        ]