from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
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

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # print(scope['path'])
        # print(receive)
        # print(send)
        # query_params = parse_qs(scope["query_string"].decode())
        # print(query_params["token"][-1])
        scope = dict(scope)
        token_key = parse_qs(scope["query_string"].decode())['token'][0]
        headers = dict(scope['headers'])

        scope['user'] = await get_user(token_key)


        return await self.inner(scope, receive, send)


TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(AuthMiddlewareStack(inner))
