from .consumer import MyJsonRpcWebsocketConsumerTest, DjangoJsonRpcWebsocketConsumerTest
from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.conf.urls import url

websocket_urlpatterns = [
    url(r'^django/$', DjangoJsonRpcWebsocketConsumerTest),
    url(r'^ws/', MyJsonRpcWebsocketConsumerTest),
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})