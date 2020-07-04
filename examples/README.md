# Usage Exanples

## RPC Server

### AMQP

```python
#!/usr/bin/env python

from commlib_py.transports.amqp import RPCServer, ConnectionParameters


def callback(msg, meta):
    return msg


if __name__ == '__main__':
    rpc_name = 'test_rpc'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'r4a-platform.ddns.net'
    conn_params.port = 5782
    rpcs = RPCServer(conn_params, on_request=callback, rpc_name=rpc_name)
    rpcs.run_forever()
```

### Redis

```python
#!/usr/bin/env python

from commlib_py.transports.redis import RPCServer, ConnectionParameters


def callback(msg, meta):
    return msg


if __name__ == '__main__':
    rpc_name = 'test_rpc'
    conn_params = ConnectionParameters()
    rpcs = RPCServer(conn_params, on_request=callback, rpc_name=rpc_name)
    rpcs.run_forever()
```

## RPC Client

### AMQP

```python
#!/usr/bin/env python

from commlib_py.transports.amqp import RPCClient, ConnectionParameters


if __name__ == '__main__':
    rpc_name = 'test_rpc'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'r4a-platform.ddns.net'
    conn_params.port = 5782
    rpcc = RPCClient(conn_params=conn_params, rpc_name=rpc_name)
    data = {'a': 1, 'b': 'aa'}
    resp = rpcc.call(data)
    print(resp)
```

### Redis

```python
#!/usr/bin/env python

from commlib_py.transports.redis import RPCClient, ConnectionParameters


if __name__ == '__main__':
    rpc_name = 'test_rpc'
    conn_params = ConnectionParameters()
    rpcc = RPCClient(conn_params=conn_params, rpc_name=rpc_name)
    data = {'a': 1, 'b': 'aa'}
    resp = rpcc.call(data)
    print(resp)
```

## Publisher

### AMQP

```python
#!/usr/bin/env python

from commlib_py.transports.amqp import Publisher, ConnectionParameters
import time


if __name__ == '__main__':
    topic_name = 'testtopic'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'r4a-platform.ddns.net'
    conn_params.port = 5782
    p = Publisher(conn_params=conn_params,
                  topic=topic_name)
    data = {'state': 0}
    while True:
        try:
            p.publish(data)
            time.sleep(2)
        except:
            break

```

### Redis

```python
#!/usr/bin/env python

from commlib_py.transports.redis import Publisher, ConnectionParameters
import time


if __name__ == '__main__':
    topic_name = 'testtopic'
    conn_params = ConnectionParameters()
    p = Publisher(conn_params=conn_params,
                  topic=topic_name)
    data = {'state': 0}
    while True:
        try:
            p.publish(data)
            time.sleep(2)
        except:
            break

```

## Subscriber

### AMQP

```python
#!/usr/bin/env python

from commlib_py.transports.amqp import Subscriber, ConnectionParameters


def callback(msg, meta):
    print('Message: {}'.format(msg))


if __name__ == '__main__':
    topic_name = 'testtopic'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'r4a-platform.ddns.net'
    conn_params.port = 5782
    s = Subscriber(conn_params=conn_params,
                   topic=topic_name,
                   on_message=callback)
    s.run_forever()
```

### Redis

```python
#!/usr/bin/env python

from commlib_py.transports.amqp import Subscriber, ConnectionParameters


def callback(msg, meta):
    print('Message: {}'.format(msg))


if __name__ == '__main__':
    topic_name = 'testtopic'
    conn_params = ConnectionParameters()
    conn_params.credentials.username = 'testuser'
    conn_params.credentials.password = 'testuser'
    conn_params.host = 'r4a-platform.ddns.net'
    conn_params.port = 5782
    s = Subscriber(conn_params=conn_params,
                   topic=topic_name,
                   on_message=callback)
    s.run_forever()
```
