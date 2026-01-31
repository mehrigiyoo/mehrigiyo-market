# call/tasks.py
from datetime import timedelta
from celery import shared_task
from django.db import models
from django.utils import timezone
from django.conf import settings

from utils.fcm import send_fcm
from .models import Call
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
    Check for call timeouts and mark as missed
    Runs every 30 seconds
    """
    logger.info(" Checking for call timeouts...")

    # 60 seconds timeout
    timeout_threshold = timezone.now() - timedelta(seconds=60)

    # Find timed out calls
    timed_out_calls = Call.objects.filter(
        status__in=['initiated', 'ringing'],
        created_at__lt=timeout_threshold
    ).select_related('caller', 'receiver')

    missed_count = 0
    for call in timed_out_calls:
        try:
            # Mark as missed
            call.status = 'missed'
            call.ended_at = timezone.now()
            call.save(update_fields=['status', 'ended_at'])

            # Send FCM notification
            send_fcm(
                user=call.receiver,
                type='call_missed',
                title="Missed call",
                body=f"You missed a call from {call.caller.first_name or call.caller.phone}",
                call_id=call.id,
                caller_id=call.caller.id,
                caller_name=call.caller.first_name or call.caller.phone,
                caller_phone=call.caller.phone,
                caller_avatar=call.caller.avatar.url if call.caller.avatar else '',
                call_type=call.call_type,
                missed_at=call.created_at.isoformat(),
            )

            # Delete LiveKit room
            try:
                from .service import livekit_service
                livekit_service.delete_room(call.livekit_room_name)
            except Exception as e:
                logger.warning(f"Failed to delete room: {e}")

            logger.info(f"📞 Call {call.id} marked as missed")
            missed_count += 1

        except Exception as e:
            logger.error(f"Error processing call {call.id}: {e}")

    if missed_count > 0:
        logger.info(f" Marked {missed_count} calls as missed")

    return f"Processed {missed_count} calls"
