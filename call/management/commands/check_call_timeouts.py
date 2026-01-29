# call/management/commands/check_call_timeouts.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from call.models import Call, CallEvent
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

from call.service import livekit_service

logger = logging.getLogger('call')


class Command(BaseCommand):
    help = 'Check and mark unanswered calls as missed after timeout'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=60,
            help='Timeout in seconds (default: 60)'
        )

    def handle(self, *args, **options):
        timeout_seconds = options['timeout']
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

                # Send WebSocket notification
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

                self.stdout.write(
                    self.style.SUCCESS(f'✓ Call {call.id} marked as missed ({call.caller} → {call.receiver})')
                )
                count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error marking call {call.id} as missed: {e}')
                )
                logger.error(f"Error marking call {call.id} as missed: {e}")

        if count == 0:
            self.stdout.write(
                self.style.WARNING('No calls to mark as missed')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully marked {count} call(s) as missed')
            )

        return count