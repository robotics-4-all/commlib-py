import functools
import logging
from typing import Any, Dict, List
from commlib.connection import BaseConnectionParameters
from commlib.node import Node

aggregation_logger = None


class TopicMessageProcessor:
    def __init__(self, broker_params: BaseConnectionParameters,
                 input_topic: List[str], output_topic: str,
                 data_processors: List[callable] = []):
        self.broker_params = broker_params
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.data_processors = data_processors  # List of functions to process incoming data

        self.node = Node(node_name="TopicMessageProcessor",
                         connection_params=self.broker_params,
                         debug=False, heartbeats=False)

    @classmethod
    def logger(cls) -> logging.Logger:
        global aggregation_logger
        if aggregation_logger is None:
            aggregation_logger = logging.getLogger(__name__)
        return aggregation_logger

    @property
    def log(self):
        return self.logger()

    def create_subscriptions(self):
        _clb = functools.partial(self.on_msg_internal, self.data_processors)
        self.node.create_psubscriber(topic=self.input_topic, on_message=_clb)

    def create_publisher(self):
        self.pub = self.node.create_mpublisher()

    def on_msg_internal(self, processors: Dict[str, callable],
                        payload: Dict[str, Any], topic: str):
        for proc in processors:
            try:
                payload = proc(payload)
                if not isinstance(payload, dict):
                    self.log.warning("Processor did not return a dict")
                    continue
                self.pub.publish(topic=self.output_topic, msg=payload)
                self.log.info(f"Processed message: {payload}")
            except Exception as e:
                self.log.error(f"Error processing message: {e}")
                continue

    def start(self):
        self.create_publisher()
        self.create_subscriptions()
        self.node.run_forever()


class TopicAggregator:
    def __init__(self, broker_params: BaseConnectionParameters,
                 input_topics: List[str], output_topic: str,
                 data_processors: Dict[str, callable] = {}):
        self.broker_params = broker_params
        self.input_topics = input_topics
        self.output_topic = output_topic
        self.data_processors = data_processors  # List of functions to process incoming data

        self.node = Node(node_name="TopicAggregator",
                         connection_params=self.broker_params,
                         debug=False, heartbeats=False)

    @classmethod
    def logger(cls) -> logging.Logger:
        global aggregation_logger
        if aggregation_logger is None:
            aggregation_logger = logging.getLogger(__name__)
        return aggregation_logger

    @property
    def log(self):
        return self.logger()

    def create_subscriptions(self):
        for topic in self.input_topics:
            if topic in self.data_processors:
                _procs = self.data_processors[topic]
                _clb = functools.partial(self.on_msg_internal, processors=_procs)
            else:
                _clb = self.on_msg_internal
            self.node.create_psubscriber(topic=topic, on_message=_clb)

    def create_publisher(self):
        self.pub = self.node.create_mpublisher()

    def on_msg_internal(self,
                        payload: Dict[str, Any],
                        topic: str,
                        processors: Dict[str, callable] = {}
                        ):
        for proc in processors:
            try:
                payload = proc(payload)
                if not isinstance(payload, dict):
                    self.log.warning("Processor did not return a dict")
                    continue
                self.pub.publish(topic=self.output_topic, msg=payload)
            except Exception as e:
                self.log.error(f"Error processing message: {e}")
                continue

    def start(self):
        self.create_publisher()
        self.create_subscriptions()
        self.node.run_forever()
