# Example of using TopicAggregator aggregation

This example shows how to use `TopicAggregator` class to aggregate data from several input topics to a single output topic.

```
     +-------------+       +-------------+       +-------------+
     |  Topic A    |------>| MQTT Broker |--->---|TopicAggregated|
     |  (Data A)   |       +-------------+       | (Combined)  |
     +-------------+       |             |       +-------------+
                             ^
                             |
     +-------------+       |             |
     |  Topic B    |------>|             |
     |  (Data B)   |       +-------------+
     +-------------+             |
                                 |
                                 |
                                 |
          +------------------------------------------+
          |  Topic Aggregator                      |
          |                                         |
          |  Input Topics:                          |
          |    - Topic A                           |
          |    - Topic B                           |
          |                                         |
          |  Processors:                           |
          |    - Processor A: Processes Data A     |
          |    - Processor B: Processes Data B     |
          |                                         |
          |  Aggregation Logic: Combines Processed Data |
          +------------------------------------------+

```


Furthermore, for each input topic data processors can be applied.

```
    processors = {
        "goaldsl.1.event": [
            lambda msg: {
                "position": {
                    "x": msg["x"], "y": msg["y"], "z": 0
                },
                "orientation": {
                    "x": 0, "y": 0, "z": msg["theta"]
                }
            }
        ]
    }
    topicmerge = TopicAggregator(conn_params, input_topics, output_topic,
                                 data_processors=processors)
```

**Important Note: This class does not apply any synchronization mechanism! Input topics are processed independently.**

An example of using the `TopicAggregator` class in the IoT domain, for sensor data aggregation from various data sources, is given below:

```
     +---------------------+       +-------------+       +---------------------+
     |  Sensor A (Temp)    |------>| MQTT Broker |--->---|Aggregated Sensor Data|
     |  (temp_raw)         |       +-------------+       | (temp_avg, humidity)|
     +---------------------+       |             |       +---------------------+
                                     ^
                                     |
     +---------------------+       |             |
     |  Sensor B (Humidity)|------>|             |
     |  (humidity_raw)     |       +-------------+
     +---------------------+             |
                                         |
                                         |
                                         |
          +-------------------------------------------------+
          |  Topic Aggregator                            |
          |                                                 |
          |  Input Topics:                                  |
          |    - sensor/temperature                        |
          |    - sensor/humidity                           |
          |                                                 |
          |  Processors:                                   |
          |    - Temperature Processor:                    |
          |        - Converts temp_raw to Celsius          |
          |        - Calculates average temperature over time |
          |    - Humidity Processor:                        |
          |        - Filters out invalid humidity readings   |
          |                                                 |
          |  Aggregation Logic: Combines processed temperature  |
          |  and humidity data into a single message.         |
          +-------------------------------------------------+

```
