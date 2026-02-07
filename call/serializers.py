from rest_framework import serializers
from .models import Call, CallEvent
from account.models import UserModel
from chat.models import ChatRoom


class CallUserMiniSerializer(serializers.ModelSerializer):
    """
    Minimal user info for calls

    ✅ Keys saqlanadi: first_name, last_name
    ✅ Value full_name dan olinadi
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
        """
        ✅ Key: first_name (o'zgarmaydi)
        ✅ Value: full_name (profile dan)
        """
        return self._get_user_full_name(obj)

    def get_last_name(self, obj):
        """
        ✅ Key: last_name (o'zgarmaydi)
        ✅ Value: bo'sh string
        """
        return ''

    def get_avatar(self, obj):
        if hasattr(obj, 'avatar') and obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None


class CallEventSerializer(serializers.ModelSerializer):
    """Call event serializer"""
    user = CallUserMiniSerializer(read_only=True)

    class Meta:
        model = CallEvent
        fields = ['id', 'event_type', 'user', 'timestamp', 'metadata']


class CallSerializer(serializers.ModelSerializer):
    """Call detail serializer"""
    caller = CallUserMiniSerializer(read_only=True)
    receiver = CallUserMiniSerializer(read_only=True)
    formatted_duration = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    events = CallEventSerializer(many=True, read_only=True)

    class Meta:
        model = Call
        fields = [
            'id', 'room', 'call_type', 'status',
            'caller', 'receiver', 'livekit_room_name',
            'created_at', 'initiated_at', 'ringing_at',
            'answered_at', 'ended_at',
            'duration', 'formatted_duration', 'quality_score',
            'recording_enabled', 'recording_url',
            'is_active', 'events'
        ]
        read_only_fields = ['livekit_room_name', 'duration', 'created_at']


class CallListSerializer(serializers.ModelSerializer):
    """Call list serializer (lighter)"""
    caller = CallUserMiniSerializer(read_only=True)
    receiver = CallUserMiniSerializer(read_only=True)
    formatted_duration = serializers.ReadOnlyField()

    class Meta:
        model = Call
        fields = [
            'id', 'call_type', 'status',
            'caller', 'receiver',
            'created_at', 'duration', 'formatted_duration'
        ]


class CallInitiateSerializer(serializers.Serializer):
    """Initiate call request"""
    room_id = serializers.IntegerField()
    call_type = serializers.ChoiceField(choices=['audio', 'video'])

    def validate_room_id(self, value):
        try:
            room = ChatRoom.objects.get(id=value)
        except ChatRoom.DoesNotExist:
            raise serializers.ValidationError("Chat room topilmadi")

        # Access check
        user = self.context['request'].user
        if not room.participants.filter(id=user.id).exists():
            raise serializers.ValidationError("Sizda bu roomga kirish huquqi yo'q")

        return value

    def validate(self, data):
        room_id = data['room_id']
        room = ChatRoom.objects.get(id=room_id)

        # Check if there's already an active call
        active_call = Call.objects.filter(
            room=room,
            status__in=['initiated', 'ringing', 'answered']
        ).first()

        if active_call:
            raise serializers.ValidationError(
                "Bu roomda allaqachon active call mavjud"
            )

        return data


class CallResponseSerializer(serializers.Serializer):
    """Call response (answer/reject)"""
    action = serializers.ChoiceField(choices=['answer', 'reject'])