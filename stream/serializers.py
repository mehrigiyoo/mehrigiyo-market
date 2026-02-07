from rest_framework import serializers
from .models import LiveStream, StreamViewer, StreamChat, StreamReaction
from account.models import UserModel


class StreamUserMiniSerializer(serializers.ModelSerializer):
    """
    Minimal user info for streams

     Keys saqlanadi: first_name, last_name
     Value full_name dan olinadi
    """
    avatar = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = ['id', 'phone', 'first_name', 'last_name', 'role', 'avatar']

    def _get_user_full_name(self, user):
        """
        User ning to'liq ismini olish

        Priority:
        - Client: client_profile.full_name
        - Doctor: doctor.full_name
        - Fallback: phone
        """
        # Client
        if hasattr(user, 'client_profile'):
            try:
                full_name = (user.client_profile.full_name or '').strip()
                if full_name:
                    return full_name
            except:
                pass

        # Doctor
        if hasattr(user, 'doctor'):
            try:
                full_name = (user.doctor.full_name or '').strip()
                if full_name:
                    return full_name
            except:
                pass

        # Fallback
        return user.phone or ''

    def get_first_name(self, obj):
        return self._get_user_full_name(obj)

    def get_last_name(self, obj):
        return ''

    def get_avatar(self, obj):
        """Avatar with absolute URL"""
        if hasattr(obj, 'avatar') and obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None


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