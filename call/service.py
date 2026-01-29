# call/services.py - SIMPLIFIED VERSION (Token only)

from livekit import api
from django.conf import settings
from django.core.cache import cache
from datetime import timedelta
import logging
import requests

logger = logging.getLogger(__name__)


class LiveKitService:
    """
    LiveKit integration service - Simplified (Token generation only)
    Room management qilmaymiz - LiveKit auto-create qiladi
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LiveKitService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize LiveKit configuration"""
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        self.ws_url = settings.LIVEKIT_WS_URL
        self.http_url = settings.LIVEKIT_HTTP_URL

    def generate_token(self, room_name, participant_identity, participant_name, metadata=None):
        """
        Generate LiveKit access token

        LiveKit automatically creates room when first participant joins
        """
        try:
            token = api.AccessToken(self.api_key, self.api_secret)

            token.with_identity(str(participant_identity))
            token.with_name(participant_name)

            if metadata:
                token.with_metadata(metadata)

            # Permissions
            token.with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            ))

            # Token expires in 1 hour
            token.with_ttl(timedelta(hours=1))

            jwt_token = token.to_jwt()

            logger.info(f"Generated token for {participant_name} in room {room_name}")
            return jwt_token

        except Exception as e:
            logger.error(f"Error generating token: {e}")
            raise

    def create_room(self, room_name, max_participants=2, empty_timeout=300):
        """
        Create LiveKit room via REST API

        LiveKit Cloud auto-creates rooms, but we can pre-create for settings
        """
        try:
            url = f"{self.http_url}/twirp/livekit.RoomService/CreateRoom"

            headers = {
                "Authorization": f"Bearer {self._get_admin_token()}",
                "Content-Type": "application/json"
            }

            data = {
                "name": room_name,
                "empty_timeout": empty_timeout,
                "max_participants": max_participants
            }

            response = requests.post(url, json=data, headers=headers, timeout=10)

            if response.status_code == 200:
                logger.info(f"Created LiveKit room: {room_name}")
                room_data = response.json()

                # Cache room info
                cache.set(f"livekit_room:{room_name}", room_data, timeout=3600)

                return room_data
            else:
                logger.warning(f"Room creation returned {response.status_code}: {response.text}")
                # Auto-create will handle it
                return {'name': room_name, 'auto_create': True}

        except Exception as e:
            logger.warning(f"Room API call failed, will auto-create: {e}")
            # LiveKit auto-creates on join anyway
            return {'name': room_name, 'auto_create': True}

    def delete_room(self, room_name):
        """
        Delete/End LiveKit room via REST API
        """
        try:
            url = f"{self.http_url}/twirp/livekit.RoomService/DeleteRoom"

            headers = {
                "Authorization": f"Bearer {self._get_admin_token()}",
                "Content-Type": "application/json"
            }

            data = {"room": room_name}

            response = requests.post(url, json=data, headers=headers, timeout=10)

            if response.status_code == 200:
                logger.info(f"Deleted LiveKit room: {room_name}")
                cache.delete(f"livekit_room:{room_name}")
                return True
            else:
                logger.warning(f"Room deletion returned {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error deleting room {room_name}: {e}")
            return False

    def get_room(self, room_name):
        """Get room info via REST API"""
        try:
            # Check cache first
            cached = cache.get(f"livekit_room:{room_name}")
            if cached:
                return cached

            url = f"{self.http_url}/twirp/livekit.RoomService/ListRooms"

            headers = {
                "Authorization": f"Bearer {self._get_admin_token()}",
                "Content-Type": "application/json"
            }

            response = requests.post(url, json={}, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                for room in data.get('rooms', []):
                    if room['name'] == room_name:
                        return room

            return None

        except Exception as e:
            logger.error(f"Error getting room {room_name}: {e}")
            return None

    def list_participants(self, room_name):
        """List participants in room"""
        try:
            url = f"{self.http_url}/twirp/livekit.RoomService/ListParticipants"

            headers = {
                "Authorization": f"Bearer {self._get_admin_token()}",
                "Content-Type": "application/json"
            }

            data = {"room": room_name}

            response = requests.post(url, json=data, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json().get('participants', [])

            return []

        except Exception as e:
            logger.error(f"Error listing participants in {room_name}: {e}")
            return []

    def remove_participant(self, room_name, participant_identity):
        """Remove participant from room"""
        try:
            url = f"{self.http_url}/twirp/livekit.RoomService/RemoveParticipant"

            headers = {
                "Authorization": f"Bearer {self._get_admin_token()}",
                "Content-Type": "application/json"
            }

            data = {
                "room": room_name,
                "identity": participant_identity
            }

            response = requests.post(url, json=data, headers=headers, timeout=10)

            if response.status_code == 200:
                logger.info(f"Removed {participant_identity} from {room_name}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error removing participant: {e}")
            return False

    def _get_admin_token(self):
        """Generate admin token for API calls"""
        token = api.AccessToken(self.api_key, self.api_secret)
        token.with_grants(api.VideoGrants(room_admin=True))
        token.with_ttl(timedelta(minutes=5))
        return token.to_jwt()


# Singleton instance
livekit_service = LiveKitService()