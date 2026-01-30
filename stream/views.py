import uuid
import logging
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import StreamChat, StreamReaction
from .serializers import StreamChatSerializer



from .models import LiveStream, StreamViewer
from .serializers import (
    LiveStreamSerializer, LiveStreamListSerializer,
    LiveStreamCreateSerializer
)
from .services import livekit_stream_service

logger = logging.getLogger(__name__)


class LiveStreamViewSet(viewsets.ModelViewSet):
    """
    LiveStream ViewSet - Performance Optimized

    Endpoints:
    - GET    /api/streams/           - List streams
    - POST   /api/streams/           - Create stream
    - GET    /api/streams/{id}/      - Stream detail
    - PATCH  /api/streams/{id}/      - Update stream
    - DELETE /api/streams/{id}/      - Delete/Cancel stream

    - POST   /api/streams/{id}/start/      - Start stream (host)
    - POST   /api/streams/{id}/end/        - End stream (host)
    - POST   /api/streams/{id}/join/       - Join stream (viewer)
    - POST   /api/streams/{id}/leave/      - Leave stream

    - GET    /api/streams/live/            - Currently live streams
    - GET    /api/streams/scheduled/       - Upcoming scheduled streams
    - GET    /api/streams/my_streams/      - User's hosted streams
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Optimized queryset with prefetch"""
        return LiveStream.objects.select_related('host').filter(
            Q(host=self.request.user) | Q(status='live')
        )

    def get_serializer_class(self):
        """Dynamic serializer based on action"""
        if self.action == 'list':
            return LiveStreamListSerializer
        elif self.action == 'create':
            return LiveStreamCreateSerializer
        return LiveStreamSerializer

    def create(self, request):
        """
        Create new stream

        POST /api/streams/
        {
            "title": "My Stream",
            "description": "Test stream",
            "scheduled_at": "2026-02-01T10:00:00Z" (optional)
        }
        """
        serializer = LiveStreamCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Generate unique room name
        room_name = f"stream_{uuid.uuid4().hex[:16]}"

        # Create stream
        stream = serializer.save(
            host=request.user,
            livekit_room_name=room_name,
            status='scheduled' if serializer.validated_data.get('scheduled_at') else 'live'
        )

        # Create LiveKit room
        try:
            livekit_stream_service.create_room(room_name, max_participants=1000)
        except Exception as e:
            logger.error(f"LiveKit room creation failed: {e}")

        # If not scheduled, start immediately
        if not serializer.validated_data.get('scheduled_at'):
            stream.start_stream()

        # Generate host token
        host_token = livekit_stream_service.generate_host_token(
            room_name=room_name,
            host_id=request.user.id,
            host_name=request.user.first_name or request.user.phone
        )

        response_data = LiveStreamSerializer(stream).data
        response_data['livekit_token'] = host_token
        response_data['livekit_ws_url'] = livekit_stream_service.ws_url

        logger.info(f"Stream created: {stream.id} by {request.user}")

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Start stream (for scheduled streams)

        POST /api/streams/{id}/start/
        """
        stream = self.get_object()

        # Permission check
        if stream.host != request.user:
            return Response(
                {'error': 'Only host can start stream'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Status check
        if stream.status != 'scheduled':
            return Response(
                {'error': 'Stream must be scheduled to start'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Start stream
        stream.start_stream()

        # Generate token
        host_token = livekit_stream_service.generate_host_token(
            room_name=stream.livekit_room_name,
            host_id=request.user.id,
            host_name=request.user.first_name or request.user.phone
        )

        return Response({
            'stream_id': stream.id,
            'status': stream.status,
            'livekit_token': host_token,
            'livekit_ws_url': livekit_stream_service.ws_url,
        })

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End stream"""
        stream = self.get_object()

        if stream.host != request.user:
            return Response(
                {'error': 'Only host can end stream'},
                status=status.HTTP_403_FORBIDDEN
            )

        # End stream
        stream.end_stream()

        # Delete LiveKit room
        livekit_stream_service.delete_room(stream.livekit_room_name)

        # NEW: Broadcast stream ended via WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        stream_group_name = f'stream_{stream.id}'

        async_to_sync(channel_layer.group_send)(
            stream_group_name,
            {
                'type': 'stream_ended',
                'duration': stream.duration,
            }
        )

        logger.info(f"Stream ended: {stream.id}, duration: {stream.duration}s")

        return Response({
            'stream_id': stream.id,
            'status': stream.status,
            'duration': stream.duration,
            'total_views': stream.total_views,
            'peak_viewers': stream.peak_viewers,
        })

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """
        Join stream as viewer

        POST /api/streams/{id}/join/
        {
            "device_type": "mobile" (optional)
        }
        """
        stream = self.get_object()

        # Status check
        if stream.status != 'live':
            return Response(
                {'error': 'Stream is not live'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add viewer to cache (fast!)
        stream.add_viewer(request.user.id)

        # Create viewer record (async, not blocking)
        device_type = request.data.get('device_type', 'unknown')
        StreamViewer.objects.create(
            stream=stream,
            user=request.user,
            device_type=device_type
        )

        # Increment total views
        stream.total_views += 1
        stream.save(update_fields=['total_views'])

        # Generate viewer token
        viewer_token = livekit_stream_service.generate_viewer_token(
            room_name=stream.livekit_room_name,
            viewer_id=request.user.id,
            viewer_name=request.user.first_name or request.user.phone
        )

        logger.info(f"User {request.user} joined stream {stream.id}")

        return Response({
            'stream_id': stream.id,
            'livekit_token': viewer_token,
            'livekit_ws_url': livekit_stream_service.ws_url,
            'chat_enabled': stream.chat_enabled,
            'reactions_enabled': stream.reactions_enabled,
            'viewer_count': stream.get_active_viewers(),
        })

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """
        Leave stream

        POST /api/streams/{id}/leave/
        """
        stream = self.get_object()

        # Remove from cache
        stream.remove_viewer(request.user.id)

        # Update viewer record
        viewer = StreamViewer.objects.filter(
            stream=stream,
            user=request.user,
            left_at__isnull=True
        ).first()

        if viewer:
            viewer.left_at = timezone.now()
            viewer.calculate_watch_duration()

        logger.info(f"User {request.user} left stream {stream.id}")

        return Response({
            'stream_id': stream.id,
            'viewer_count': stream.get_active_viewers(),
        })

    @action(detail=False, methods=['get'])
    def live(self, request):
        """
        Get currently live streams

        GET /api/streams/live/
        """
        streams = LiveStream.objects.filter(
            status='live'
        ).select_related('host').order_by('-viewer_count')

        serializer = LiveStreamListSerializer(streams, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def scheduled(self, request):
        """
        Get scheduled streams

        GET /api/streams/scheduled/
        """
        streams = LiveStream.objects.filter(
            status='scheduled',
            scheduled_at__gte=timezone.now()
        ).select_related('host').order_by('scheduled_at')

        serializer = LiveStreamListSerializer(streams, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_streams(self, request):
        """
        Get user's hosted streams

        GET /api/streams/my_streams/
        """
        streams = LiveStream.objects.filter(
            host=request.user
        ).order_by('-created_at')

        serializer = LiveStreamListSerializer(streams, many=True)
        return Response(serializer.data)



class StreamChatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Stream Chat ViewSet - READ ONLY

    Live chat → WebSocket
    History → REST API

    Endpoints:
    - GET /api/stream/streams/{stream_id}/chat/ - Chat history
    """

    permission_classes = [IsAuthenticated]
    serializer_class = StreamChatSerializer

    def get_queryset(self):
        """Get chat history"""
        stream_id = self.kwargs.get('stream_pk')
        return StreamChat.objects.filter(
            stream_id=stream_id,
            is_deleted=False
        ).select_related('user').order_by('created_at')  # Oldest first


class StreamReactionViewSet(viewsets.ViewSet):
    """
    Stream Reaction ViewSet

    Live reactions → WebSocket
    Counts → REST API

    Endpoints:
    - GET /api/stream/streams/{stream_id}/reactions/counts/
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def counts(self, request, stream_pk=None):
        """Get reaction counts"""
        from .models import LiveStream
        from django.db.models import Count

        try:
            stream = LiveStream.objects.get(id=stream_pk)
        except LiveStream.DoesNotExist:
            return Response(
                {'error': 'Stream not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get counts
        reaction_counts = StreamReaction.objects.filter(
            stream=stream
        ).values('reaction_type').annotate(
            count=Count('id')
        )

        # Format
        counts = {
            'like': 0,
            'fire': 0,
            'clap': 0,
            'wow': 0,
        }

        for item in reaction_counts:
            counts[item['reaction_type']] = item['count']

        return Response(counts)