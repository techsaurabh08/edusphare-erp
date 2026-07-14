import os
from django.core.asgi import get_asgi_application

# Ensure Django is initialized before we import Channels code
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edusphere_project.settings')
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import portal.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            portal.routing.websocket_urlpatterns
        )
    ),
})
