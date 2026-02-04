import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class LiveStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for live streaming

    Features:
    - Real-time chat
    - Viewer count updates
    - Reactions
    - Stream status updates

    URL: ws://server/ws/stream/{stream_id}/
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.stream_id = self.scope['url_route']['kwargs']['stream_id']
        self.stream_group_name = f'stream_{self.stream_id}'

        # Get user from scope (JWT authentication)
        self.user = self.scope.get('user')

        # ✅ FIX: User ID ni saqlab qo'yamiz (disconnect uchun)
        self.user_id = None
        self.is_viewer_added = False  # ← Track qilish uchun

        if not self.user or not self.user.is_authenticated:
            logger.warning(f"Unauthenticated connection attempt to stream {self.stream_id}")
            await self.close()
            return

        # ✅ User ID ni saqlash
        self.user_id = self.user.id

        # Streamni DBdan olish
        stream = await self.get_stream()
        if not stream:
            logger.warning(f"Stream {self.stream_id} not found")
            await self.close()
            return

        if not stream.is_live:
            logger.info(f"Stream {self.stream_id} is not live")
            await self.close()
            return

        # Join stream group
        await self.channel_layer.group_add(
            self.stream_group_name,
            self.channel_name
        )

        await self.accept()

        # ✅ Viewer qo'shish va flag o'rnatish
        if stream.is_live:
            await self.add_viewer()
            self.is_viewer_added = True  # ← Flag
            await self.send_viewer_count()

        logger.info(f"User {self.user.id} connected to stream {self.stream_id}")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnect"""

        # ✅ FIX: User va user_id mavjudligini tekshirish
        if not hasattr(self, 'user_id') or not self.user_id:
            logger.warning(f"Disconnect without user_id for stream {self.stream_id}")
            return

        # Leave stream group
        await self.channel_layer.group_discard(
            self.stream_group_name,
            self.channel_name
        )

        # ✅ FIX: Faqat viewer qo'shilgan bo'lsa, olib tashlash
        if hasattr(self, 'is_viewer_added') and self.is_viewer_added:
            await self.remove_viewer()
            await self.send_viewer_count()
            logger.info(f"User {self.user_id} removed from stream {self.stream_id} (viewers updated)")
        else:
            logger.info(f"User {self.user_id} disconnected from stream {self.stream_id} (no viewer update)")

    async def receive(self, text_data):
        """
        Receive message from WebSocket

        Message types:
        - stream.message: Chat message
        - stream.reaction: Reaction
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'stream.message':
                await self.handle_chat_message(data)

            elif message_type == 'stream.reaction':
                await self.handle_reaction(data)

            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def handle_chat_message(self, data):
        """
        Handle chat message

        Flow:
        1. Validate message
        2. Save to database
        3. Broadcast to all viewers
        """
        message_text = data.get('message', '').strip()

        if not message_text or len(message_text) > 500:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message length'
            }))
            return

        # Check if chat enabled
        stream = await self.get_stream()

        # Faqat live stream va chat enabled bo'lsa davom etadi
        if not stream or not stream.chat_enabled or not stream.is_live:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Chat is disabled or stream ended'
            }))
            return

        # Save message to database
        chat_message = await self.save_chat_message(message_text)

        if not chat_message:
            return

        # Broadcast to all viewers in stream
        await self.channel_layer.group_send(
            self.stream_group_name,
            {
                'type': 'stream_message',
                'message_id': chat_message.id,
                'message': chat_message.message,
                'user': {
                    'id': self.user.id,
                    'phone': self.user.phone,
                    'first_name': self.user.first_name or '',
                    'avatar': self.user.avatar.url if self.user.avatar else None,
                },
                'created_at': chat_message.created_at.isoformat(),
            }
        )

    async def handle_reaction(self, data):
        """Handle reaction"""
        reaction_type = data.get('reaction_type')

        # Validate reaction type
        from .models import StreamReaction
        valid_types = [choice[0] for choice in StreamReaction.REACTION_CHOICES]

        stream = await self.get_stream()
        if not stream or not stream.is_live:
            return
        if reaction_type not in valid_types:
            return

        # Save reaction
        await self.save_reaction(reaction_type)

        # Broadcast reaction to all viewers
        await self.channel_layer.group_send(
            self.stream_group_name,
            {
                'type': 'stream_reaction',
                'reaction_type': reaction_type,
                'user_id': self.user.id,
            }
        )

    # BROADCAST HANDLERS
    async def stream_message(self, event):
        """
        Broadcast chat message to client
        """
        await self.send(text_data=json.dumps({
            'type': 'stream_message',
            'message_id': event['message_id'],
            'message': event['message'],
            'user': event['user'],
            'created_at': event['created_at'],
        }))

    async def stream_reaction(self, event):
        """
        Broadcast reaction to client
        """
        await self.send(text_data=json.dumps({
            'type': 'stream_reaction',
            'reaction_type': event['reaction_type'],
            'user_id': event['user_id'],
        }))

    async def viewer_count_update(self, event):
        """
        Broadcast viewer count update
        """
        await self.send(text_data=json.dumps({
            'type': 'viewer_count',
            'count': event['count'],
        }))

    async def stream_ended(self, event):
        """
        Notify that stream has ended
        """
        await self.send(text_data=json.dumps({
            'type': 'stream_ended',
            'duration': event.get('duration', 0),
        }))

    # DATABASE OPERATIONS
    @database_sync_to_async
    def get_stream(self):
        """Get stream object"""
        from .models import LiveStream
        try:
            return LiveStream.objects.get(id=self.stream_id)
        except LiveStream.DoesNotExist:
            return None

    @database_sync_to_async
    def save_chat_message(self, message_text):
        """Save chat message to database"""
        from .models import LiveStream, StreamChat

        try:
            stream = LiveStream.objects.get(id=self.stream_id)

            if stream.status != 'live':
                return None

            chat_message = StreamChat.objects.create(
                stream=stream,
                user=self.user,
                message=message_text
            )

            return chat_message

        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            return None

    @database_sync_to_async
    def save_reaction(self, reaction_type):
        """Save reaction to database"""
        from .models import LiveStream, StreamReaction

        try:
            stream = LiveStream.objects.get(id=self.stream_id)

            # Create or get reaction
            StreamReaction.objects.get_or_create(
                stream=stream,
                user=self.user,
                reaction_type=reaction_type
            )

        except Exception as e:
            logger.error(f"Error saving reaction: {e}")

    @database_sync_to_async
    def add_viewer(self):
        """Add viewer to stream"""
        from .models import LiveStream, StreamViewer

        try:
            stream = LiveStream.objects.get(id=self.stream_id)
            stream.add_viewer(self.user_id)

            # Create viewer record
            StreamViewer.objects.get_or_create(
                stream=stream,
                user=self.user,
                left_at__isnull=True,
                defaults={'device_type': 'web'}
            )

            logger.info(f"Viewer added: user_id={self.user_id}, stream_id={self.stream_id}")

        except Exception as e:
            logger.error(f"Error adding viewer: {e}")

    @database_sync_to_async
    def remove_viewer(self):
        """Remove viewer from stream"""
        from .models import LiveStream, StreamViewer
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()

        try:
            stream = LiveStream.objects.get(id=self.stream_id)

            # ✅ FIX: user_id orqali olib tashlash (self.user emas!)
            stream.remove_viewer(self.user_id)

            # ✅ User obyektini olish
            try:
                user = UserModel.objects.get(id=self.user_id)
            except UserModel.DoesNotExist:
                logger.error(f"User {self.user_id} not found")
                return

            # Update viewer record
            viewer = StreamViewer.objects.filter(
                stream=stream,
                user=user,
                left_at__isnull=True
            ).first()

            if viewer:
                viewer.left_at = timezone.now()
                viewer.calculate_watch_duration()
                logger.info(
                    f"Viewer removed: user_id={self.user_id}, stream_id={self.stream_id}, duration={viewer.watch_duration}s")
            else:
                logger.warning(f"Active viewer record not found: user_id={self.user_id}, stream_id={self.stream_id}")

        except Exception as e:
            logger.error(f"Error removing viewer: {e}")

    @database_sync_to_async
    def get_viewer_count(self):
        """Get current viewer count"""
        from .models import LiveStream

        try:
            stream = LiveStream.objects.get(id=self.stream_id)
            count = stream.get_active_viewers()
            logger.debug(f"Stream {self.stream_id} viewer count: {count}")
            return count
        except Exception as e:
            logger.error(f"Error getting viewer count: {e}")
            return 0

    async def send_viewer_count(self):
        """Send viewer count to all in group"""
        count = await self.get_viewer_count()

        await self.channel_layer.group_send(
            self.stream_group_name,
            {
                'type': 'viewer_count_update',
                'count': count,
            }
        )