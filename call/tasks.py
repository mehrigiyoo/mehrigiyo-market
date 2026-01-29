# call/tasks.py
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.db import models
from django.utils import timezone
from django.conf import settings
from .models import Call, CallEvent
import logging
from .service import livekit_service

logger = logging.getLogger('call')


@shared_task
def cleanup_abandoned_calls():
    """
    Clean up calls that were initiated but never answered
    Runs every 5 minutes
    """
    timeout = getattr(settings, 'CALL_ANSWER_TIMEOUT', 300)
    threshold = timezone.now() - timezone.timedelta(seconds=timeout)

    abandoned_calls = Call.objects.filter(
        status__in=['initiated', 'ringing'],
        created_at__lt=threshold
    )

    for call in abandoned_calls:
        try:
            call.mark_status('missed')
            livekit_service.delete_room(call.livekit_room_name)
            logger.info(f"Cleaned up abandoned call: {call.id}")
        except Exception as e:
            logger.error(f"Error cleaning up call {call.id}: {e}")

    return f"Cleaned up {abandoned_calls.count()} calls"


@shared_task
def check_long_running_calls():
    """
    Check and end calls that exceed maximum duration
    Runs every 10 minutes
    """
    max_duration = getattr(settings, 'MAX_CALL_DURATION', 7200)
    threshold = timezone.now() - timezone.timedelta(seconds=max_duration)

    long_calls = Call.objects.filter(
        status='answered',
        answered_at__lt=threshold
    )

    for call in long_calls:
        try:
            call.mark_status('ended')
            livekit_service.delete_room(call.livekit_room_name)
            logger.warning(f"Force-ended long call: {call.id}, duration: {call.duration}s")
        except Exception as e:
            logger.error(f"Error ending long call {call.id}: {e}")

    return f"Ended {long_calls.count()} long calls"


@shared_task
def generate_call_analytics(date=None):
    """
    Generate daily call analytics
    """
    from django.db.models import Count, Avg, Sum

    if not date:
        date = timezone.now().date()

    calls = Call.objects.filter(
        created_at__date=date
    )

    stats = calls.aggregate(
        total_calls=Count('id'),
        audio_calls=Count('id', filter=models.Q(call_type='audio')),
        video_calls=Count('id', filter=models.Q(call_type='video')),
        answered_calls=Count('id', filter=models.Q(status='answered')),
        missed_calls=Count('id', filter=models.Q(status='missed')),
        rejected_calls=Count('id', filter=models.Q(status='rejected')),
        avg_duration=Avg('duration'),
        total_duration=Sum('duration'),
    )

    logger.info(f"Call analytics for {date}: {stats}")
    return stats


@shared_task
def check_call_timeouts():
    """
    Check and mark unanswered calls as missed
    Runs every 30 seconds via Celery Beat
    """
    timeout_seconds = 60
    threshold = timezone.now() - timezone.timedelta(seconds=timeout_seconds)

    # Find unanswered calls older than threshold
    unanswered_calls = Call.objects.filter(
        status__in=['initiated', 'ringing'],
        created_at__lt=threshold
    ).select_related('caller', 'receiver', 'room')

    count = 0
    for call in unanswered_calls:
        try:
            # Mark as missed
            call.status = 'missed'
            call.ended_at = timezone.now()
            call.save()

            # Log event
            CallEvent.objects.create(
                call=call,
                event_type='missed',
                user=call.receiver,
                metadata={'reason': 'timeout', 'timeout_seconds': timeout_seconds}
            )

            # End LiveKit room
            livekit_service.delete_room(call.livekit_room_name)

            # WebSocket notification
            try:
                channel_layer = get_channel_layer()
                room_group_name = f'chat_{call.room.id}'

                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        'type': 'call_missed',
                        'call_id': call.id,
                        'reason': 'timeout'
                    }
                )
            except Exception as ws_error:
                logger.warning(f"WebSocket notification failed: {ws_error}")

            logger.info(f"Call {call.id} marked as missed (timeout) - {call.caller} → {call.receiver}")
            count += 1

        except Exception as e:
            logger.error(f"Error marking call {call.id} as missed: {e}")

    if count > 0:
        logger.info(f"Marked {count} call(s) as missed")

    return f"Checked calls, marked {count} as missed"
