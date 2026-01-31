import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_call_notification(receiver, call, caller):
    """
    Send FCM notification for incoming call

    Args:
        receiver: User receiving the call
        call: Call object
        caller: User initiating the call
    """
    try:
        # Check if Firebase is configured
        if not hasattr(settings, 'FIREBASE_REGISTRATION_KEYS'):
            logger.warning("Firebase not configured, skipping FCM notification")
            return

        # Get receiver's FCM tokens from UserDevice model
        # Assuming you have a UserDevice model with fcm_token field
        try:
            from account.models import UserDevice
            devices = UserDevice.objects.filter(
                user=receiver,
                is_active=True,
                fcm_token__isnull=False
            ).exclude(fcm_token='')

            if not devices.exists():
                logger.info(f"No active devices with FCM token for user {receiver.id}")
                return
        except ImportError:
            logger.warning("UserDevice model not found, skipping FCM")
            return

        # Import Firebase (lazy import to avoid errors if not installed)
        try:
            import firebase_admin
            from firebase_admin import credentials, messaging
        except ImportError:
            logger.error("firebase-admin not installed")
            return

        # Initialize Firebase if not already done
        if not firebase_admin._apps:
            try:
                cred_path = settings.FIREBASE_CRED_PATH if hasattr(settings, 'FIREBASE_CRED_PATH') else None
                if cred_path:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                else:
                    logger.warning("Firebase credentials path not configured")
                    return
            except Exception as e:
                logger.error(f"Firebase initialization failed: {e}")
                return

        # Prepare notification data
        call_type_display = 'Video Call' if call.call_type == 'video' else 'Voice Call'
        caller_name = caller.first_name or caller.phone

        # Create notification
        notification = messaging.Notification(
            title=f"Incoming {call_type_display}",
            body=f"{caller_name} is calling you...",
        )

        # Data payload
        data = {
            'type': 'incoming_call',
            'call_id': str(call.id),
            'caller_id': str(caller.id),
            'caller_name': caller_name,
            'caller_phone': caller.phone,
            'caller_avatar': caller.avatar.url if hasattr(caller, 'avatar') and caller.avatar else '',
            'call_type': call.call_type,
            'livekit_room_name': call.livekit_room_name,
        }

        # Send to all devices
        success_count = 0
        for device in devices:
            try:
                message = messaging.Message(
                    notification=notification,
                    data=data,
                    token=device.fcm_token,
                    android=messaging.AndroidConfig(
                        priority='high',
                        notification=messaging.AndroidNotification(
                            channel_id='call_channel',
                            priority='max',
                            default_sound=True,
                            default_vibrate_timings=True,
                        ),
                    ),
                    apns=messaging.APNSConfig(
                        headers={'apns-priority': '10'},
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                alert=messaging.ApsAlert(
                                    title=f"Incoming {call_type_display}",
                                    body=f"{caller_name} is calling...",
                                ),
                                sound='default',
                                badge=1,
                            ),
                        ),
                    ),
                )

                response = messaging.send(message)
                logger.info(f"FCM sent to device {device.id}: {response}")
                success_count += 1

            except messaging.UnregisteredError:
                logger.warning(f"Device {device.id} token invalid, marking inactive")
                device.is_active = False
                device.save()
            except Exception as e:
                logger.error(f"Error sending FCM to device {device.id}: {e}")

        logger.info(f"FCM notifications sent: {success_count}/{devices.count()}")

    except Exception as e:
        logger.error(f"Error in send_call_notification: {e}", exc_info=True)
