import time
import json
import http.client

from typing import Dict, List, Any, Optional

from commlib.endpoints import TransportType, EndpointType, endpoint_factory
from commlib.msg import DataClass, DataField, Object, PubSubMessage, RPCMessage


"""
{
    HOST: 'example.org/user',
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
    @DataClass
    class Request(RPCMessage.Request):
        host: str
        port: int = 80
        path: str = '/'
        verb: str = 'GET'
        query_params: Dict = DataField(default_factory=dict)
        path_params: Dict = DataField(default_factory=dict)
        body_params: Dict = DataField(default_factory=dict)
        headers: Dict = DataField(default_factory=dict)

    @DataClass
    class Response(RPCMessage.Response):
        data: Dict = DataField(default_factory=dict)


class RESTProxy:
    def __init__(self, broker_uri: str,
                 broker_type: TransportType,
                 broker_params: Any,
                 debug: bool = False):
        self._debug = debug
        svc = endpoint_factory(EndpointType.RPCService,
                               broker_type)(rpc_name=broker_uri,
                                            msg_type=RESTProxyMessage,
                                            conn_params=broker_params,
                                            on_request=self._on_request,
                                            debug=self._debug)
        self._svc = svc

    def _on_request(self, msg):
        print(msg)
        conn = http.client.HTTPConnection(msg.host, msg.port)
        conn.request(msg.verb, msg.path)
        resp = conn.getresponse()
        resp_body = resp.read().decode('utf8')
        try:
            resp_body = json.loads(resp_body)
        except:
            pass
        return RESTProxyMessage.Response(data=resp_body)

    def run(self):
        self._svc.run()

    def run_forever(self):
        self._svc.run()
        while True:
            time.sleep(0.001)
