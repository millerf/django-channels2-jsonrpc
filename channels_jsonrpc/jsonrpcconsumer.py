import json
import logging
from channels.generic.websocket import JsonWebsocketConsumer, AsyncJsonWebsocketConsumer
from django.conf import settings
from six import string_types
from inspect import getfullargspec
keywords_args = 'varkw'

# Get an instance of a logger
logger = logging.getLogger(__name__)


class JsonRpcException(Exception):
    """
    >>> exc = JsonRpcException(1, JsonRpcConsumer.INVALID_REQUEST)
    >>> str(exc)
    '{"jsonrpc": "2.0", "id": 1, "error": {"message": "Invalid Request", "code": -32600}}'
    """

    def __init__(self, rpc_id, code, data=None):
        self.rpc_id = rpc_id
        self.code = code
        self.data = data

    @property
    def message(self):
        return RpcBase.errors[self.code]

    def as_dict(self):
        return RpcBase.error(self.rpc_id, self.code, self.message, self.data)

    def __str__(self):
        return json.dumps(self.as_dict())


class MethodNotSupported(Exception):
    pass


class RpcBase:
    """
        Variant of WebsocketConsumer that automatically JSON-encodes and decodes
        messages as they come in and go out. Expects everything to be text; will
        error on binary data.

        http://groups.google.com/group/json-rpc/web/json-rpc-2-0
        errors:
        code 	message 	meaning
        -32700 	Parse error 	Invalid JSON was received by the server.
                An error occurred on the server while parsing the JSON text.
        -32600 	Invalid Request 	The JSON sent is not a valid Request object.
        -32601 	Method not found 	The method does not exist / is not available.
        -32602 	Invalid params 	Invalid method parameter(s).
        -32603 	Internal error 	Internal JSON-RPC error.
        -32099 to -32000
                Server error 	Reserved for implementation-defined server-errors. (@TODO)
        """

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    GENERIC_APPLICATION_ERROR = -32000
    PARSE_RESULT_ERROR = -32701
    errors = dict()
    errors[PARSE_ERROR] = 'Parse Error'
    errors[INVALID_REQUEST] = 'Invalid Request'
    errors[METHOD_NOT_FOUND] = 'Method Not Found'
    errors[INVALID_PARAMS] = 'Invalid Params'
    errors[INTERNAL_ERROR] = 'Internal Error'
    errors[GENERIC_APPLICATION_ERROR] = 'Application Error'
    errors[PARSE_RESULT_ERROR] = 'Error while parsing result'

    available_rpc_methods = dict()
    available_rpc_notifications = dict()

    @classmethod
    def rpc_method(cls, rpc_name=None, websocket=True, http=True):
        """
        Decorator to list RPC methods available. An optional name and protocol rectrictions can be added
        :param rpc_name: RPC name for the function
        :param bool websocket: if websocket transport can use this function
        :param bool http:if http transport can use this function
        :return: decorated function
        """
        def wrap(f):
            name = rpc_name if rpc_name is not None else f.__name__
            cid = id(cls)
            if cid not in cls.available_rpc_methods:
                cls.available_rpc_methods[cid] = dict()
            f.options = dict(websocket=websocket, http=http)
            cls.available_rpc_methods[cid][name] = f

            return f

        return wrap

    @classmethod
    def get_rpc_methods(cls):
        """
        Returns the RPC methods available for this consumer
        :return: list
        """
        if id(cls) not in cls.available_rpc_methods:
            return []
        return list(cls.available_rpc_methods[id(cls)].keys())

    @classmethod
    def rpc_notification(cls, rpc_name=None, websocket=True, http=True):
        """
        Decorator to list RPC notifications available. An optional name can be added
        :param rpc_name: RPC name for the function
        :param bool websocket: if websocket transport can use this function
        :param bool http:if http transport can use this function
        :return: decorated function
        """
        def wrap(f):
            name = rpc_name if rpc_name is not None else f.__name__
            cid = id(cls)
            if cid not in cls.available_rpc_notifications:
                cls.available_rpc_notifications[cid] = dict()
            f.options = dict(websocket=websocket, http=http)
            cls.available_rpc_notifications[cid][name] = f
            return f

        return wrap

    @classmethod
    def get_rpc_notifications(cls):
        """
        Returns the RPC methods available for this consumer
        :return: list
        """
        if id(cls) not in cls.available_rpc_notifications:
            return []
        return list(cls.available_rpc_notifications[id(cls)].keys())

    @staticmethod
    def json_rpc_frame(_id=None, result=None, params=None, method=None, error=None):
        frame = {'jsonrpc': '2.0'}
        if _id is not None:
            frame['id'] = _id
        if method:
            frame['method'] = method
            frame['params'] = params
        elif result is not None:
            frame['result'] = result
        elif error is not None:
            frame['error'] = error

        return frame

    @staticmethod
    def error(_id, code, message, data=None):
        """
        Error-type answer generator
        :param _id: int
        :param code: code of the error
        :param message: message for the error
        :param data: (optional) error data
        :return: object
        """
        error = {'code': code, 'message': message}
        if data is not None:
            error['data'] = data

        return RpcBase.json_rpc_frame(error=error, _id=_id)

    def notify_channel(self, method, params):
        """
        Notify a group. Using JSON-RPC notificatons
        :param method: JSON-RPC method
        :param params: parmas of the method
        :return:
        """
        content = self.json_rpc_frame(method=method, params=params)
        self.send(self.encode_json(content))

    def rpc_validate(self, request: dict):
        """ Check id request is JSON-RPC compatible """
        if not isinstance(request, dict):
            raise JsonRpcException(None, self.INVALID_REQUEST)

        request_id = request.get('id')
        method_name = request.get('method')

        if method_name is None or method_name == '':
            raise JsonRpcException(request_id, self.INVALID_REQUEST)

        if request.get('jsonrpc') != "2.0":
            raise JsonRpcException(request_id, self.INVALID_REQUEST)

        if not isinstance(method_name, string_types):
            raise JsonRpcException(request_id, self.INVALID_REQUEST)

        if method_name.startswith('_'):
            raise JsonRpcException(request_id, self.METHOD_NOT_FOUND)

    def _get_method(self, data, is_notification):
        method_name = data['method']

        try:
            if is_notification:
                method = self.__class__.available_rpc_notifications[id(self.__class__)][method_name]
            else:
                method = self.__class__.available_rpc_methods[id(self.__class__)][method_name]
            # Test if the websocket or http header was at false
            proto = self.scope['type']
            if not method.options[proto]:
                raise MethodNotSupported(f'Method not available through {proto}')
        except (KeyError, MethodNotSupported):
            raise JsonRpcException(data.get('id'), self.METHOD_NOT_FOUND)

        return method

    def _get_params(self, data):
        params = data.get('params', [])
        if not isinstance(params, (list, dict)):
            raise JsonRpcException(data.get('id'), self.INVALID_PARAMS)
        return params

    def _method_call(self, method, params):
        func_args = getattr(getfullargspec(method), keywords_args)
        if func_args and 'kwargs' in func_args:
            if isinstance(params, list):
                result = method(*params, consumer=self)
            else:
                result = method(**params, consumer=self)
        else:
            if isinstance(params, list):
                result = method(*params)
            else:
                result = method(**params)

        return result


class JsonRpcWebsocketConsumer(JsonWebsocketConsumer, RpcBase):
    def decode_json(self, data):
        try:
            return json.loads(data)
        except json.decoder.JSONDecodeError:
            frame = self.error(None, self.PARSE_ERROR, self.errors[self.PARSE_ERROR])
            self.send_json(frame)
            return None

    def encode_json(self, data):
        try:
            return json.dumps(data)
        except TypeError:
            frame = self.error(None, self.PARSE_ERROR, self.errors[self.PARSE_RESULT_ERROR], '%s' % data['result'])
            return json.dumps(frame)

    def _process(self, rpc_request):
        is_notification = not bool(rpc_request.get('id'))
        method = self._get_method(rpc_request, is_notification=is_notification)
        params = self._get_params(rpc_request)

        # log call in debug mode
        if settings.DEBUG:
            logger.debug(f'Executing {method.__name__}({json.dumps(params)})')

        result = self._method_call(method, params)

        if not is_notification:
            if settings.DEBUG:
                logger.debug(f'Execution result: {result}')
            rpc_response = self.json_rpc_frame(result=result, _id=rpc_request.get('id'))
            self.send_json(rpc_response)

        elif result is not None:
            logger.warning(f'The notification method {method.__name__} shouldn`t return any result')

    def receive_json(self, rpc_request, **kwargs):
        try:
            self.rpc_validate(rpc_request)
            self._process(rpc_request)

        except JsonRpcException as ex:
            self.send_json(ex.as_dict())

        except Exception as ex:
            logger.debug('Application error', ex)
            rpc_response = self.error(rpc_request.get('id'),
                                      self.GENERIC_APPLICATION_ERROR,
                                      str(ex),
                                      ex.args[0] if len(ex.args) == 1 else ex.args)
            self.send_json(rpc_response)


class AsyncRpcBase(RpcBase):
    """ Override all async methods """
    async def _method_call(self, method, params):
        func_args = getattr(getfullargspec(method), keywords_args)

        if func_args and 'kwargs' in func_args:
            if isinstance(params, list):
                result = await method(*params, consumer=self)
            else:
                result = await method(**params, consumer=self)
        else:
            if isinstance(params, list):
                result = await method(*params)
            else:
                result = await method(**params)

        return result


class AsyncJsonRpcWebsocketConsumer(AsyncJsonWebsocketConsumer, AsyncRpcBase):
    async def _process(self, rpc_request):
        is_notification = not bool(rpc_request.get('id'))
        method = self._get_method(rpc_request, is_notification=is_notification)
        params = self._get_params(rpc_request)

        # log call in debug mode
        if settings.DEBUG:
            logger.debug(f'Executing {method.__name__}({json.dumps(params)})')

        result = await self._method_call(method, params)

        if not is_notification:
            if settings.DEBUG:
                logger.debug(f'Execution result: {result}')
            rpc_response = self.json_rpc_frame(result=result, _id=rpc_request.get('id'))
            await self.send_json(rpc_response)

        elif result is not None:
            logger.warning(f'The notification method {method.__name__} shouldn`t return any result')

    async def receive_json(self, rpc_request, **kwargs):
        try:
            self.rpc_validate(rpc_request)
            await self._process(rpc_request)

        except JsonRpcException as e:
            await self.send_json(e.as_dict())

        except Exception as e:
            logger.debug('Application error', e)
            rpc_response = self.error(rpc_request.get('id'),
                                      self.GENERIC_APPLICATION_ERROR,
                                      str(e),
                                      e.args[0] if len(e.args) == 1 else e.args)
            await self.send_json(rpc_response)

