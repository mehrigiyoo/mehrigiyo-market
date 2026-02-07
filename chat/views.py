from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Prefetch, Count, Max
from django.utils import timezone
from .models import ChatRoom, Message, MessageAttachment
from .serializers import (
    ChatRoomSerializer, ChatRoomCreateSerializer,
    MessageSerializer, MessageCreateSerializer
)


class MessagePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class ChatRoomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatRoomSerializer

    def get_queryset(self):
        return ChatRoom.objects.filter(
            participants=self.request.user
        ).prefetch_related(
            'participants'
        ).annotate(
            last_message_time_annotated=Max('messages__created_at')
        ).order_by('-last_message_time_annotated').distinct()

    def get_serializer_class(self):
        if self.action == 'create':
            return ChatRoomCreateSerializer
        return ChatRoomSerializer

    def create(self, request, *args, **kwargs):
        """1:1 chat yaratish yoki olish"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room = serializer.save()

        output_serializer = ChatRoomSerializer(room, context={'request': request})
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Chatdagi barcha xabarlar"""
        room = self.get_object()

        if not room.participants.filter(id=request.user.id).exists():
            return Response(
                {'detail': 'Sizda bu chatga kirish huquqi yo\'q'},
                status=status.HTTP_403_FORBIDDEN
            )

        messages = room.messages.select_related('sender').prefetch_related('attachments', 'reply_to__sender')

        paginator = MessagePagination()
        page = paginator.paginate_queryset(messages, request)

        serializer = MessageSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Chatdagi barcha xabarlarni o'qilgan deb belgilash"""
        room = self.get_object()

        if not room.participants.filter(id=request.user.id).exists():
            return Response(
                {'detail': 'Sizda bu chatga kirish huquqi yo\'q'},
                status=status.HTTP_403_FORBIDDEN
            )

        updated = room.messages.filter(
            is_read=False
        ).exclude(
            sender=request.user
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

        return Response({
            'success': True,
            'marked_count': updated
        })

    @action(detail=False, methods=['get'])
    def unread_total(self, request):
        """Umumiy o'qilmagan xabarlar soni"""
        total = Message.objects.filter(
            room__participants=request.user,
            is_read=False
        ).exclude(
            sender=request.user
        ).count()

        return Response({'unread_count': total})


class MessageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    pagination_class = MessagePagination

    def get_queryset(self):
        return Message.objects.filter(
            room__participants=self.request.user
        ).select_related('sender', 'room').prefetch_related('attachments')

    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    def create(self, request, *args, **kwargs):
        """Yangi xabar yuborish (text yoki file)"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        message = serializer.save()

        #  Message data tayyorlash (ABSOLUTE URLs bilan)
        message_data = self._prepare_message_data(message, request)

        #  WebSocket broadcast
        channel_layer = get_channel_layer()
        room_group_name = f'chat_{message.room.id}'

        try:
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'chat_message_handler',
                    'message': message_data
                }
            )
        except Exception as e:
            print(f"WebSocket broadcast error: {e}")

        return Response(message_data, status=status.HTTP_201_CREATED)

    def _prepare_message_data(self, message, request):
        """
        Message obyektini dict ga aylantirish
        ABSOLUTE URLs bilan
        """
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
            'is_mine': message.sender.id == request.user.id,
            'attachments': [],
            'reply_to': None
        }

        # ✅ Attachments with ABSOLUTE URLs
        for att in message.attachments.all():
            attachment_data = {
                'id': att.id,
                'file_type': att.file_type,
                'file_name': att.file_name,
                'size': att.size,
                'duration': att.duration,
                'file_url': request.build_absolute_uri(att.file.url) if att.file else None,
                'thumbnail_url': request.build_absolute_uri(att.thumbnail.url) if att.thumbnail else None,
            }
            data['attachments'].append(attachment_data)

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

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Bitta xabarni o'qilgan deb belgilash"""
        message = self.get_object()

        if message.sender != request.user and not message.is_read:
            message.is_read = True
            message.read_at = timezone.now()
            message.save(update_fields=['is_read', 'read_at'])

        serializer = self.get_serializer(message)
        return Response(serializer.data)






# Doctor eski chatlarni is_active True/False update


class DoctorChatRoomViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Doctor's chat room management

    Endpoints:
    - GET /api/doctor/chat-rooms/                        - List my chat rooms
    - GET /api/doctor/chat-rooms/{id}/                   - Chat room detail
    - POST /api/doctor/chat-rooms/{id}/toggle-active/   - Activate/Deactivate
    """

    permission_classes = [IsAuthenticated]

    # def get_queryset(self):
    #     """Get chat rooms for current doctor"""
    #     user = self.request.user
    #
    #     # Faqat doctorlar kirishi mumkin
    #     if user.role != 'doctor':
    #         return ChatRoom.objects.none()
    #
    #     # Doctor ishtirok etgan barcha chat roomlar
    #     return ChatRoom.objects.filter(
    #         room_type='1:1',
    #         participants=user
    #     ).prefetch_related('participants').order_by('-updated_at')

    # def list(self, request):
    #     """
    #     Doctor's chat roomlar ro'yxati
    #
    #     GET /api/doctor/chat-rooms/
    #     """
    #     queryset = self.get_queryset()
    #
    #     rooms_data = []
    #     for room in queryset:
    #         # Ikkinchi participant (client)
    #         other_participant = room.participants.exclude(id=request.user.id).first()
    #
    #         if other_participant:
    #             rooms_data.append({
    #                 'id': room.id,
    #                 'is_active': room.is_active,
    #                 'client': {
    #                     'id': other_participant.id,
    #                     'name': f"{other_participant.first_name or ''} {other_participant.last_name or ''}".strip() or other_participant.phone,
    #                     'phone': other_participant.phone,
    #                 },
    #                 'last_message': room.last_message_text,
    #                 'last_message_time': room.last_message_time,
    #                 'created_at': room.created_at,
    #                 'updated_at': room.updated_at,
    #             })
    #
    #     return Response({
    #         'count': len(rooms_data),
    #         'results': rooms_data
    #     })

    # def retrieve(self, request, pk=None):
    #     """
    #     Chat room detail
    #
    #     GET /api/doctor/chat-rooms/{id}/
    #     """
    #     room = self.get_object()
    #
    #     # Ikkinchi participant
    #     other_participant = room.participants.exclude(id=request.user.id).first()
    #
    #     return Response({
    #         'id': room.id,
    #         'is_active': room.is_active,
    #         'room_type': room.room_type,
    #         'client': {
    #             'id': other_participant.id,
    #             'name': f"{other_participant.first_name or ''} {other_participant.last_name or ''}".strip() or other_participant.phone,
    #             'phone': other_participant.phone,
    #         } if other_participant else None,
    #         'created_at': room.created_at,
    #         'updated_at': room.updated_at,
    #     })

    # @action(detail=True, methods=['post'])
    # def toggle_active(self, request, pk=None):
    #     """
    #     Chat roomni aktivlashtirish yoki deaktivlashtirish
    #
    #     POST /api/doctor/chat-rooms/{id}/toggle-active/
    #
    #     Body (optional):
    #     {
    #         "is_active": true  // yoki false
    #     }
    #
    #     Agar body bo'lmasa, avtomatik toggle qiladi
    #     """
    #     room = self.get_object()
    #
    #     # Request body dan is_active olish
    #     new_status = request.data.get('is_active')
    #
    #     if new_status is not None:
    #         # Aniq qiymat berilgan
    #         room.is_active = bool(new_status)
    #     else:
    #         # Toggle qilish
    #         room.is_active = not room.is_active
    #
    #     room.save()
    #
    #     # Ikkinchi participant
    #     other_participant = room.participants.exclude(id=request.user.id).first()
    #
    #     import logging
    #     logger = logging.getLogger(__name__)
    #     logger.info(f"Doctor {request.user.id} {'activated' if room.is_active else 'deactivated'} chat room {room.id}")
    #
    #     # Clientga notification yuborish (optional)
    #     if other_participant:
    #         try:
    #             from utils.fcm import send_fcm
    #
    #             if room.is_active:
    #                 send_fcm(
    #                     user=other_participant,
    #                     type='chat_activated',
    #                     title='Chat aktivlashtirildi',
    #                     body=f'Dr. {request.user.first_name} bilan chat yana ochildi',
    #                     chat_room_id=room.id,
    #                 )
    #             else:
    #                 send_fcm(
    #                     user=other_participant,
    #                     type='chat_deactivated',
    #                     title='Chat yopildi',
    #                     body=f'Dr. {request.user.first_name} bilan chat yakunlandi',
    #                     chat_room_id=room.id,
    #                 )
    #         except Exception as e:
    #             logger.error(f"Failed to send FCM: {e}")
    #
    #     return Response({
    #         'room_id': room.id,
    #         'is_active': room.is_active,
    #         'message': f"Chat room {'activated' if room.is_active else 'deactivated'} successfully"
    #     })

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Chat roomni aktivlashtirish

        POST /api/doctor/chat-rooms/{id}/activate/
        """
        room = self.get_object()
        room.is_active = True
        room.save()

        return Response({
            'room_id': room.id,
            'is_active': room.is_active,
            'message': 'Chat room activated'
        })

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Chat roomni deaktivlashtirish

        POST /api/doctor/chat-rooms/{id}/deactivate/
        """
        room = self.get_object()
        room.is_active = False
        room.save()

        return Response({
            'room_id': room.id,
            'is_active': room.is_active,
            'message': 'Chat room deactivated'
        })




