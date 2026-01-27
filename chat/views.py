from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Prefetch, Count
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
            'participants',
            Prefetch('messages', queryset=Message.objects.select_related('sender').order_by('-created_at')[:1])
        ).distinct()

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

        # Access tekshirish
        if not room.participants.filter(id=request.user.id).exists():
            return Response(
                {'detail': 'Sizda bu chatga kirish huquqi yo\'q'},
                status=status.HTTP_403_FORBIDDEN
            )

        messages = room.messages.select_related('sender').prefetch_related('attachments', 'reply_to__sender')

        # Pagination
        paginator = MessagePagination()
        page = paginator.paginate_queryset(messages, request)

        serializer = MessageSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Chatdagi barcha xabarlarni o'qilgan deb belgilash"""
        room = self.get_object()

        # Access tekshirish
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
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        message = serializer.save()

        #  WebSocket broadcast
        channel_layer = get_channel_layer()
        room_group_name = f'chat_{message.room.id}'

        output_serializer = MessageSerializer(message, context={'request': request})

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat_message_handler',
                'message': output_serializer.data
            }
        )

        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    # def create(self, request, *args, **kwargs):
    #     """Yangi xabar yuborish"""
    #     serializer = self.get_serializer(data=request.data, context={'request': request})
    #     serializer.is_valid(raise_exception=True)
    #     message = serializer.save()
    #
    #     output_serializer = MessageSerializer(message, context={'request': request})
    #     return Response(output_serializer.data, status=status.HTTP_201_CREATED)

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