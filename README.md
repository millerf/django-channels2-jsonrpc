# Django-channels2-jsonrpc


--------------


For channels 1, see [here](https://github.com/millerf/django-channels-jsonrpc)



--------------

[![PyPI version](https://badge.fury.io/py/django-channels2-jsonrpc.svg)](https://badge.fury.io/py/django-channels2-jsonrpc) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/b95e52e1177443e283ebeb3ebaf35df4)](https://www.codacy.com/manual/fab/django-channels2-jsonrpc?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=millerf/django-channels2-jsonrpc&amp;utm_campaign=Badge_Grade) [![Build Status](https://travis-ci.org/millerf/django-channels2-jsonrpc.svg?branch=master)](https://travis-ci.org/millerf/django-channels2-jsonrpc) [![Coverage Status](https://coveralls.io/repos/github/millerf/django-channels2-jsonrpc/badge.svg)](https://coveralls.io/github/millerf/django-channels2-jsonrpc) [![Code Climate](https://codeclimate.com/github/millerf/django-channels2-jsonrpc/badges/gpa.svg)](https://codeclimate.com/github/millerf/django-channels2-jsonrpc)

The Django-channels2-jsonrpc is aimed to enable [JSON-RPC](http://json-rpc.org/) functionnality on top of the excellent django channels project and especially their Websockets functionality.
It is aimed to be:
  - Fully integrated with Channels
  - Fully implement JSON-RPC 1 and 2 protocol
  - Support both WebSocket and HTTP transports
  - Easy integration

## Tech


The only Django-channels-jsonrpc dependency is the [Django channels project](https://github.com/django/channels)

## Installation


Download and extract the [latest pre-built release](https://github.com/joemccann/dillinger/releases).

Install the dependencies and devDependencies and start the server.

```sh
$ pip install django-channels2-jsonrpc
```


## Use


See complete example [here](https://github.com/millerf/django-channels2-jsonrpc/blob/master/example/django_example/), and in particular [consumer.py](https://github.com/millerf/django-channels2-jsonrpc/blob/master/example/django_example/consumer.py)

It is intended to be used as a Websocket consumer. See [documentation](https://channels.readthedocs.io/en/latest/topics/consumers.html#websocketconsumer) except... simplier...

Import JsonRpcWebsocketConsumer, AsyncJsonRpcWebsocketConsumer or  AsyncRpcHttpConsumer class and create the consumer

```python
from channels_jsonrpc import JsonRpcWebsocketConsumer

class MyJsonRpcConsumer(JsonRpcConsumer):

    def connect(self, message, **kwargs):
        """
		Perform things on WebSocket connection start
		"""
		self.accept()

        print("connect")
        # Do stuff if needed

  def disconnect(self, message, **kwargs):
        """
		 Perform things on WebSocket connection close
		"""  print("disconnect")
        # Do stuff if needed

```
JsonRpcWebsocketConsumer derives from Channels JsonWebsocketConsumer, you can read about all it's features here:
[https://channels.readthedocs.io/en/latest/topics/consumers.html#websocketconsumer](https://channels.readthedocs.io/en/latest/topics/consumers.html#websocketconsumer)
Then the last step is to create the RPC methos hooks. IT is done with the decorator:
```python
@MyJsonRpcConsumer.rpc_method()
````


Like this:

```python
@MyJsonRpcConsumer.rpc_method()
def ping():
    return "pong"
```


**MyJsonRpcConsumer.rpc_method()** accept a *string* as a parameter to 'rename' the function
```python
@MyJsonRpcConsumer.rpc_method("mymodule.rpc.ping")
def ping():
    return "pong"
```

Will now be callable with "method":"mymodule.rpc.ping" in the rpc call:
```javascript
{"id":1, "jsonrpc":"2.0","method":"mymodule.rpc.ping","params":{}}
```

RPC methods can obviously accept parameters. They also return "results" or "errors":
```python
@MyJsonRpcConsumer.rpc_method("mymodule.rpc.ping")
def ping(fake_an_error):
    if fake_an_error:
        # Will return an error to the client
 #  --> {"id":1, "jsonrpc":"2.0","method":"mymodule.rpc.ping","params":{}} #  <-- {"id": 1, "jsonrpc": "2.0", "error": {"message": "fake_error", "code": -32000, "data": ["fake_error"]}}  raise Exception("fake_error")
    else:
        # Will return a result to the client
 #  --> {"id":1, "jsonrpc":"2.0","method":"mymodule.rpc.ping","params":{}} #  <-- {"id": 1, "jsonrpc": "2.0", "result": "pong"}  return "pong"
```



## Async Use

Simply derive your customer from an asynchronous customer like `AsyncJsonRpcWebsocketConsumer`


```python
from channels_jsonrpc import AsyncJsonRpcWebsocketConsumer

class MyAsyncJsonRpcConsumer(AsyncJsonRpcWebsocketConsumer):
	pass

@MyAsyncJsonRpcConsumer.rpc_method("mymodule.rpc.ping")
async def ping(fake_an_error):
	return "ping"
```

## [Sessions and other parameters from Consumer object](#consumer)
The original channel message - that can contain sessions (if activated with [http_user](https://channels.readthedocs.io/en/stable/generics.html#websockets)) and other important info  can be easily accessed by retrieving the `**kwargs` and get a parameter named *consumer*

```python
MyJsonRpcConsumerTest.rpc_method()
def json_rpc_method(param1, **kwargs):
    consumer = kwargs["consumer"]
    ##do something with consumer
```

Example:

```python
class MyJsonRpcConsumerTest(JsonRpcConsumer):
    # Set to True to automatically port users from HTTP cookies
 # (you don't need channel_session_user, this implies it) # https://channels.readthedocs.io/en/stable/generics.html#websockets  http_user = True

....

@MyJsonRpcConsumerTest.rpc_method()
    def ping(**kwargs):
        consumer = kwargs["consumer"]
        consumer.scope["session"]["test"] = True
  return "pong"

```

## Custom JSON encoder class
  `Same as Channels. See` [here](https://channels.readthedocs.io/en/latest/topics/consumers.html#jsonwebsocketconsumer)

## Testing


The JsonRpcConsumer class can be tested the same way Channels Consumers are tested.
See [here](http://channels.readthedocs.io/en/stable/testing.html)


## License


MIT

*Have fun with Websockets*!

**Free Software, Hell Yeah!**

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)
