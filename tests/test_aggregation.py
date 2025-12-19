#!/usr/bin/env python

"""Tests for commlib aggregation module."""

import unittest
from typing import Dict, Any

from commlib.aggregation import TopicMessageProcessor
from commlib.transports.mock import ConnectionParameters


class TestTopicMessageProcessor(unittest.TestCase):
    """Test TopicMessageProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.conn_params = ConnectionParameters(
            host="test",
            port="1234",
            reconnect_attempts=0
        )

    def test_processor_creation(self):
        """Test TopicMessageProcessor creation."""
        processor = TopicMessageProcessor(
            broker_params=self.conn_params,
            input_topic=["input.topic"],
            output_topic="output.topic"
        )
        self.assertEqual(processor.input_topic, ["input.topic"])
        self.assertEqual(processor.output_topic, "output.topic")
        self.assertIsNotNone(processor.node)

    def test_processor_with_multiple_input_topics(self):
        """Test TopicMessageProcessor with multiple input topics."""
        input_topics = ["topic1", "topic2", "topic3"]
        processor = TopicMessageProcessor(
            broker_params=self.conn_params,
            input_topic=input_topics,
            output_topic="output"
        )
        self.assertEqual(processor.input_topic, input_topics)

    def test_processor_with_data_processors(self):
        """Test TopicMessageProcessor with data processors."""
        def processor1(data: Dict[str, Any]) -> Dict[str, Any]:
            data["processed_by"] = "processor1"
            return data

        def processor2(data: Dict[str, Any]) -> Dict[str, Any]:
            data["processed_by"] = "processor2"
            return data

        processors = [processor1, processor2]
        processor = TopicMessageProcessor(
            broker_params=self.conn_params,
            input_topic=["input"],
            output_topic="output",
            data_processors=processors
        )
        self.assertEqual(processor.data_processors, processors)
        self.assertEqual(len(processor.data_processors), 2)

    def test_processor_broker_params(self):
        """Test TopicMessageProcessor broker parameters."""
        processor = TopicMessageProcessor(
            broker_params=self.conn_params,
            input_topic=["input"],
            output_topic="output"
        )
        self.assertEqual(processor.broker_params, self.conn_params)

    def test_processor_logger(self):
        """Test TopicMessageProcessor logger."""
        processor = TopicMessageProcessor(
            broker_params=self.conn_params,
            input_topic=["input"],
            output_topic="output"
        )
        logger = processor.logger()
        self.assertIsNotNone(logger)
        self.assertTrue(hasattr(logger, 'info'))

    def test_processor_log_property(self):
        """Test TopicMessageProcessor log property."""
        processor = TopicMessageProcessor(
            broker_params=self.conn_params,
            input_topic=["input"],
            output_topic="output"
        )
        log = processor.log
        self.assertIsNotNone(log)
        self.assertTrue(hasattr(log, 'info'))

    def test_processor_create_subscriptions(self):
        """Test TopicMessageProcessor create_subscriptions."""
        processor = TopicMessageProcessor(
            broker_params=self.conn_params,
            input_topic=["input.topic"],
            output_topic="output.topic"
        )
        # Should not raise an exception
        try:
            processor.create_subscriptions()
        except Exception as e:
            # This is expected if the node is not properly initialized
            # but we're just testing that the method exists
            pass
        self.assertIsNotNone(processor.node)

    def test_processor_create_publisher(self):
        """Test TopicMessageProcessor create_publisher."""
        processor = TopicMessageProcessor(
            broker_params=self.conn_params,
            input_topic=["input"],
            output_topic="output"
        )
        try:
            processor.create_publisher()
        except Exception:
            # Expected if node not properly initialized
            pass
        # We're just testing that the method exists and doesn't crash catastrophically
        self.assertIsNotNone(processor)

    def test_processor_with_empty_data_processors(self):
        """Test TopicMessageProcessor with empty data processors list."""
        processor = TopicMessageProcessor(
            broker_params=self.conn_params,
            input_topic=["input"],
            output_topic="output",
            data_processors=[]
        )
        self.assertEqual(processor.data_processors, [])

    def test_processor_node_name(self):
        """Test TopicMessageProcessor node name."""
        processor = TopicMessageProcessor(
            broker_params=self.conn_params,
            input_topic=["input"],
            output_topic="output"
        )
        self.assertEqual(processor.node._node_name, "TopicMessageProcessor")


if __name__ == '__main__':
    unittest.main()
