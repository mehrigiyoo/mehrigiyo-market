# chat/consumers.py
import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from chat.models import ChatRoom, Message, MessageAttachment

# Role + participation check
def can_participate(user, room):
    if not user or not user.is_authenticated:
        return False
    if user.role == 'operator':
        return True
    if user.role in ['doctor', 'client']:
        return user in room.participants.all()
    return False

# Chat Consumer
class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        # 1. User headers dan middleware orqali olingan
        self.user = self.scope.get('user', None)
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # 2. Room id
        self.room_id = self.scope['url_route']['kwargs'].get('room_id')
        if not self.room_id:
            await self.close()
            return

        self.room_group_name = f"chat_{self.room_id}"

        # 3. Room va participantsni prefetch
        try:
            room = await sync_to_async(
                lambda: ChatRoom.objects.prefetch_related(
                    'participants', 'messages__attachments'
                ).get(id=self.room_id)
            )()
            self.room = room
        except ChatRoom.DoesNotExist:
            await self.close()
            return

        # 4. Participation check
        if not can_participate(self.user, room):
            await self.close()
            return

        # 5. Join channel layer
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # 6. Send chat history (latest 50 messages)
        last_messages = await sync_to_async(
            lambda: list(room.messages.prefetch_related('attachments').order_by('-created_at')[:50])
        )()

        history = []
        for msg in reversed(last_messages):
            attachments = [
                {"file": a.file.url, "file_type": a.file_type, "size": a.size}
                for a in msg.attachments.all()
            ]
            history.append({
                "message_id": msg.id,
                "sender_id": msg.sender.id,
                "text": msg.text,
                "attachments": attachments,
                "created_at": msg.created_at.isoformat()
            })

        await self.send_json({"type": "chat.history", "messages": history})

    # Disconnect
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive WebSocket message
    async def receive_json(self, content):
        room = self.room

        if not can_participate(self.user, room):
            await self.send_json({"error": "Not allowed"})
            return

        text = content.get('text', '').strip()
        attachments_data = content.get('attachments', [])

        # 1. Create Message
        message = await sync_to_async(Message.objects.create)(
            room=room,
            sender=self.user,
            text=text
        )

        # 2. Create attachments
        attachments_list = []
        for a in attachments_data:
            # 'file' field – serverda saqlangan URL yoki InMemoryFile
            attachment = await sync_to_async(MessageAttachment.objects.create)(
                message=message,
                file=a['file'],  # file object or uploaded URL
                file_type=a['file_type'],
                size=a['size']
            )
            attachments_list.append({
                "file": attachment.file.url,
                "file_type": attachment.file_type,
                "size": attachment.size
            })

        # 3. Broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': {
                    'message_id': message.id,
                    'sender_id': self.user.id,
                    'text': text,
                    'attachments': attachments_list,
                    'created_at': message.created_at.isoformat()
                }
            }
        )

    # Send message event
    async def chat_message(self, event):
        await self.send_json({"type": "chat.message", "message": event['message']})
