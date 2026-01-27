from rest_framework import serializers
from .models import ChatRoom, Message, MessageAttachment
from account.models import UserModel


class UserMiniSerializer(serializers.ModelSerializer):
    """User minimal ma'lumoti"""
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = ['id', 'phone', 'first_name', 'last_name', 'avatar', 'role']

    def get_avatar(self, obj):
        # Sizning user modelingizda avatar fieldi bo'lsa
        # if hasattr(obj, 'avatar') and obj.avatar:
        #     request = self.context.get('request')
        #     if request:
        #         return request.build_absolute_uri(obj.avatar.url)
        # return None

        if hasattr(obj, 'avatar') and obj.avatar:
            return obj.avatar.url  # /media/avatars/1.png kabi
        return None


class MessageAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = MessageAttachment
        fields = ['id', 'file_type', 'file_name', 'size', 'duration', 'file_url', 'thumbnail_url', 'created_at']

    def get_file_url(self, obj):
        # request = self.context.get('request')
        # if obj.file and request:
        #     return request.build_absolute_uri(obj.file.url)
        # return None

        if obj.file:
            return obj.file.url
        return None


    # def get_thumbnail_url(self, obj):
    #     request = self.context.get('request')
    #     if obj.thumbnail and request:
    #         return request.build_absolute_uri(obj.thumbnail.url)
    #     return None

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return None


class MessageSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    reply_to = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'room', 'sender', 'message_type', 'text',
            'is_read', 'read_at', 'created_at', 'updated_at',
            'attachments', 'reply_to', 'is_mine'
        ]
        read_only_fields = ['sender', 'is_read', 'read_at', 'created_at', 'updated_at']

    def get_reply_to(self, obj):
        if obj.reply_to:
            return {
                'id': obj.reply_to.id,
                'sender': UserMiniSerializer(obj.reply_to.sender, context=self.context).data,
                'text': obj.reply_to.text[:100],
                'message_type': obj.reply_to.message_type,
            }
        return None

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.sender.id == request.user.id
        return False


# Mavjud MessageCreateSerializer ni yangilash
class MessageCreateSerializer(serializers.ModelSerializer):
    """Message yaratish uchun (text va files)"""
    attachments = serializers.ListField(
        child=serializers.FileField(max_length=100000, allow_empty_file=False),
        required=False,
        write_only=True
    )

    class Meta:
        model = Message
        fields = ['room', 'text', 'message_type', 'reply_to', 'attachments']

    def validate(self, data):
        # Text yoki attachment bo'lishi kerak
        if not data.get('text') and not data.get('attachments'):
            raise serializers.ValidationError("Text yoki attachment yuborish kerak")

        # Room access tekshirish
        room = data.get('room')
        user = self.context['request'].user
        if not room.participants.filter(id=user.id).exists():
            raise serializers.ValidationError("Sizda bu chatga kirish huquqi yo'q")

        # File size validation
        attachments = data.get('attachments', [])
        for file in attachments:
            file_type = self._get_file_type(file.name)
            max_size = self._get_max_size(file_type)

            if file.size > max_size:
                raise serializers.ValidationError(
                    f"{file_type} maksimal hajmi {max_size / 1024 / 1024:.0f}MB"
                )

        return data

    def create(self, validated_data):
        attachments_data = validated_data.pop('attachments', [])
        validated_data['sender'] = self.context['request'].user

        # Auto-detect message_type
        if attachments_data and not validated_data.get('text'):
            validated_data['message_type'] = self._get_file_type(attachments_data[0].name)

        message = Message.objects.create(**validated_data)

        # Attachmentlarni saqlash
        for file in attachments_data:
            file_type = self._get_file_type(file.name)
            MessageAttachment.objects.create(
                message=message,
                file=file,
                file_type=file_type,
                file_name=file.name,
                size=file.size
            )

        return message

    def _get_file_type(self, filename):
        """Fayl turini aniqlash"""
        ext = filename.lower().split('.')[-1]
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
            return 'image'
        elif ext in ['mp4', 'avi', 'mov', 'wmv', 'mkv', 'flv']:
            return 'video'
        elif ext in ['mp3', 'wav', 'ogg', 'm4a', 'aac', 'flac']:
            return 'audio'
        else:
            return 'file'

    def _get_max_size(self, file_type):
        """Maksimal fayl hajmi (bytes)"""
        sizes = {
            'image': 5 * 1024 * 1024,  # 5 MB
            'video': 50 * 1024 * 1024,  # 50 MB
            'audio': 10 * 1024 * 1024,  # 10 MB
            'file': 20 * 1024 * 1024,  # 20 MB
        }
        return sizes.get(file_type, 20 * 1024 * 1024)

class ChatRoomSerializer(serializers.ModelSerializer):
    participants = UserMiniSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_type', 'participants', 'created_at', 'updated_at',
            'last_message', 'unread_count', 'other_user'
        ]

    def get_last_message(self, obj):
        last_msg = obj.messages.select_related('sender').prefetch_related('attachments').last()
        if last_msg:
            return MessageSerializer(last_msg, context=self.context).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.get_unread_count(request.user)
        return 0

    def get_other_user(self, obj):
        """1:1 chat uchun qarshi taraf"""
        request = self.context.get('request')
        if request and request.user and obj.room_type == '1:1':
            other = obj.get_other_participant(request.user)
            if other:
                return UserMiniSerializer(other, context=self.context).data
        return None


class ChatRoomCreateSerializer(serializers.Serializer):
    """1:1 chat yaratish/olish"""
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        try:
            user = UserModel.objects.get(id=value)
        except UserModel.DoesNotExist:
            raise serializers.ValidationError("User topilmadi")

        # O'zi bilan chat yaratishni taqiqlash
        if self.context['request'].user.id == value:
            raise serializers.ValidationError("O'zingiz bilan chat yarata olmaysiz")

        return value

    def create(self, validated_data):
        current_user = self.context['request'].user  # Client
        other_user = UserModel.objects.get(id=validated_data['user_id'])  # Doctor

        # Oldingi room borligini tekshiradi
        room, created = ChatRoom.get_or_create_private_room(current_user, other_user)
        return room
