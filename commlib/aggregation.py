import functools
from typing import Any, Dict, List
from commlib.connection import BaseConnectionParameters
from commlib.node import Node



class TopicMerge:
    def __init__(self, broker_params: BaseConnectionParameters,
                 input_topics: List[str], output_topic: str,
                 data_processors: Dict[str, callable] = {}):
        self.broker_params = broker_params
        self.input_topics = input_topics
        self.output_topic = output_topic
        self.data_processors = data_processors  # List of functions to process incoming data

        self.node = Node(node_name="TopicMerge",
                         connection_params=self.broker_params,
                         debug=False, heartbeats=False)

    def create_subscriptions(self):
        for topic in self.input_topics:
            if topic in self.data_processors:
                _procs = self.data_processors[topic]
            _clb = functools.partial(self.on_msg_internal, _procs)
            self.node.create_psubscriber(topic=topic, on_message=_clb)

    def create_publisher(self):
        self.pub = self.node.create_mpublisher()

    def on_msg_internal(self, processors: Dict[str, callable],
                        payload: Dict[str, Any], topic: str):
        print(f"TO KAKO TO POSE: {payload}")
        for proc in processors:
            print(f"TO KALO TO POSE: {proc(payload)}")
        self.pub.publish(topic=self.output_topic, msg=payload)

    def start(self):
        self.create_publisher()
        self.create_subscriptions()
        self.node.run_forever()
