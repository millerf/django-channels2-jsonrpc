from datetime import datetime
from channels_jsonrpc import JsonRpcConsumerTest, JsonRpcException
from channels.testing import WebsocketCommunicator
from .routing import application
from .consumer import MyJsonRpcWebsocketConsumerTest, DjangoJsonRpcWebsocketConsumerTest

from channels.routing import ProtocolTypeRouter, URLRouter


class MyJsonRpcConsumer(JsonRpcConsumerTest):
    pass


class MyJsonRpcConsumer2(JsonRpcConsumerTest):
    pass


import aiounittest


class MyTest(aiounittest.AsyncTestCase):

    async def test_connection(self):
        # Test connection
        communicator = WebsocketCommunicator(application, 'ws/')
        connected, subprotocol = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_response_are_well_formatted(self):
        # Answer should always json-rpc2
        communicator = WebsocketCommunicator(application, 'ws/')
        await communicator.connect()
        await communicator.send_json_to({'value': 'my_value'})

        response = await communicator.receive_json_from()
        assert response['error']['code'] == JsonRpcConsumerTest.INVALID_REQUEST
        assert response['error']['message'] == JsonRpcConsumerTest.errors[JsonRpcConsumerTest.INVALID_REQUEST]
        assert response['jsonrpc'] == '2.0'
        assert hasattr(response, 'id') is False
        await communicator.disconnect()

    async def test_inadequate_request(self):

        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()

        await client.send_json_to({"value": "my_value"})
        response = await client.receive_json_from()
        assert (response['error'] ==
                {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                 u'message': JsonRpcConsumerTest.errors[JsonRpcConsumerTest.INVALID_REQUEST]})

        await client.send_json_to(None)
        response = await client.receive_json_from()
        assert (response['error'] == {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                                      u'message': JsonRpcConsumerTest.errors[
                                          JsonRpcConsumerTest.INVALID_REQUEST]})

        await client.send_json_to(["value", "my_value"])
        response = await client.receive_json_from()
        assert (response['error'] == {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                                      u'message': JsonRpcConsumerTest.errors[
                                          JsonRpcConsumerTest.INVALID_REQUEST]})

        # missing "method"
        await client.send_json_to({"id": "2", "jsonrpc": "2.0", "params": {}})
        response = await client.receive_json_from()
        assert (response['error'] ==
                {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                 u'message': JsonRpcConsumerTest.errors[JsonRpcConsumerTest.INVALID_REQUEST]})

        # wrong method name
        await client.send_json_to({"id": "2", "jsonrpc": "2.0", "method": 2, "params": {}})
        response = await client.receive_json_from()
        assert (response['error'] == {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                                      u'message': JsonRpcConsumerTest.errors[
                                          JsonRpcConsumerTest.INVALID_REQUEST]})

        # wrong method name
        await client.send_json_to({"id": "2", "jsonrpc": "2.0", "method": "_test", "params": {}})
        response = await client.receive_json_from()
        assert (response['error'] == {u'code': JsonRpcConsumerTest.METHOD_NOT_FOUND,
                                      u'message': JsonRpcConsumerTest.errors[
                                          JsonRpcConsumerTest.METHOD_NOT_FOUND]})

        await client.send_json_to({"value": "my_value"})
        response = await client.receive_json_from()
        assert (response['error'] == {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                                      u'message': JsonRpcConsumerTest.errors[
                                          JsonRpcConsumerTest.INVALID_REQUEST]})

        await client.send_to(text_data='sqwdw')
        response = await client.receive_json_from()
        assert (response['error'] ==
                {u'code': JsonRpcConsumerTest.PARSE_ERROR,
                 u'message': JsonRpcConsumerTest.errors[JsonRpcConsumerTest.PARSE_ERROR]})

        await client.send_json_to({})
        response = await client.receive_json_from()
        assert (response['error'] ==
                {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                 u'message': JsonRpcConsumerTest.errors[JsonRpcConsumerTest.INVALID_REQUEST]})

        await client.disconnect()

    async def test_unexisting_method(self):
        # unknown method
        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()
        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "unknown_method", "params": {}})
        response = await client.receive_json_from()
        assert (response['error'] == {u'code': JsonRpcConsumerTest.METHOD_NOT_FOUND,
                                      u'message': JsonRpcConsumerTest.errors[JsonRpcConsumerTest.METHOD_NOT_FOUND]})
        await client.disconnect()

    async def test_parsing_with_bad_request(self):
        # Test that parsing a bad request works

        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()

        await client.send_json_to({"id": "2", "method": "ping2", "params": {}})
        response = await client.receive_json_from()
        assert (response['error'] ==
                {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                 u'message': JsonRpcConsumerTest.errors[JsonRpcConsumerTest.INVALID_REQUEST]})
        await client.disconnect()

    async def test_notification(self):
        # Test that parsing a bad request works

        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()
        await client.send_json_to({"jsonrpc": "2.0", "method": "a_notif", "params": {}})
        assert await client.receive_nothing() is True
        await client.disconnect()

    async def test_method(self):

        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping2():
            return "pong2"

        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()
        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping2", "params": {}})

        response = await client.receive_json_from()
        assert (response['result'] == "pong2")
        await client.disconnect()

    async def test_parsing_with_good_request_wrong_params(self):
        @JsonRpcConsumerTest.rpc_method()
        def ping2():
            return "pong2"

        # Test that parsing a ping request works
        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()

        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping2", "params": ["test"]})
        msg = await client.receive_json_from()
        self.assertIn(msg['error']['message'],
                      [u'ping2() takes no arguments (1 given)',  # python 2
                       u'ping2() takes 0 positional arguments but 1 was given'])  # python 3
        await client.disconnect()

    async def test_parsing_with_good_request_ainvalid_paramas(self):
        @JsonRpcConsumerTest.rpc_method()
        def ping2(test):
            return "pong2"

        # Test that parsing a ping request works
        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()
        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping2", "params": True})
        msg = await client.receive_json_from()
        self.assertEqual(msg['error'], {u'code': JsonRpcConsumerTest.INVALID_PARAMS,
                                        u'message': JsonRpcConsumerTest.errors[
                                            JsonRpcConsumerTest.INVALID_PARAMS]})
        await client.disconnect()

    async def test_parsing_with_good_request(self):
        # Test that parsing a ping request works
        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()
        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping", "params": [False]})
        msg = await client.receive_json_from()
        self.assertEqual(msg['result'], "pong")
        await client.disconnect()

    async def test_id_on_good_request(self):
        # Test that parsing a ping request works
        client = WebsocketCommunicator(application, 'ws/')

        await client.send_json_to({"id": 52, "jsonrpc": "2.0", "method": "ping", "params": {}})
        msg = await client.receive_json_from()
        self.assertEqual(msg['id'], 52)
        await client.disconnect()

    async def test_id_on_errored_request(self):
        # Test that parsing a ping request works
        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()

        await client.send_json_to({"id": 52, "jsonrpc": "2.0", "method": "ping", "params": ["test"]})
        msg = await client.receive_json_from()
        self.assertEqual(msg['id'], 52)
        await client.disconnect()

    async def test_get_rpc_methods(self):

        @MyJsonRpcConsumer.rpc_method()
        def ping3():
            return "pong3"

        @MyJsonRpcConsumer2.rpc_method()
        def ping4():
            return "pong4"

        methods = MyJsonRpcConsumer.get_rpc_methods()
        self.assertEqual(methods, ['ping3'])
        self.assertEqual(MyJsonRpcConsumer2.get_rpc_methods(), ['ping4'])

    async def test_get_rpc_methods_with_name(self):

        class MyJsonRpcConsumer(JsonRpcConsumerTest):
            pass

        @MyJsonRpcConsumer.rpc_method('test.ping.rpc')
        def ping5():
            return "pong5"

        self.assertEqual(MyJsonRpcConsumer.get_rpc_methods(), ['test.ping.rpc'])

    async def test_error_on_rpc_call(self):
        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping_with_error():
            raise Exception("pong_with_error")

        # Test that parsing a ping request works
        client = WebsocketCommunicator(application, 'ws/')

        await client.connect()

        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping_with_error", "params": {}})
        msg = await client.receive_json_from()
        self.assertEqual(msg['error']['message'], u'pong_with_error')
        await client.disconnect()

    async def test_error_on_rpc_call_with_data(self):
        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping_with_error_data():
            raise Exception("test_data", True)

        # Test that parsing a ping request works
        client = WebsocketCommunicator(application, 'ws/')

        await client.connect()

        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping_with_error_data", "params": {}})
        msg = await client.receive_json_from()
        self.assertEqual(msg['id'], 1)
        self.assertEqual(msg['error']['code'], JsonRpcConsumerTest.GENERIC_APPLICATION_ERROR)
        self.assertEqual(msg['error']['data'], ['test_data', True])
        await client.disconnect()

    async def test_JsonRpcWebsocketConsumerTest_clean(self):

        class TestNamesakeJsonRpcConsumer(JsonRpcConsumerTest):
            pass

        @TestNamesakeJsonRpcConsumer.rpc_method()
        def method_34():
            pass

        self.assertIn("method_34", TestNamesakeJsonRpcConsumer.get_rpc_methods())

        TestNamesakeJsonRpcConsumer.clean()

        self.assertEqual(TestNamesakeJsonRpcConsumer.get_rpc_methods(), [])

    async def test_namesake_consumers(self):

        # Changed name to TestNamesakeJsonRpcConsumer2 to prevent overlapping with "previous" MyJsonRpcConsumer

        class Context1():
            class TestNamesakeJsonRpcConsumer2(JsonRpcConsumerTest):
                pass

        class Context2():
            class TestNamesakeJsonRpcConsumer2(JsonRpcConsumerTest):
                pass

        Context1.TestNamesakeJsonRpcConsumer2.clean()
        Context2.TestNamesakeJsonRpcConsumer2.clean()

        @Context1.TestNamesakeJsonRpcConsumer2.rpc_method()
        def method1():
            pass

        @Context2.TestNamesakeJsonRpcConsumer2.rpc_method()
        def method2():
            pass

        self.assertEqual(Context1.TestNamesakeJsonRpcConsumer2.get_rpc_methods(), ['method1'])
        self.assertEqual(Context2.TestNamesakeJsonRpcConsumer2.get_rpc_methods(), ['method2'])

    async def test_no_rpc_methods(self):
        class TestNamesakeJsonRpcConsumer(JsonRpcConsumerTest):
            pass

        self.assertEqual(TestNamesakeJsonRpcConsumer.get_rpc_methods(), [])

    async def test_jsonRpcexception_dumping(self):
        import json
        exception = JsonRpcException(1, JsonRpcConsumerTest.GENERIC_APPLICATION_ERROR, data=[True, "test"])
        json_res = json.loads(str(exception))
        self.assertEqual(json_res["id"], 1)
        self.assertEqual(json_res["jsonrpc"], "2.0")
        self.assertEqual(json_res["error"]["data"], [True, "test"])
        self.assertEqual(json_res["error"]["code"], JsonRpcConsumerTest.GENERIC_APPLICATION_ERROR)

    async def test_session_pass_param(self):
        from channels.sessions import SessionMiddlewareStack
        from .routing import websocket_urlpatterns

        application = ProtocolTypeRouter({
            'websocket': SessionMiddlewareStack(
                URLRouter(
                    websocket_urlpatterns
                )
            ),
        })

        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping_set_session(**kwargs):
            kwargs['consumer'].scope["session"]["test"] = True
            return "pong_set_session"

        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping_get_session(**kwargs):
            assert (kwargs['consumer'].scope["session"]["test"] is True)
            return "pong_get_session"

        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()

        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping_set_session", "params": {}})
        msg = await client.receive_json_from()
        self.assertEqual(msg['result'], "pong_set_session")
        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping_get_session", "params": {}})
        msg = await client.receive_json_from()
        self.assertEqual(msg['result'], "pong_get_session")
        await client.disconnect()

    async def test_Session(self):

        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping_set_session2(**kwargs):
            kwargs['consumer'].scope["session"]["test"] = True
            return "pong_set_session2"

        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping_get_session2(**kwargs):
            self.assertNotIn("test", kwargs['consumer'].scope["session"])
            return "pong_get_session2"

        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()

        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping_set_session2", "params": {}})
        msg = await client.receive_json_from()
        self.assertEqual(msg['result'], "pong_set_session2")

        client2 = WebsocketCommunicator(application, 'ws/')

        await client2.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping_get_session2", "params": {}})
        msg = await client2.receive_json_from()
        self.assertEqual(msg['result'], "pong_get_session2")
        await client.disconnect()
        await client2.disconnect()

    async def test_custom_json_encoder(self):
        some_date = datetime.utcnow()

        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def test_method():
            return {
                'date': some_date
            }


        @DjangoJsonRpcWebsocketConsumerTest.rpc_method()
        def test_method1():
            return {
                'date': some_date
            }

        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()
        client_django = WebsocketCommunicator(application, 'django/')
        await client_django.connect()

        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "test_method", "params": {}})
        msg = await client.receive_json_from()
        assert (msg['error']['code'] == JsonRpcConsumerTest.PARSE_ERROR)
        assert (msg['error']['message'] == JsonRpcConsumerTest.errors[JsonRpcConsumerTest.PARSE_RESULT_ERROR])

        await client_django.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "test_method1", "params": {}})
        msg = await client_django.receive_json_from()
        self.assertEqual(msg['result'], {u'date': some_date.isoformat()[:-3]})
        await client.disconnect()
        await client_django.disconnect()

    async def test_original_message_position_safe(self):

        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping_set_session(name, value, **kwargs):
            consumer = kwargs["consumer"]
            consumer.scope["session"]["test"] = True
            return ["pong_set_session", value, name]

        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping_get_session(value2, name2, **kwargs):
            consumer = kwargs["consumer"]
            self.assertEqual(consumer.scope['session']['test'], True)
            return ["pong_get_session", value2, name2]

        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()

        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping_set_session",
                                   "params": ["name_of_function", "value_of_function"]})
        msg = await client.receive_json_from()
        self.assertEqual(msg['result'], ["pong_set_session", "value_of_function", "name_of_function"])
        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping_get_session",
                                   "params": {"name2": "name2_of_function", "value2": "value2_of_function"}})
        msg = await client.receive_json_from()
        self.assertEqual(msg['result'], ["pong_get_session", "value2_of_function", "name2_of_function"])
        await client.disconnect()

    async def test_websocket_param_in_decorator_for_method(self):

        @MyJsonRpcWebsocketConsumerTest.rpc_method(websocket=False)
        def ping():
            return "pong"

        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()

        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping", "params": []})
        msg = await client.receive_json_from()
        self.assertEqual(msg['error']['message'], "Method Not Found")
        await client.disconnect()

    async def test_websocket_param_in_decorator_for_notification(self):

        @MyJsonRpcWebsocketConsumerTest.rpc_notification(websocket=False)
        def ping():
            return "pong"

        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()

        await client.send_json_to({"jsonrpc": "2.0", "method": "ping", "params": []})
        # Should display an error in the back
        # The notification method shouldn't return any result
        # method: ping, params: []
        self.assertEqual(await client.receive_nothing(), True)
        await client.disconnect()


class TestsNotifications(aiounittest.AsyncTestCase):

    async def test_channel_notifications(self):

        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def send_to_reply_channel(**kwargs):
            consumer = kwargs["consumer"]
            consumer.notify_channel("notification.ownnotif",
                                                        {"payload": 12})
            return True

        client = WebsocketCommunicator(application, 'ws/')

        client2 = WebsocketCommunicator(application, 'ws/')

        # we test own reply channel
        await client.send_json_to({"id":1, "jsonrpc":"2.0", "method": "send_to_reply_channel", "params": []})

        msg = await client.receive_json_from()
        self.assertEqual(msg['method'], "notification.ownnotif")
        self.assertEqual(msg['params'], {"payload": 12})

        msg = await client.receive_json_from()
        self.assertEqual(msg['result'], True)

        await client.disconnect()
        await client2.disconnect()

    async def test_inbound_notifications(self):
        @MyJsonRpcWebsocketConsumerTest.rpc_notification()
        def notif1(params, **kwargs):
            self.assertEqual(params, {"payload": True})

        @MyJsonRpcWebsocketConsumerTest.rpc_notification('notif.notif2')
        def notif2(params, **kwargs):
            self.assertEqual(params, {"payload": 12345})

        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()

        # we send a notification to the server
        await client.send_json_to({"jsonrpc": "2.0", "method": "notif1", "params": [{"payload": True}]})
        self.assertEqual(await client.receive_nothing(), True)

        # we test with method rewriting
        await client.send_json_to({"jsonrpc": "2.0", "method": "notif.notif2", "params": [{"payload": 12345}]})
        self.assertEqual(await client.receive_nothing(), True)
        await client.disconnect()

    async def test_kwargs_not_there(self):
        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping():
            return True

        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()

        # we send a notification to the server
        await client.send_json_to({"id": 1, "jsonrpc": "2.0", "method": "ping", "params": []})
        msg = await client.receive_json_from()
        self.assertEqual(msg["result"], True)
        await client.disconnect()

    async def test_error_on_notification_frame(self):
        @MyJsonRpcWebsocketConsumerTest.rpc_method()
        def ping():
            return True

        client = WebsocketCommunicator(application, 'ws/')
        await client.connect()

        # we send a notification to the server
        await client.send_json_to({"jsonrpc": "2.0", "method": "dwqwdq", "params": []})
        self.assertEqual(await client.receive_nothing(), True)
        await client.disconnect()
