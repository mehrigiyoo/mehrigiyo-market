from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def get_user(token_key):
    if not token_key:
        return AnonymousUser()

    from rest_framework_simplejwt.tokens import UntypedToken
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    from jwt import decode as jwt_decode
    from django.conf import settings
    from django.contrib.auth import get_user_model

    UserModel = get_user_model()
    try:
        # Token validate
        UntypedToken(token_key)
        decoded_data = jwt_decode(token_key, settings.SECRET_KEY, algorithms=["HS256"])
        user = UserModel.objects.get(id=decoded_data["user_id"])
        return user
    except (InvalidToken, TokenError, UserModel.DoesNotExist, Exception) as e:
        print(f"Auth error: {e}")
        return AnonymousUser()


class TokenAuthMiddleware:
    """
    Token authentication middleware for WebSocket
    Supports both:
    1. Headers: Authorization: Bearer <token>
    2. Query params: ?token=<token>
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        token_key = None

        # 1. Headers dan token olish
        headers = dict(scope.get('headers', []))
        auth_header = headers.get(b'authorization', None)

        if auth_header:
            try:
                auth_header_str = auth_header.decode()
                if ' ' in auth_header_str:
                    token_key = auth_header_str.split(' ')[1]
                else:
                    token_key = auth_header_str
            except Exception as e:
                print(f"Header parse error: {e}")

        # 2. Agar headers da yo'q bo'lsa, query params dan olish
        if not token_key:
            query_string = scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            token_list = query_params.get('token', [])
            if token_list:
                token_key = token_list[0]

        # User authentication
        scope['user'] = await get_user(token_key)

        # Debug
        print(f"WebSocket Auth - User: {scope['user']}, Token found: {bool(token_key)}")

        return await self.inner(scope, receive, send)


TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(inner)
