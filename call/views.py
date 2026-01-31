from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import uuid
import logging

from .models import Call, CallEvent
from .notification import send_call_notification
from .serializers import (
    CallSerializer, CallListSerializer,
    CallInitiateSerializer
)
from chat.models import ChatRoom
from .service import livekit_service

logger = logging.getLogger(__name__)


class CallPagination(PageNumberPagination):
    """Custom pagination for calls"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CallViewSet(viewsets.ModelViewSet):
    """
    Call ViewSet - Unified API for Voice & Video Calls

    Endpoints:
    - POST   /api/call/calls/initiate/     - Initiate call
    - POST   /api/call/calls/{id}/answer/  - Answer call
    - POST   /api/call/calls/{id}/reject/  - Reject call
    - POST   /api/call/calls/{id}/end/     - End call
    - POST   /api/call/calls/{id}/cancel/  - Cancel call
    - GET    /api/call/calls/              - List calls
    - GET    /api/call/calls/{id}/         - Call detail
    - GET    /api/call/calls/active/       - Active calls
    - GET    /api/call/calls/history/      - Call history
    """

    permission_classes = [IsAuthenticated]
    pagination_class = CallPagination

    def get_queryset(self):
        """Get calls for current user"""
        return Call.objects.filter(
            Q(caller=self.request.user) | Q(receiver=self.request.user)
        ).select_related('caller', 'receiver', 'room').prefetch_related('events')

    def get_serializer_class(self):
        """Dynamic serializer selection"""
        if self.action == 'list':
            return CallListSerializer
        return CallSerializer


    # INITIATE CALL
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """
        Initiate new call (voice or video)

        Request:
            {
                "room_id": 2,
                "call_type": "audio"  # or "video"
            }

        Response:
            {
                "call_id": 1,
                "status": "initiated",
                "call_type": "audio",
                "livekit_room_name": "call_abc123",
                "livekit_token": "eyJhbGc...",
                "livekit_ws_url": "ws://livekit:7880",
                "caller": {...},
                "receiver": {...}
            }
        """
        serializer = CallInitiateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        room_id = serializer.validated_data['room_id']
        call_type = serializer.validated_data['call_type']

        try:
            chat_room = ChatRoom.objects.get(id=room_id)

            # Get participants
            caller = request.user
            receiver = chat_room.get_other_participant(caller)

            if not receiver:
                return Response(
                    {'error': 'Receiver topilmadi'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            #  BUSY CHECK - YANGI!
            # Check if caller is busy
            caller_busy = Call.objects.filter(
                Q(caller=caller) | Q(receiver=caller),
                status__in=['initiated', 'ringing', 'answered']
            ).exists()

            if caller_busy:
                return Response(
                    {
                        'error': 'You are already in a call',
                        'error_code': 'CALLER_BUSY',
                        'message': 'Siz allaqachon boshqa calldasiz'
                    },
                    status=status.HTTP_409_CONFLICT
                )

            # Check if receiver is busy
            receiver_busy = Call.objects.filter(
                Q(caller=receiver) | Q(receiver=receiver),
                status__in=['initiated', 'ringing', 'answered']
            ).exists()

            if receiver_busy:
                return Response(
                    {
                        'error': 'User is busy',
                        'error_code': 'RECEIVER_BUSY',
                        'message': f'{receiver.first_name or "Foydalanuvchi"} boshqa callda'
                    },
                    status=status.HTTP_409_CONFLICT
                )

            # ... rest of existing initiate code
            # Generate room name, create call, etc.

            livekit_room_name = f"call_{uuid.uuid4().hex[:16]}"

            lk_room = livekit_service.create_room(
                room_name=livekit_room_name,
                max_participants=2,
                empty_timeout=300
            )

            if not lk_room:
                logger.error(f"Failed to create LiveKit room for call {livekit_room_name}")
                return Response(
                    {'error': 'Call yaratishda xatolik'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Create Call record
            call = Call.objects.create(
                room=chat_room,
                call_type=call_type,
                status='initiated',
                caller=caller,
                receiver=receiver,
                livekit_room_name=livekit_room_name
            )

            # Log event
            CallEvent.objects.create(
                call=call,
                event_type='initiated',
                user=caller,
                metadata={'call_type': call_type}
            )

            # Generate tokens
            caller_token = livekit_service.generate_token(
                room_name=livekit_room_name,
                participant_identity=caller.id,
                participant_name=f"{caller.first_name or caller.phone}",
                metadata=f'{{"user_id": {caller.id}, "role": "{caller.role}"}}'
            )

            receiver_token = livekit_service.generate_token(
                room_name=livekit_room_name,
                participant_identity=receiver.id,
                participant_name=f"{receiver.first_name or receiver.phone}",
                metadata=f'{{"user_id": {receiver.id}, "role": "{receiver.role}"}}'
            )

            # WebSocket signal
            self._send_websocket_signal(
                room_id=chat_room.id,
                signal_type='call_incoming',
                data={
                    'call_id': call.id,
                    'call_type': call_type,
                    'caller': {
                        'id': caller.id,
                        'phone': caller.phone,
                        'first_name': caller.first_name or '',
                        'last_name': caller.last_name or '',
                        'role': caller.role,
                    },
                    'livekit_room_name': livekit_room_name,
                    'livekit_token': receiver_token,
                    'livekit_ws_url': livekit_service.ws_url,
                }
            )

            # 2. FCM Notification
            try:
                send_call_notification(
                    receiver=receiver,
                    call=call,
                    caller=caller
                )
                logger.info(f"FCM notification sent for call {call.id}")
            except Exception as e:
                logger.error(f"FCM notification failed for call {call.id}: {e}")
                # Don't fail the call if notification fails

            logger.info(f"Call initiated: {call.id} - {caller} → {receiver} ({call_type})")

            # Response to caller
            return Response({
                'call_id': call.id,
                'status': call.status,
                'call_type': call.call_type,
                'livekit_room_name': livekit_room_name,
                'livekit_token': caller_token,
                'livekit_ws_url': livekit_service.ws_url,
                'caller': {
                    'id': caller.id,
                    'phone': caller.phone,
                    'first_name': caller.first_name or '',
                    'role': caller.role,
                },
                'receiver': {
                    'id': receiver.id,
                    'phone': receiver.phone,
                    'first_name': receiver.first_name or '',
                    'role': receiver.role,
                }
            }, status=status.HTTP_201_CREATED)

        except ChatRoom.DoesNotExist:
            return Response(
                {'error': 'Chat room topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error initiating call: {e}", exc_info=True)
            return Response(
                {'error': 'Call yaratishda xatolik'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ANSWER CALL
    @action(detail=True, methods=['post'])
    def answer(self, request, pk=None):
        """
        Answer incoming call

        Response:
            {
                "call_id": 1,
                "status": "answered",
                "livekit_token": "eyJhbGc...",
                "livekit_ws_url": "ws://livekit:7880"
            }
        """
        call = self.get_object()

        # Permission check
        if call.receiver != request.user:
            return Response(
                {'error': 'Sizda bu call ni answer qilish huquqi yo\'q'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Status check
        if call.status not in ['initiated', 'ringing']:
            return Response(
                {'error': f'Call allaqachon {call.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Update status
            call.mark_status('answered')

            # Log event
            CallEvent.objects.create(
                call=call,
                event_type='answered',
                user=request.user
            )

            # Generate token for receiver (if not already done)
            receiver_token = livekit_service.generate_token(
                room_name=call.livekit_room_name,
                participant_identity=request.user.id,
                participant_name=f"{request.user.first_name or request.user.phone}",
                metadata=f'{{"user_id": {request.user.id}, "role": "{request.user.role}"}}'
            )

            # Send signal to caller
            self._send_websocket_signal(
                room_id=call.room.id,
                signal_type='call_answered',
                data={
                    'call_id': call.id,
                    'answerer': {
                        'id': request.user.id,
                        'phone': request.user.phone,
                        'first_name': request.user.first_name or '',
                    }
                }
            )

            logger.info(f"Call answered: {call.id} by {request.user}")

            return Response({
                'call_id': call.id,
                'status': call.status,
                'call_type': call.call_type,
                'livekit_room_name': call.livekit_room_name,
                'livekit_token': receiver_token,
                'livekit_ws_url': livekit_service.ws_url,
            })

        except Exception as e:
            logger.error(f"Error answering call {call.id}: {e}", exc_info=True)
            return Response(
                {'error': 'Call answer qilishda xatolik'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # REJECT CALL
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject incoming call

        Response:
            {
                "call_id": 1,
                "status": "rejected"
            }
        """
        call = self.get_object()

        # Permission check
        if call.receiver != request.user:
            return Response(
                {'error': 'Sizda bu call ni reject qilish huquqi yo\'q'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Status check
        if call.status not in ['initiated', 'ringing']:
            return Response(
                {'error': f'Call allaqachon {call.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Update status
            call.mark_status('rejected')

            # Log event
            CallEvent.objects.create(
                call=call,
                event_type='rejected',
                user=request.user
            )

            # End LiveKit room
            livekit_service.delete_room(call.livekit_room_name)

            # Send signal to caller
            self._send_websocket_signal(
                room_id=call.room.id,
                signal_type='call_rejected',
                data={
                    'call_id': call.id,
                    'rejecter': {
                        'id': request.user.id,
                        'phone': request.user.phone,
                        'first_name': request.user.first_name or '',
                    }
                }
            )

            logger.info(f"Call rejected: {call.id} by {request.user}")

            return Response({
                'call_id': call.id,
                'status': call.status
            })

        except Exception as e:
            logger.error(f"Error rejecting call {call.id}: {e}", exc_info=True)
            return Response(
                {'error': 'Call reject qilishda xatolik'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # CALL CANCEL REQUEST USER
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel call before answer

        Only caller can cancel
        Status must be 'initiated' or 'ringing'

        Response:
            {
                "call_id": 1,
                "status": "cancelled"
            }
        """
        call = self.get_object()

        # Permission: faqat caller cancel qila oladi
        if call.caller != request.user:
            return Response(
                {'error': 'Faqat caller call ni cancel qila oladi'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Status check: faqat answered bo'lmagan calllarni cancel qilish mumkin
        if call.status not in ['initiated', 'ringing']:
            return Response(
                {'error': f'Call allaqachon {call.status}. Cancel qilib bo\'lmaydi'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Update status
            call.mark_status('cancelled')

            # Log event
            CallEvent.objects.create(
                call=call,
                event_type='cancelled',
                user=request.user,
                metadata={'reason': 'user_cancelled'}
            )

            # End LiveKit room
            livekit_service.delete_room(call.livekit_room_name)

            # Send signal to receiver
            self._send_websocket_signal(
                room_id=call.room.id,
                signal_type='call_cancelled',
                data={
                    'call_id': call.id,
                    'cancelled_by': {
                        'id': request.user.id,
                        'phone': request.user.phone,
                        'first_name': request.user.first_name or '',
                    }
                }
            )

            logger.info(f"Call cancelled: {call.id} by {request.user}")

            return Response({
                'call_id': call.id,
                'status': call.status
            })

        except Exception as e:
            logger.error(f"Error cancelling call {call.id}: {e}", exc_info=True)
            return Response(
                {'error': 'Call cancel qilishda xatolik'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # END CALL
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """
        End active call

        Response:
            {
                "call_id": 1,
                "status": "ended",
                "duration": 125,
                "formatted_duration": "2m 5s"
            }
        """
        call = self.get_object()

        # Permission check
        if request.user not in [call.caller, call.receiver]:
            return Response(
                {'error': 'Sizda bu call ni end qilish huquqi yo\'q'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Status check
        if call.status == 'ended':
            return Response(
                {'error': 'Call allaqachon ended'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Update status
            call.mark_status('ended')

            # Log event
            CallEvent.objects.create(
                call=call,
                event_type='ended',
                user=request.user
            )

            # End LiveKit room
            livekit_service.delete_room(call.livekit_room_name)

            # Send signal to other participant
            self._send_websocket_signal(
                room_id=call.room.id,
                signal_type='call_ended',
                data={
                    'call_id': call.id,
                    'ended_by': {
                        'id': request.user.id,
                        'phone': request.user.phone,
                        'first_name': request.user.first_name or '',
                    },
                    'duration': call.duration,
                    'formatted_duration': call.formatted_duration
                }
            )

            logger.info(f"Call ended: {call.id} by {request.user}, duration: {call.formatted_duration}")

            return Response({
                'call_id': call.id,
                'status': call.status,
                'duration': call.duration,
                'formatted_duration': call.formatted_duration
            })

        except Exception as e:
            logger.error(f"Error ending call {call.id}: {e}", exc_info=True)
            return Response(
                {'error': 'Call end qilishda xatolik'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ACTIVE CALLS
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get active calls for current user

        Response:
            [
                {
                    "id": 1,
                    "call_type": "video",
                    "status": "answered",
                    "caller": {...},
                    "receiver": {...},
                    "created_at": "..."
                }
            ]
        """
        active_calls = self.get_queryset().filter(
            status__in=['initiated', 'ringing', 'answered']
        )

        serializer = CallListSerializer(active_calls, many=True, context={'request': request})
        return Response(serializer.data)

    # CALL HISTORY
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get call history (paginated)

        Query params:
            - page: Page number
            - page_size: Items per page (default: 20)
            - call_type: Filter by call type (audio/video)
            - status: Filter by status

        Response:
            {
                "count": 100,
                "next": "...",
                "previous": "...",
                "results": [...]
            }
        """
        queryset = self.get_queryset().filter(
            status__in=['ended', 'missed', 'rejected']
        )

        # Filters
        call_type = request.query_params.get('call_type')
        if call_type:
            queryset = queryset.filter(call_type=call_type)

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CallListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = CallListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)



    # HELPER METHODS
    def _send_websocket_signal(self, room_id, signal_type, data):
        """
        Send WebSocket signal to chat room

        Args:
            room_id: Chat room ID
            signal_type: Signal type (call_incoming, call_answered, etc.)
            data: Signal data
        """
        try:
            channel_layer = get_channel_layer()
            room_group_name = f'chat_{room_id}'

            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': signal_type,
                    **data
                }
            )

            logger.debug(f"WebSocket signal sent: {signal_type} to room {room_id}")

        except Exception as e:
            logger.error(f"Error sending WebSocket signal: {e}", exc_info=True)