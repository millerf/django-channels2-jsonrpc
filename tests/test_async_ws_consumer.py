import pytest
from channels.testing import WebsocketCommunicator
from channels_jsonrpc import AsyncJsonRpcWebsocketConsumer

INVALID_REQUEST = {'error': {'code': -32600, 'message': 'Invalid Request'}, 'jsonrpc': '2.0'}
INVALID_METHOD_NAME = {'error': {'code': -32600, 'message': 'Invalid Request'}, 'id': 1, 'jsonrpc': '2.0'}
METHOD_NOT_FOUND = {'error': {'code': -32601, 'message': 'Method Not Found'}, 'id': 1, 'jsonrpc': '2.0'}
INVALID_PARAMS = {'error': {'code': -32602, 'message': 'Invalid Params'}, 'id': 1, 'jsonrpc': '2.0'}
VALID_METHOD = {'id': 1, 'jsonrpc': '2.0', 'result': 'pong'}
VALID_METHOD_BOUNDED = {'id': 1, 'jsonrpc': '2.0', 'result': 'TestConsumer'}


@pytest.mark.asyncio
async def test_async_json_websocket_consumer():
    """
    Tests that AsyncJsonWebsocketConsumer is implemented correctly.
    """
    results = {}

    class TestConsumer(AsyncJsonRpcWebsocketConsumer):
        async def connect(self):
            await self.accept()

        async def receive_json(self, data=None, **kwargs):
            results['received'] = data
            await super().receive_json(data, **kwargs)

    @TestConsumer.rpc_method()
    async def registered_ping(param):
        return 'pong'

    @TestConsumer.rpc_method()
    async def registered_ping_named(param=None):
        return 'pong'

    @TestConsumer.rpc_method()
    async def registered_ping_bound(param, **kwargs):
        consumer = kwargs['consumer']
        return consumer.__class__.__name__

    app = TestConsumer()

    # Open a connection
    communicator = WebsocketCommunicator(app, '/ws/')
    connected, _ = await communicator.connect()
    assert connected

    # Test sending malformed rpc
    request = {'hello': 'world'}
    await communicator.send_json_to(request)
    response = await communicator.receive_json_from()
    assert response == INVALID_REQUEST
    assert results['received'] == request

    # Test sending malformed rpc (not dict)
    request = ['hello', 'world']
    await communicator.send_json_to(request)
    response = await communicator.receive_json_from()
    assert response == INVALID_REQUEST
    assert results['received'] == request

    # Test sending malformed rpc (no method name)
    request = {'id': 1, 'jsonrpc': '2.0'}
    await communicator.send_json_to(request)
    response = await communicator.receive_json_from()
    assert response == INVALID_METHOD_NAME
    assert results['received'] == request

    # Test sending malformed rpc (not registered method)
    request = {'id': 1, 'jsonrpc': '2.0', 'method': 'ping'}
    await communicator.send_json_to(request)
    response = await communicator.receive_json_from()
    assert response == METHOD_NOT_FOUND
    assert results['received'] == request

    # Test sending malformed rpc (single param w/o container)
    request = {'id': 1, 'jsonrpc': '2.0', 'method': 'registered_ping', 'params': 1}
    await communicator.send_json_to(request)
    response = await communicator.receive_json_from()
    assert response == INVALID_PARAMS
    assert results['received'] == request

    # # Test sending malformed rpc (single param) TODO: exposed internal error message
    # request = {'id': 1, 'jsonrpc': '2.0', 'method': 'registered_ping', 'params': [1, 2]}
    # await communicator.send_json_to(request)
    # response = await communicator.receive_json_from()
    # assert response == 'pong'
    # assert results['received'] == request

    # Test sending rpc (single positional param)
    request = {'id': 1, 'jsonrpc': '2.0', 'method': 'registered_ping', 'params': [1]}
    await communicator.send_json_to(request)
    response = await communicator.receive_json_from()
    assert response == VALID_METHOD
    assert results['received'] == request

    # Test sending rpc (single named param)
    request = {'id': 1, 'jsonrpc': '2.0', 'method': 'registered_ping_named', 'params': {'param': 1}}
    await communicator.send_json_to(request)
    response = await communicator.receive_json_from()
    assert response == VALID_METHOD
    assert results['received'] == request

    # # Test sending rpc (single named param with invalid name) TODO: exposed internal error message
    # request = {'id': 1, 'jsonrpc': '2.0', 'method': 'registered_ping_named', 'params': {'a': 1}}
    # await communicator.send_json_to(request)
    # response = await communicator.receive_json_from()
    # assert response == VALID_METHOD
    # assert results['received'] == request

    # Test sending rpc (with consumer instance usage)
    request = {'id': 1, 'jsonrpc': '2.0', 'method': 'registered_ping_bound', 'params': [1]}
    await communicator.send_json_to(request)
    response = await communicator.receive_json_from()
    assert response == VALID_METHOD_BOUNDED
    assert results['received'] == request
