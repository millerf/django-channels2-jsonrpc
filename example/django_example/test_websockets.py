from datetime import datetime
from channels_jsonrpc import JsonRpcConsumerTest, JsonRpcException
from channels.testing import WebsocketCommunicator
import pytest
from .routing import application
from .consumer import MyJsonRpcWebsocketConsumerTest

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter


# class TestMyJsonRpcConsumer(JsonRpcConsumerTest):
#     pass
#
#
# class TestMyJsonRpcConsumer2(JsonRpcConsumerTest):
#     pass


@pytest.mark.asyncio
async def test_connection():
    # Test connection
    communicator = WebsocketCommunicator(application, '')
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_response_are_well_formatted():
    # Answer should always json-rpc2
    communicator = WebsocketCommunicator(application, '')
    await communicator.connect()
    await communicator.send_json_to({'value': 'my_value'})

    response = await communicator.receive_json_from()
    assert response['error']['code'] == JsonRpcConsumerTest.INVALID_REQUEST
    assert response['error']['message'] == JsonRpcConsumerTest.errors[JsonRpcConsumerTest.INVALID_REQUEST]
    assert response['jsonrpc'] == '2.0'
    assert hasattr(response, 'id') is False
    await communicator.disconnect()

@pytest.mark.asyncio
async def test_inadequate_request():

    client = WebsocketCommunicator(application, '')
    await client.connect()

    await client.send_json_to({"value": "my_value"})
    response = await client.receive_json_from()
    assert(response['error'] ==
                     {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                     u'message': JsonRpcConsumerTest.errors[JsonRpcConsumerTest.INVALID_REQUEST]})

    await client.send_json_to(None)
    response = await client.receive_json_from()
    assert(response['error'] == {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                                                 u'message': JsonRpcConsumerTest.errors[
                                                     JsonRpcConsumerTest.INVALID_REQUEST]})

    await client.send_json_to(["value", "my_value"])
    response = await client.receive_json_from()
    assert(response['error'] == {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                                                 u'message': JsonRpcConsumerTest.errors[
                                                     JsonRpcConsumerTest.INVALID_REQUEST]})

    # missing "method"
    await client.send_json_to({"id":"2", "jsonrpc":"2.0", "params":{}})
    response = await client.receive_json_from()
    assert(response['error'] ==
                     {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                     u'message': JsonRpcConsumerTest.errors[JsonRpcConsumerTest.INVALID_REQUEST]})

    # wrong method name
    await client.send_json_to({"id":"2", "jsonrpc":"2.0", "method":2, "params":{}})
    response = await client.receive_json_from()
    assert(response['error'] == {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                                                 u'message': JsonRpcConsumerTest.errors[
                                                     JsonRpcConsumerTest.INVALID_REQUEST]})

    # wrong method name
    await client.send_json_to({"id":"2", "jsonrpc":"2.0", "method":"_test", "params":{}})
    response = await client.receive_json_from()
    assert(response['error'] == {u'code': JsonRpcConsumerTest.METHOD_NOT_FOUND,
                                                 u'message': JsonRpcConsumerTest.errors[
                                                     JsonRpcConsumerTest.METHOD_NOT_FOUND]})

    await client.send_json_to({"value": "my_value"})
    response = await client.receive_json_from()
    assert(response['error'] == {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                                                 u'message': JsonRpcConsumerTest.errors[
                                                     JsonRpcConsumerTest.INVALID_REQUEST]})

    await client.send_to(text_data='sqwdw')
    response = await client.receive_json_from()
    assert(response['error'] ==
                     {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                      u'message': JsonRpcConsumerTest.errors[JsonRpcConsumerTest.INVALID_REQUEST]})

    await client.send_json_to({})
    response = await client.receive_json_from()
    assert(response['error'] ==
                     {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
                     u'message': JsonRpcConsumerTest.errors[JsonRpcConsumerTest.INVALID_REQUEST]})


#     def test_unexisting_method():
#         # unknown method
#         client = HttpClient()
#
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id": 1, "jsonrpc": "2.0", "method": "unknown_method", "params": {}}')
#         msg = client.receive()
#         assert(msg['error'], {u'code': JsonRpcConsumerTest.METHOD_NOT_FOUND,
#                                         u'message': JsonRpcConsumerTest.errors[JsonRpcConsumerTest.METHOD_NOT_FOUND]})
#
#     def test_parsing_with_bad_request():
#         # Test that parsing a bad request works
#
#         client = HttpClient()
#
#         await communicator.send_json_to({"id":"2", "method":"ping2", "params":{}})
#         assert(client.receive()['error'],
#                          {u'code': JsonRpcConsumerTest.INVALID_REQUEST,
#                          u'message': JsonRpcConsumerTest.errors[JsonRpcConsumerTest.INVALID_REQUEST]})
#
#     def test_notification():
#         # Test that parsing a bad request works
#
#         client = HttpClient()
#
#         await communicator.send_json_to({"jsonrpc":"2.0", "method":"a_notif", "params":{}})
#         assert(client.receive(), None)
#
#     def test_method():
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def ping2():
#             return "pong2"
#
#         client = HttpClient()
#         await communicator.send_json_to({"id":1, "jsonrpc":"2.0", "method":"ping2", "params":{}})
#
#         msg = client.receive()
#
#         assert(msg['result'], "pong2")
#
#     def test_parsing_with_good_request_wrong_params():
#         @JsonRpcConsumerTest.rpc_method()
#         def ping2():
#             return "pong2"
#
#         # Test that parsing a ping request works
#         client = HttpClient()
#
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"ping2", "params":["test"]}')
#         msg = client.receive()
#         self.assertIn(msg['error']['message'],
#                       [u'ping2() takes no arguments (1 given)',               # python 2
#                        u'ping2() takes 0 positional arguments but 1 was given'])     # python 3
#
#     def test_parsing_with_good_request_ainvalid_paramas():
#         @JsonRpcConsumerTest.rpc_method()
#         def ping2(test):
#             return "pong2"
#
#         # Test that parsing a ping request works
#         client = HttpClient()
#
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"ping2", "params":true}')
#         msg = client.receive()
#         assert(msg['error'], {u'code': JsonRpcConsumerTest.INVALID_PARAMS,
#                                                      u'message': JsonRpcConsumerTest.errors[
#                                                          JsonRpcConsumerTest.INVALID_PARAMS]})
#
#     def test_parsing_with_good_request():
#         # Test that parsing a ping request works
#         client = HttpClient()
#
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"ping", "params":[false]}')
#         msg = client.receive()
#         asserts(msg['result'], "pong")
#
#     def test_id_on_good_request():
#         # Test that parsing a ping request works
#         client = HttpClient()
#
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":52, "jsonrpc":"2.0", "method":"ping", "params":{}}')
#         msg = client.receive()
#         assert(msg['id'], 52)
#
#     def test_id_on_errored_request():
#         # Test that parsing a ping request works
#         client = HttpClient()
#
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":52, "jsonrpc":"2.0", "method":"ping", "params":["test"]}')
#         msg = client.receive()
#         assert(msg['id'], 52)
#
#     def test_get_rpc_methods():
#
#         @TestMyJsonRpcConsumer.rpc_method()
#         def ping3():
#             return "pong3"
#
#         @TestMyJsonRpcConsumer2.rpc_method()
#         def ping4():
#             return "pong4"
#
#         methods = TestMyJsonRpcConsumer.get_rpc_methods()
#         asserts(methods, ['ping3'])
#         asserts(TestMyJsonRpcConsumer2.get_rpc_methods(), ['ping4'])
#
#     def test_get_rpc_methods_with_name():
#
#         class TestMyJsonRpcConsumer(JsonRpcConsumerTest):
#             pass
#
#         @TestMyJsonRpcConsumer.rpc_method('test.ping.rpc')
#         def ping5():
#             return "pong5"
#
#         asserts(TestMyJsonRpcConsumer.get_rpc_methods(), ['test.ping.rpc'])
#
#     def test_error_on_rpc_call():
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def ping_with_error():
#             raise Exception("pong_with_error")
#
#         # Test that parsing a ping request works
#         client = HttpClient()
#
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"ping_with_error", "params":{}}')
#         msg = client.receive()
#         assert(msg['error']['message'], u'pong_with_error')
#
#     def test_error_on_rpc_call_with_data():
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def ping_with_error_data():
#             raise Exception("test_data", True)
#
#         # Test that parsing a ping request works
#         client = HttpClient()
#
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"ping_with_error_data", "params":{}}')
#         msg = client.receive()
#         assert(msg['id'], 1)
#         assert(msg['error']['code'], JsonRpcConsumerTest.GENERIC_APPLICATION_ERROR)
#         assert(msg['error']['data'], ['test_data', True])
#
#
#     def test_JsonRpcWebsocketConsumerTest_clean():
#
#         class TestNamesakeJsonRpcConsumer(JsonRpcConsumerTest):
#             pass
#
#         @TestNamesakeJsonRpcConsumer.rpc_method()
#         def method_34():
#             pass
#
#         self.assertIn("method_34", TestNamesakeJsonRpcConsumer.get_rpc_methods())
#
#         TestNamesakeJsonRpcConsumer.clean()
#
#         asserts(TestNamesakeJsonRpcConsumer.get_rpc_methods(), [])
#
#     def test_namesake_consumers():
#
#         # Changed name to TestNamesakeJsonRpcConsumer2 to prevent overlapping with "previous" TestMyJsonRpcConsumer
#
#         class Context1():
#             class TestNamesakeJsonRpcConsumer2(JsonRpcConsumerTest):
#                 pass
#
#         class Context2():
#             class TestNamesakeJsonRpcConsumer2(JsonRpcConsumerTest):
#                 pass
#
#         Context1.TestNamesakeJsonRpcConsumer2.clean()
#         Context2.TestNamesakeJsonRpcConsumer2.clean()
#
#         @Context1.TestNamesakeJsonRpcConsumer2.rpc_method()
#         def method1():
#           pass
#
#         @Context2.TestNamesakeJsonRpcConsumer2.rpc_method()
#         def method2():
#           pass
#
#         asserts(Context1.TestNamesakeJsonRpcConsumer2.get_rpc_methods(), ['method1'])
#         asserts(Context2.TestNamesakeJsonRpcConsumer2.get_rpc_methods(), ['method2'])
#
#     def test_no_rpc_methods():
#         class TestNamesakeJsonRpcConsumer(JsonRpcConsumerTest):
#             pass
#
#         asserts(TestNamesakeJsonRpcConsumer.get_rpc_methods(), [])
#
#     def test_jsonRpcexception_dumping():
#         import json
#         exception = JsonRpcException(1, JsonRpcConsumerTest.GENERIC_APPLICATION_ERROR, data=[True, "test"])
#         json_res = json.loads(str(exception))
#         assert(json_res["id"], 1)
#         assert(json_res["jsonrpc"], "2.0")
#         assert(json_res["error"]["data"], [True, "test"])
#         assert(json_res["error"]["code"], JsonRpcConsumerTest.GENERIC_APPLICATION_ERROR)
#
#     def test_session_pass_param():
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def ping_set_session(**kwargs):
#             original_message = kwargs["original_message"]
#             original_message.channel_session["test"] = True
#             return "pong_set_session"
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def ping_get_session(**kwargs):
#             original_message = kwargs["original_message"]
#             assert(original_message.channel_session["test"], True)
#             return "pong_get_session"
#
#         client = HttpClient()
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"ping_set_session", "params":{}}')
#         msg = client.receive()
#         assert(msg['result'], "pong_set_session")
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"ping_get_session", "params":{}}')
#         msg = client.receive()
#         assert(msg['result'], "pong_get_session")
#
#     def test_Session():
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def ping_set_session2(**kwargs):
#             original_message = kwargs["original_message"]
#             original_message.channel_session["test"] = True
#             return "pong_set_session2"
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def ping_get_session2(**kwargs):
#             original_message = kwargs["original_message"]
#             self.assertNotIn("test", original_message.channel_session)
#             return "pong_get_session2"
#
#         client = HttpClient()
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"ping_set_session2", "params":{}}')
#         msg = client.receive()
#         assert(msg['result'], "pong_set_session2")
#
#         client2 = HttpClient()
#         client2.send_and_consume(u'websocket.receive',
#                                  text='{"id":1, "jsonrpc":"2.0", "method":"ping_get_session2", "params":{}}')
#         msg = client2.receive()
#         assert(msg['result'], "pong_get_session2")
#
#     def test_custom_json_encoder():
#         some_date = datetime.utcnow()
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def test_method():
#             return {
#                 'date': some_date
#             }
#
#         client = HttpClient()
#         try:
#             client.send_and_consume(u'websocket.receive',
#                                     text='{"id":1, "jsonrpc":"2.0", "method":"test_method", "params":{}}')
#             self.fail('Looks like test does not work')
#         except TypeError:
#             pass
#
#         @DjangoJsonRpcWebsocketConsumerTest.rpc_method()
#         def test_method1():
#             return {
#                 'date': some_date
#             }
#
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"test_method1", "params":{}}',
#                                 path='/django/')
#         msg = client.receive()
#         assert(msg['result'], {u'date': some_date.isoformat()[:-3]})
#
#     def test_message_is_not_thread_safe():
#
#         class SpoofMessage:
#
#             class Channel:
#                 def __init__():
#                     self.name = None
#
#             def __init__():
#                 self.channel = SpoofMessage.Channel()
#                 self.payload = None
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def ping2(**kwargs):
#             original_message = kwargs["original_message"]
#             return original_message.payload
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def ping3(**kwargs):
#             original_message = kwargs["original_message"]
#             return original_message.payload
#
#         def thread_test():
#             for _i in range(0, 10000):
#                 _message = SpoofMessage()
#                 _message.channel.name = "websocket.test"
#                 _message.payload = "test%s" % _i
#                 _res = MyJsonRpcWebsocketConsumerTest._JsonRpcConsumer__process(
#                     {"id": 1, "jsonrpc": "2.0", "method": "ping3", "params": []}, _message)
#                 assert(_res['result'], "test%s" % _i)
#
#         import threading
#         threading._start_new_thread(thread_test, ())
#
#         for i in range(0, 10000):
#             _message = SpoofMessage()
#             _message.channel.name = "websocket.test"
#             _message.payload = "test%s" % i
#             res = MyJsonRpcWebsocketConsumerTest._JsonRpcConsumer__process(
#                 {"id": 1, "jsonrpc": "2.0", "method": "ping2", "params": []}, _message)
#             assert(res['result'], "test%s" % i)
#
#     def test_original_message_position_safe():
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def ping_set_session(name, value, **kwargs):
#             original_message = kwargs["original_message"]
#             original_message.channel_session["test"] = True
#             return ["pong_set_session", value, name]
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def ping_get_session(value2, name2, **kwargs):
#             original_message = kwargs["original_message"]
#             assert(original_message.channel_session["test"], True)
#             return ["pong_get_session", value2, name2]
#
#         client = HttpClient()
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"ping_set_session", '
#                                      '"params":["name_of_function", "value_of_function"]}')
#         msg = client.receive()
#         assert(msg['result'], ["pong_set_session", "value_of_function", "name_of_function"])
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"ping_get_session", '
#                                      '"params":{"name2": "name2_of_function", "value2": "value2_of_function"}}')
#         msg = client.receive()
#         assert(msg['result'], ["pong_get_session", "value2_of_function", "name2_of_function"])
#
#     def test_websocket_param_in_decorator_for_method():
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method(websocket=False)
#         def ping():
#             return "pong"
#
#         client = HttpClient()
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"ping", '
#                                      '"params":[]}')
#         msg = client.receive()
#         assert(msg['error']['message'], "Method Not Found")
#
#     def test_websocket_param_in_decorator_for_notification():
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_notification(websocket=False)
#         def ping():
#             return "pong"
#
#         client = HttpClient()
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"jsonrpc":"2.0", "method":"ping", '
#                                      '"params":[]}')
#         msg = client.receive()
#         assert(msg, None)
#
#
# class TestsNotifications(ChannelTestCase):
#
#     def test_group_notifications():
#         from channels import Group
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def add_client_to_group(group_name, **kwargs):
#             original_message = kwargs["original_message"]
#             Group(group_name).add(original_message.reply_channel)
#             return True
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def send_to_group(group_name, **kwargs):
#             MyJsonRpcWebsocketConsumerTest.notify_group(group_name, "notification.notif", {"payload": 1234})
#             return True
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def send_to_reply_channel(**kwargs):
#             original_message = kwargs["original_message"]
#             MyJsonRpcWebsocketConsumerTest.notify_channel(original_message.reply_channel,
#                                                         "notification.ownnotif",
#                                                         {"payload": 12})
#             return True
#
#         def send_notif(_client):
#             _client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"send_to_group", "params":["group_test"]}')
#             # receive notif
#             msg = _client.receive()
#             assert(msg['method'], "notification.notif")
#             assert(msg['params'], {"payload": 1234})
#
#             # receive response
#             msg = _client.receive()
#             assert(msg['result'], True)
#
#         client = HttpClient()
#         client2 = HttpClient()
#
#         # we test own reply channel
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"send_to_reply_channel", "params": []}')
#
#         msg = client.receive()
#         asserts(msg['method'], "notification.ownnotif")
#         assert(msg['params'], {"payload": 12})
#
#         msg = client.receive()
#         assert(msg['result'], True)
#
#         # we add client to a group_test group
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"add_client_to_group", "params":["group_test"]}')
#         msg = client.receive()
#         assert(msg['result'], True)
#
#         msg = client.receive()
#         assert(msg, None)
#
#         # we make sure it works
#         send_notif(client)
#
#         # we make sure the second client didn't receive anything
#         msg = client2.receive()
#         assert(msg, None)
#
#         # we add the second client to another group
#         client2.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"add_client_to_group", "params":["group_test2"]}')
#         msg = client2.receive()
#         assert(msg['result'], True)
#
#         # send again
#         send_notif(client)
#
#         # we make sure the second client didn't receive anything
#         msg = client2.receive()
#         assert(msg, None)
#
#         # we add the second client to SAME group
#         client2.send_and_consume(u'websocket.receive',
#                                  text='{"id":1, "jsonrpc":"2.0", "method":"add_client_to_group", "params":["group_test"]}')
#         msg = client2.receive()
#         assert(msg['result'], True)
#
#         send_notif(client)
#
#         # now second client should receive (as well)
#         msg = client2.receive()
#         assert(msg['method'], "notification.notif")
#         assert(msg['params'], {"payload": 1234})
#
#         # notif from second client
#         send_notif(client2)
#
#         # now second client should receive (as well)
#         msg = client.receive()
#         assert(msg['method'], "notification.notif")
#         assert(msg['params'], {"payload": 1234})
#
#     def test_inbound_notifications():
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_notification()
#         def notif1(params, **kwargs):
#             assert(params, {"payload": True})
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_notification('notif.notif2')
#         def notif2(params, **kwargs):
#             assert(params, {"payload": 12345})
#
#         client = HttpClient()
#
#         # we send a notification to the server
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"jsonrpc":"2.0", "method":"notif1", "params":[{"payload": true}]}')
#         msg = client.receive()
#         assert(msg, None)
#
#         # we test with method rewriting
#         client.send_and_consume(u'websocket.receive',
#                             text='{"jsonrpc":"2.0", "method":"notif.notif2", "params":[{"payload": 12345}]}')
#         assert(msg, None)
#
#     def test_kwargs_not_there():
#
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def ping():
#             return True
#
#         client = HttpClient()
#
#         # we send a notification to the server
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"id":1, "jsonrpc":"2.0", "method":"ping", "params":[]}')
#         msg = client.receive()
#         assert(msg["result"], True)
#
#     def test_error_on_notification_frame():
#         @MyJsonRpcWebsocketConsumerTest.rpc_method()
#         def ping():
#             return True
#
#         client = HttpClient()
#
#         # we send a notification to the server
#         client.send_and_consume(u'websocket.receive',
#                                 text='{"jsonrpc":"2.0", "method":"dwqwdq", "params":[]}')
#         msg = client.receive()
#         assert(msg, None)
