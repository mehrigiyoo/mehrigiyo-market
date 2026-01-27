from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
from account.models import UserModel


@database_sync_to_async
def get_user(token_key):
    try:
        UntypedToken(token_key)
    except (InvalidToken, TokenError) as e:
        return None
    else:
        decoded_data = jwt_decode(token_key, settings.SECRET_KEY, algorithms=["HS256"])
        user = UserModel.objects.get(id=decoded_data["user_id"])
    return user

from urllib.parse import parse_qs
class TokenAuthMiddleware:
    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        # headers keys are bytes, values are bytes
        auth_header = headers.get(b'authorization', None)
        token_key = None
        if auth_header:
            # b'Bearer <token>'
            token_key = auth_header.decode().split(' ')[1]

        if not token_key:
            scope['user'] = AnonymousUser()
        else:
            scope['user'] = await get_user(token_key)

        return await self.inner(scope, receive, send)
