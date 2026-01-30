"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from chat.chatmiddleware import TokenAuthMiddlewareStack
from chat.routing import websocket_urlpatterns as chat_ws_patterns
from stream.routing import websocket_urlpatterns as stream_ws_patterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddlewareStack(
        URLRouter(
            chat_ws_patterns + stream_ws_patterns
        )
    ),
})



# import os
# import django
# from django.core.asgi import get_asgi_application
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# django.setup()
#
# from channels.routing import ProtocolTypeRouter, URLRouter
# from chat.chatmiddleware import TokenAuthMiddlewareStack
# from chat.routing import websocket_urlpatterns
#
# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": TokenAuthMiddlewareStack(
#         URLRouter(websocket_urlpatterns)
#     ),
# })


