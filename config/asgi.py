"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from django.urls import re_path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django_asgi_app = get_asgi_application()
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.chatmiddleware import TokenAuthMiddleware
from chat.routing import websocket_urlpatterns



application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": TokenAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter([
                re_path(r"^ws/", URLRouter(websocket_urlpatterns)),
            ])
        )
    ),
})

# application = ProtocolTypeRouter(
#     {
#         # (http->django views is added by default)
#         "websocket": TokenAuthMiddleware(
#             URLRouter(chat.routing.websocket_urlpatterns)
#         )
#     }
# )