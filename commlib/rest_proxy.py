import time
import json

import requests

from typing import Dict, List, Any, Optional, Union

from commlib.endpoints import TransportType, EndpointType, endpoint_factory
from commlib.msg import PubSubMessage, RPCMessage


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
        base_url: str
        path: str = '/'
        verb: str = 'GET'
        query_params: Dict = {}
        path_params: Dict = {}
        body_params: Dict = {}
        headers: Dict = {}

    class Response(RPCMessage.Response):
        data: Union[str, Dict, int]
        headers: Dict[str, Any]
        status_code: int = 200


class RESTProxy:
    """RESTProxy.

    REST Proxy implementation class. Call REST Web services via commlib
    supported protocols (AMQP, MQTT, REDIS).
    """

    def __init__(self, broker_uri: str,
                 broker_type: TransportType,
                 broker_params: Any,
                 debug: bool = False):
        """__init__.

        Args:
            broker_uri (str): broker_uri
            broker_type (TransportType): broker_type
            broker_params (Any): broker_params
            debug (bool): debug
        """
        self._debug = debug
        svc = endpoint_factory(EndpointType.RPCService,
                               broker_type)(rpc_name=broker_uri,
                                            msg_type=RESTProxyMessage,
                                            conn_params=broker_params,
                                            on_request=self._on_request,
                                            debug=self._debug)
        self._svc = svc

    def _on_request(self, msg: RESTProxyMessage.Request):
        """_on_request.

        Args:
            msg (RESTProxyMessage): Request message
        """
        url = f'{msg.base_url}{msg.path}'
        # -------- > Perform HTTP Request from input message
        if msg.verb == 'GET':
            resp = requests.get(url, params=msg.query_params,
                                headers=msg.headers)
        elif msg.verb == 'PUT':
            resp = requests.put(url, params=msg.query_params,
                                data=msg.body_params, headers=msg.headers)
        elif msg.verb == 'POST':
            resp = requests.post(url, params=msg.query_params,
                                 data=msg.body_params, headers=msg.headers)
        else:
            raise ValueError(f'HTTP Verb [{msg.verb}] is not valid!')
        # <---------------------------------------------------
        headers = dict(**resp.headers)
        data = resp.text
        if headers.get('Content-Type') == 'application/json':
            data = json.loads(data)
        return RESTProxyMessage.Response(data=data, headers=headers,
                                         status_code=resp.status_code)

    def run(self):
        """run.
        """
        self._svc.run()

    def run_forever(self):
        """run_forever.
        """
        self._svc.run()
        while True:
            time.sleep(0.001)
