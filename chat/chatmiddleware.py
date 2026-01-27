from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from account.models import UserModel

@database_sync_to_async
def get_user(token_key):
    try:
        UntypedToken(token_key)
    except (InvalidToken, TokenError):
        return AnonymousUser()
    decoded_data = jwt_decode(token_key, settings.SECRET_KEY, algorithms=["HS256"])
    try:
        user = UserModel.objects.get(id=decoded_data["user_id"])
    except UserModel.DoesNotExist:
        user = AnonymousUser()
    return user

class TokenAuthMiddleware:
    """
    Custom middleware for Channels 3
    Token JWT auth via headers: Authorization: Bearer <token>
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # headers keys are bytes
        headers = dict(scope['headers'])
        auth_header = headers.get(b'authorization', None)
        token_key = None
        if auth_header:
            token_key = auth_header.decode().split(' ')[1]

        scope['user'] = await get_user(token_key) if token_key else AnonymousUser()

        return await self.inner(scope, receive, send)


# Helper for stacking with AuthMiddlewareStack if needed
TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(inner)
