from typing import Any


"""
{
    URI: 'example.org/user',
    VERB: 'GET',
    PARAMS: {
        QUERY: [{name: '', val: ''}].
        PATH: [{name: '', val: ''}],
        BODY: [{name: '', val: ''}]
    }
}

"""


class RESTProxy:
    def __init__(self, broker_uri: str,
                 broker_params: Any):

