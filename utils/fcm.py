# utils/fcm.py - Verify this exists

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class FCMNotification:
    """Universal FCM sender"""

    _firebase_initialized = False

    @classmethod
    def _init_firebase(cls):
        """Initialize Firebase once"""
        if cls._firebase_initialized:
            return True

        try:
            import firebase_admin
            from firebase_admin import credentials

            if not firebase_admin._apps:
                # ✅ YANGI PATH
                cred_path = '/Doctor/config/firebase-cred.json'

                import os
                if not os.path.exists(cred_path):
                    logger.error(f"Firebase credentials not found at {cred_path}")
                    return False

                # Check if it's a file (not directory)
                if not os.path.isfile(cred_path):
                    logger.error(f"Firebase credentials is not a file: {cred_path}")
                    return False

                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                cls._firebase_initialized = True
                logger.info("✅ Firebase initialized successfully")

            return True

        except Exception as e:
            logger.error(f"❌ Firebase initialization failed: {e}")
            return False

    @classmethod
    def send(cls, user, type, title, body, data=None, priority='high'):
        """Send FCM notification"""
        if data is None:
            data = {}

        # Initialize Firebase
        if not cls._init_firebase():
            return False

        try:
            from account.models import UserDevice
            from firebase_admin import messaging

            # Get user devices
            devices = UserDevice.objects.filter(
                user=user,
                is_active=True,
                fcm_token__isnull=False
            ).exclude(fcm_token='')

            if not devices.exists():
                logger.info(f"⚠️  No FCM devices for user {user.id}")
                return False

            # Add type to data
            data['type'] = type
            data = {k: str(v) for k, v in data.items()}

            # Send to all devices
            success_count = 0
            for device in devices:
                try:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=title,
                            body=body,
                        ),
                        data=data,
                        token=device.fcm_token,
                        android=messaging.AndroidConfig(
                            priority=priority,
                            notification=messaging.AndroidNotification(
                                channel_id='default_channel',
                                priority='max',
                                default_sound=True,
                            ),
                        ),
                        apns=messaging.APNSConfig(
                            headers={'apns-priority': '10'},
                            payload=messaging.APNSPayload(
                                aps=messaging.Aps(
                                    alert=messaging.ApsAlert(title=title, body=body),
                                    sound='default',
                                    badge=1,
                                ),
                            ),
                        ),
                    )

                    response = messaging.send(message)
                    logger.info(f"✅ FCM sent to device {device.id}: {response}")
                    success_count += 1

                except messaging.UnregisteredError:
                    logger.warning(f"⚠️  Invalid token, deactivating device {device.id}")
                    device.is_active = False
                    device.save()
                except Exception as e:
                    logger.error(f"❌ FCM error for device {device.id}: {e}")

            logger.info(f"📊 FCM sent: {success_count}/{devices.count()} devices")
            return success_count > 0

        except Exception as e:
            logger.error(f"❌ FCM notification error: {e}", exc_info=True)
            return False


def send_fcm(user, type, title, body, **data):
    """Shortcut function"""
    return FCMNotification.send(user, type, title, body, data)