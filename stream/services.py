from livekit import api
from django.conf import settings
from datetime import timedelta
import logging
import requests

logger = logging.getLogger(__name__)


class LiveKitStreamService:
    """LiveKit service for streaming (Singleton)"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.api_key = settings.LIVEKIT_API_KEY
        self.api_secret = settings.LIVEKIT_API_SECRET
        self.ws_url = settings.LIVEKIT_WS_URL
        self.http_url = settings.LIVEKIT_HTTP_URL

    def generate_host_token(self, room_name, host_id, host_name):
        """Host token - can publish"""
        try:
            token = api.AccessToken(self.api_key, self.api_secret)
            token.with_identity(f"host_{host_id}")
            token.with_name(host_name)
            token.with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,  # Can stream
                can_subscribe=True,
                can_publish_data=True,
            ))
            token.with_ttl(timedelta(hours=2))
            return token.to_jwt()
        except Exception as e:
            logger.error(f"Error generating host token: {e}")
            raise

    def generate_viewer_token(self, room_name, viewer_id, viewer_name):
        """Viewer token - read only"""
        try:
            token = api.AccessToken(self.api_key, self.api_secret)
            token.with_identity(f"viewer_{viewer_id}")
            token.with_name(viewer_name)
            token.with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=False,  # Cannot stream
                can_subscribe=True,  # Can watch
                can_publish_data=True,  # Can chat
            ))
            token.with_ttl(timedelta(hours=2))
            return token.to_jwt()
        except Exception as e:
            logger.error(f"Error generating viewer token: {e}")
            raise

    def create_room(self, room_name, max_participants=1000):
        """Create streaming room"""
        try:
            url = f"{self.http_url}/twirp/livekit.RoomService/CreateRoom"
            headers = {
                "Authorization": f"Bearer {self._get_admin_token()}",
                "Content-Type": "application/json"
            }
            data = {
                "name": room_name,
                "empty_timeout": 300,
                "max_participants": max_participants,
            }
            response = requests.post(url, json=data, headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info(f"Created room: {room_name}")
                return response.json()
            return {'name': room_name, 'auto_create': True}
        except Exception as e:
            logger.warning(f"Room create failed, auto-create: {e}")
            return {'name': room_name, 'auto_create': True}

    def delete_room(self, room_name):
        """Delete room"""
        try:
            url = f"{self.http_url}/twirp/livekit.RoomService/DeleteRoom"
            headers = {
                "Authorization": f"Bearer {self._get_admin_token()}",
                "Content-Type": "application/json"
            }
            response = requests.post(url, json={"room": room_name}, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error deleting room: {e}")
            return False

    def _get_admin_token(self):
        """Admin token for API calls"""
        token = api.AccessToken(self.api_key, self.api_secret)
        token.with_grants(api.VideoGrants(room_admin=True))
        token.with_ttl(timedelta(minutes=5))
        return token.to_jwt()


# Singleton instance
livekit_stream_service = LiveKitStreamService()