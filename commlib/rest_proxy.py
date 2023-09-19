import json
import time
from typing import Any, Dict, List, Optional, Union

import requests

from commlib.endpoints import EndpointType, TransportType, endpoint_factory
from commlib.msg import PubSubMessage, RPCMessage
from commlib import Node


"""
{
    BASE_URL: 'https://example.org:9080',
    VERB: 'GET',
    PARAMS: {
        QUERY: [{name: '', val: ''}].
        PATH: [{name: '', val: ''}],
        BODY: [{name: '', val: ''}]
    }
    HEADERS: {}
}

"""


class RESTProxyMessage(RPCMessage):
    class Request(RPCMessage.Request):
        host: Optional[str] = 'localhost'
        port: Optional[int] = 8080
        ssl: Optional[bool] = False
        base_url: str = ''
        path: str = "/"
        verb: str = "GET"
        query_params: Dict = {}
        path_params: Dict = {}
        body_params: Dict = {}
        headers: Dict = {}

    class Response(RPCMessage.Response):
        data: Union[str, Dict, int]
        headers: Dict[str, Any]
        status_code: int = 200


class RestProxyServer:
    def __init__(self, service_map):
        self._service_map = service_map


class RESTProxy(Node):
    """RESTProxy.

    REST Proxy implementation class. Call REST Web services via commlib
    supported protocols (AMQP, MQTT, REDIS).
    """

    def __init__(
        self,
        broker_uri: str,
        broker_params: Any,
        debug: bool = False,
        *args, **kwargs
    ):
        """__init__.

        Args:
            broker_uri (str): broker_uri
            broker_type (TransportType): broker_type
            broker_params (Any): broker_params
            debug (bool): debug
        """
        self._debug = debug

        super().__init__(node_name='util.rest_proxy',
                         connection_params=broker_params,
                         *args, **kwargs)
        self._broker_uri = broker_uri
        self._svc = self.create_rpc(
            rpc_name=broker_uri,
            msg_type=RESTProxyMessage,
            on_request = self._on_request
        )
        self.logger().info(f'Initiated REST Proxy @ {broker_uri}')

    def _on_request(self, msg: RESTProxyMessage.Request):
        schema = 'https' if msg.ssl else 'http'
        port = msg.port
        if port is None:
            port = 443 if msg.ssl else 80
        url = f"{schema}://{msg.host}:{port}{msg.base_url}{msg.path}"
        self.logger().info(f'Request for: {url}')
        # -------- > Perform HTTP Request from input message
        if msg.verb == "GET":
            resp = requests.get(url, params=msg.query_params, headers=msg.headers)
        elif msg.verb == "PUT":
            resp = requests.put(
                url, params=msg.query_params, data=msg.body_params, headers=msg.headers
            )
        elif msg.verb == "POST":
            resp = requests.post(
                url, params=msg.query_params, data=msg.body_params, headers=msg.headers
            )
        else:
            raise ValueError(f"HTTP Verb [{msg.verb}] is not valid!")
        # <---------------------------------------------------
        headers = dict(**resp.headers)
        data = resp.text
        if headers.get("Content-Type") == "application/json":
            data = json.loads(data)
        return RESTProxyMessage.Response(
            data=data, headers=headers, status_code=resp.status_code
        )

    def run(self):
        """run."""
        self._svc.run()

    def run_forever(self):
        """run_forever."""
        self._svc.run()
        while True:
            time.sleep(0.01)
