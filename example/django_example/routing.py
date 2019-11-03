from .consumer import MyJsonRpcWebsocketConsumerTest, DjangoJsonRpcWebsocketConsumerTest
from django.urls import re_path


channel_routing = [
    re_path(r"^/django/$", DjangoJsonRpcWebsocketConsumerTest),
    re_path(r"", MyJsonRpcWebsocketConsumerTest)
]
