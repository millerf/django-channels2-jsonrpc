from django.core.serializers.json import DjangoJSONEncoder

from .consumer_test import JsonRpcConsumerTest
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class MyJsonRpcWebsocketConsumerTest(JsonRpcConsumerTest):

    def connection_groups(self, **kwargs):
        """
        Called to return the list of groups to automatically add/remove
        this connection to/from.
        """
        return ["test"]

    def connect(self):
        """
        Perform things on connection start
        """
        logger.info("connect")
        self.accept()

        # reject
        # self.close()

    def disconnect(self, close_code):
        """
        Perform things on connection close
        """
        logger.info("disconnect")

        # Do stuff if needed

    def process(cls, data, original_msg):
        """
        Made to test thread-safe
        :param data:
        :param original_msg:
        :return:
        """

        return cls.__process(data, original_msg)


@MyJsonRpcWebsocketConsumerTest.rpc_method()
def ping(fake_an_error, **kwargs):
    if fake_an_error:
        # Will return an error to the client
        #  --> {"id":1, "jsonrpc":"2.0","method":"mymodule.rpc.ping","params":{}}
        #  <-- {"id": 1, "jsonrpc": "2.0", "error": {"message": "fake_error", "code": -32000, "data": ["fake_error"]}}
        raise Exception(False)
    else:
        # Will return a result to the client
        #  --> {"id":1, "jsonrpc":"2.0","method":"mymodule.rpc.ping","params":{}}
        #  <-- {"id": 1, "jsonrpc": "2.0", "result": "pong"}
        return "pong"


class DjangoJsonRpcWebsocketConsumerTest(JsonRpcConsumerTest):

    def encode_json(self, data):
        return DjangoJSONEncoder().encode(data)
