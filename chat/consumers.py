import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.conf import settings
from .models import ChatRoom, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        # Anonymous user reject
        if self.user.is_anonymous:
            await self.close(code=4001)
            return

        # Room access tekshirish
        has_access = await self.check_room_access()
        if not has_access:
            await self.close(code=4003)
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # ✅ CHAT HISTORY YUBORISH
        await self.send_chat_history()

        # User online status
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'status': 'online'
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # User offline status
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'status': 'offline'
                }
            )

            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)
        elif message_type == 'read_receipt':
            await self.handle_read_receipt(data)
        elif message_type == 'load_more':
            await self.handle_load_more(data)

    async def handle_chat_message(self, data):
        """Yangi xabar yuborish"""
        text = data.get('text', '')
        reply_to_id = data.get('reply_to')

        # Message saqlash
        message = await self.save_message(text, reply_to_id)

        if message:
            # Serialize message
            message_data = await self.serialize_message(message)

            # Broadcast to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_handler',
                    'message': message_data
                }
            )

    async def handle_typing(self, data):
        """Typing indicator"""
        is_typing = data.get('is_typing', False)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_handler',
                'user_id': self.user.id,
                'is_typing': is_typing
            }
        )

    async def handle_read_receipt(self, data):
        """Xabar o'qilganini belgilash"""
        message_id = data.get('message_id')

        if message_id:
            await self.mark_message_read(message_id)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt_handler',
                    'message_id': message_id,
                    'user_id': self.user.id
                }
            )

    async def send_chat_history(self):
        """Oxirgi 50 ta xabarni yuborish"""
        messages = await self.get_recent_messages(limit=50)
        has_more = await self.has_more_messages()

        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': messages,
            'has_more': has_more
        }))

    async def handle_load_more(self, data):
        """Ko'proq xabarlar yuklash"""
        before_id = data.get('before_id')
        limit = data.get('limit', 50)

        messages = await self.get_messages_before(before_id, limit)
        has_more = await self.has_messages_before(before_id, limit)

        await self.send(text_data=json.dumps({
            'type': 'load_more_response',
            'messages': messages,
            'has_more': has_more
        }))

    # Event handlers
    async def chat_message_handler(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def typing_handler(self, event):
        # O'ziga typing yubormaslik
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'is_typing': event['is_typing']
            }))

    async def read_receipt_handler(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id']
        }))

    async def user_status(self, event):
        # O'ziga status yubormaslik
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'user_id': event['user_id'],
                'status': event['status']
            }))

    # Database operations
    @database_sync_to_async
    def check_room_access(self):
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return room.participants.filter(id=self.user.id).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, text, reply_to_id=None):
        try:
            room = ChatRoom.objects.get(id=self.room_id)

            reply_to = None
            if reply_to_id:
                try:
                    reply_to = Message.objects.get(id=reply_to_id, room=room)
                except Message.DoesNotExist:
                    pass

            message = Message.objects.create(
                room=room,
                sender=self.user,
                text=text,
                message_type='text',
                reply_to=reply_to
            )
            return message
        except Exception as e:
            print(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def serialize_message(self, message):
        """Message obyektini dict ga aylantirish (ABSOLUTE URLs)"""
        return self._message_to_dict(message)

    def _get_base_url(self):
        """Base URL olish (settings dan yoki default)"""
        # settings.py da SITE_URL mavjud bo'lsa
        if hasattr(settings, 'SITE_URL'):
            return settings.SITE_URL

        # Yoki scope dan olish
        headers = dict(self.scope.get('headers', []))
        host = headers.get(b'host', b'localhost:8000').decode()

        # Protocol aniqlash
        is_secure = self.scope.get('scheme') == 'https'
        protocol = 'https' if is_secure else 'http'

        return f'{protocol}://{host}'

    def _message_to_dict(self, message):
        """
        Message obyektini dict ga aylantirish
        ✅ ABSOLUTE URLs bilan
        """
        base_url = self._get_base_url()

        data = {
            'id': message.id,
            'room': message.room.id,
            'sender': {
                'id': message.sender.id,
                'phone': message.sender.phone,
                'first_name': message.sender.first_name or '',
                'last_name': message.sender.last_name or '',
                'role': message.sender.role,
            },
            'message_type': message.message_type,
            'text': message.text,
            'is_read': message.is_read,
            'read_at': message.read_at.isoformat() if message.read_at else None,
            'created_at': message.created_at.isoformat(),
            'updated_at': message.updated_at.isoformat(),
            'is_mine': message.sender.id == self.user.id,
            'attachments': [],
            'reply_to': None
        }

        # ✅ Attachments with ABSOLUTE URLs
        for att in message.attachments.all():
            file_url = None
            thumbnail_url = None

            if att.file:
                file_url = f"{base_url}{att.file.url}"

            if att.thumbnail:
                thumbnail_url = f"{base_url}{att.thumbnail.url}"

            data['attachments'].append({
                'id': att.id,
                'file_type': att.file_type,
                'file_name': att.file_name,
                'size': att.size,
                'duration': att.duration,
                'file_url': file_url,
                'thumbnail_url': thumbnail_url,
            })

        # Reply to
        if message.reply_to:
            data['reply_to'] = {
                'id': message.reply_to.id,
                'sender': {
                    'id': message.reply_to.sender.id,
                    'phone': message.reply_to.sender.phone,
                    'first_name': message.reply_to.sender.first_name or '',
                },
                'text': message.reply_to.text[:100] if message.reply_to.text else '',
                'message_type': message.reply_to.message_type,
            }

        return data

    @database_sync_to_async
    def get_recent_messages(self, limit=50):
        """Oxirgi xabarlarni olish"""
        messages = Message.objects.filter(
            room_id=self.room_id
        ).select_related(
            'sender', 'reply_to__sender'
        ).prefetch_related(
            'attachments'
        ).order_by('-created_at')[:limit]

        # Reverse (eskidan yangiga)
        messages = list(reversed(messages))

        # Manual serialization
        return [self._message_to_dict(msg) for msg in messages]

    @database_sync_to_async
    def has_more_messages(self):
        """Qo'shimcha xabarlar bormi"""
        count = Message.objects.filter(room_id=self.room_id).count()
        return count > 50

    @database_sync_to_async
    def get_messages_before(self, before_id, limit=50):
        """before_id dan oldingi xabarlar"""
        messages = Message.objects.filter(
            room_id=self.room_id,
            id__lt=before_id
        ).select_related(
            'sender', 'reply_to__sender'
        ).prefetch_related(
            'attachments'
        ).order_by('-created_at')[:limit]

        messages = list(reversed(messages))
        return [self._message_to_dict(msg) for msg in messages]

    @database_sync_to_async
    def has_messages_before(self, before_id, limit=50):
        """Yana xabarlar bormi"""
        count = Message.objects.filter(
            room_id=self.room_id,
            id__lt=before_id
        ).count()
        return count > limit

    @database_sync_to_async
    def mark_message_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id, room_id=self.room_id)
            if message.sender != self.user and not message.is_read:
                message.is_read = True
                message.read_at = timezone.now()
                message.save(update_fields=['is_read', 'read_at'])
                return True
        except Message.DoesNotExist:
            pass
        return False