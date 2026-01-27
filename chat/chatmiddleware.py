from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

@database_sync_to_async
def get_user(token_key):
    if not token_key:
        return AnonymousUser()
    # token importni ichida qilamiz
    from rest_framework_simplejwt.tokens import UntypedToken
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    from jwt import decode as jwt_decode
    from django.conf import settings
    from django.contrib.auth import get_user_model

    UserModel = get_user_model()
    try:
        UntypedToken(token_key)
        decoded_data = jwt_decode(token_key, settings.SECRET_KEY, algorithms=["HS256"])
        user = UserModel.objects.get(id=decoded_data["user_id"])
    except (InvalidToken, TokenError, UserModel.DoesNotExist):
        user = AnonymousUser()
    return user


class TokenAuthMiddleware:
    """Headers orqali JWT auth"""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # headers keys are bytes
        headers = dict(scope['headers'])
        auth_header = headers.get(b'authorization', None)
        token_key = None
        if auth_header:
            token_key = auth_header.decode().split(' ')[1]

        scope['user'] = await get_user(token_key)

        return await self.inner(scope, receive, send)


TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(inner)
