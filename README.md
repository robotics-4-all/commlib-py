<div id="top">

<!-- HEADER STYLE: CLASSIC -->
<div align="center">

![image](https://github.com/robotics-4-all/commlib-py/assets/4770702/0dc3db01-eb5e-40a2-9d3a-07d25613fc86)


[![PyPI version](https://badge.fury.io/py/commlib-py.svg)](https://badge.fury.io/py/commlib-py) [![Downloads](https://static.pepy.tech/badge/commlib-py)](https://pepy.tech/project/commlib-py) [![Downloads](https://static.pepy.tech/badge/commlib-py/month)](https://pepy.tech/project/commlib-py) [![Downloads](https://static.pepy.tech/badge/commlib-py/week)](https://pepy.tech/project/commlib-py)

<em></em>

<!-- BADGES -->
<!-- local repository, no metadata badges. -->

<em>Built with the tools and technologies:</em>

<img src="https://img.shields.io/badge/Redis-FF4438.svg?style=default&logo=Redis&logoColor=white" alt="Redis">
<img src="https://img.shields.io/badge/MQTT-606?logo=mqtt&logoColor=fff&style=plastic" alt="MQTT">
<img src="https://img.shields.io/badge/RabbitMQ-F60?logo=rabbitmq&logoColor=fff&style=plastic" alt="RabbitMQ">
<img src="https://img.shields.io/badge/Apache%20Kafka-231F20?logo=apachekafka&logoColor=fff&style=plastic" alt="Kafka">
<br>
<img src="https://img.shields.io/badge/Anaconda-44A833.svg?style=default&logo=Anaconda&logoColor=white" alt="Anaconda">
<img src="https://img.shields.io/badge/Pytest-0A9EDC.svg?style=default&logo=Pytest&logoColor=white" alt="Pytest">
<img src="https://img.shields.io/badge/Docker-2496ED.svg?style=default&logo=Docker&logoColor=white" alt="Docker">
<img src="https://img.shields.io/badge/Python-3776AB.svg?style=default&logo=Python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/Pydantic-E92063.svg?style=default&logo=Pydantic&logoColor=white" alt="Pydantic">

</div>
<br>

---

## 📜 Table of Contents

- [📜 Table of Contents](#-table-of-contents)
- [📖 Overview](#-overview)
- [👾 Features](#-features)
- [📜 Project Index](#-project-index)
- [🚀 Getting Started](#-getting-started)
	- [🔖 Prerequisites](#-prerequisites)
	- [🛠️ Installation](#️-installation)
		- [PyPi Releases](#pypi-releases)
		- [From Source](#from-source)
		- [JSON Serialization](#json-serialization)
	- [📺 Concepts](#-concepts)
		- [Node](#node)
		- [Req/Resp - RPCs](#reqresp---rpcs)
			- [Server Side Example](#server-side-example)
			- [Client Side Example](#client-side-example)
		- [Pub/Sub](#pubsub)
			- [Write a Simple Publisher](#write-a-simple-publisher)
			- [Write a Simple Subscriber](#write-a-simple-subscriber)
		- [Wildcard Subscriptions](#wildcard-subscriptions)
		- [Preemptive Services with Feedback (Actions)](#preemptive-services-with-feedback-actions)
			- [Write an Action Service](#write-an-action-service)
			- [Write an Action Client](#write-an-action-client)
- [📺 Advanced](#-advanced)
	- [Endpoints (Low-level API)](#endpoints-low-level-api)
	- [B2B bridges](#b2b-bridges)
	- [TCP Bridge](#tcp-bridge)
- [REST Proxy](#rest-proxy)
- [🧪 Testing](#-testing)
- [🎞️ Roadmap](#️-roadmap)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)
- [🎩 Acknowledgments](#-acknowledgments)

---

## 📖 Overview

Commlib is a **Domain-specific Language** for communication and messaging in **Cyber-Physical Systems**. Can be used for rapid development of the communication layer on-device, at the Edge and on the Cloud, or using a mixed multi-level multi-broker schema.

The goal of this project is to implement a simple Protocol-agnostic API (AMQP, Kafka, Redis, MQTT, etc) for common communication patterns in the context of Cyber-Physical Systems, using message broker technologies. Such patterns include PubSub, RPC and Preemptive Services (aka Actions), among others.


<div align="center">
<img src="https://github.com/robotics-4-all/commlib-py/assets/4770702/ab009804-75aa-4272-a471-b3f966e4011c">
</div>

---


## 👾 Features

|      | Feature         | Summary       |
| :--- | :---:           | :---          |
| ⚙️  | **Protocol-Agnostic**  | <ul><li>Protocol/Transport-level abstraction</li><li>Currently supports Redis, AMQP, MQTT and Kafka</li></ul> |
| 📄 | **Documentation** | <ul><li>Rich documentation in various formats (YAML, TOML, Markdown)</li><li>Includes detailed installation commands for different package managers</li><li>Utilizes MkDocs for generating documentation</li></ul> |
| 🧩 | **Modularity**    | <ul><li>Well-structured codebase with clear separation of concerns</li><li>Encourages code reusability and maintainability</li><li>Utilizes dependency management with Poetry</li></ul> |
| ⚡️  | **Performance**   | <ul><li>Optimized code for efficiency</li><li>Scalable architecture for handling high loads</li></ul> |
| 📦 | **Dependencies**  | <ul><li>Manages dependencies with Poetry and dependency lock files</li><li>Includes a variety of libraries for different functionalities</li><li>Dependency management with conda for environment setup</li><li>Dynamic imports of underlying transport libraries</li></ul> |

---

<!-- ## 📚 Project Structure

```sh
└── commlib-py/
    ├── brokers
    │   ├── amqp
    │   ├── dragonfly
    │   ├── kafka
    │   ├── mqtt
    │   └── redis
    ├── commlib
    │   ├── __init__.py
    │   ├── action.py
    │   ├── aggregation.py
    │   ├── async_utils.py
    │   ├── bridges.py
    │   ├── compression.py
    │   ├── connection.py
    │   ├── endpoints.py
    │   ├── exceptions.py
    │   ├── msg.py
    │   ├── node.py
    │   ├── pubsub.py
    │   ├── rpc.py
    │   ├── serializer.py
    │   ├── tcp_proxy.py
    │   ├── timer.py
    │   ├── transports
    │   └── utils.py
    ├── examples
    │   ├── bridges
    │   ├── endpoint_factory
    │   ├── minimize_conns
    │   ├── multitopic_publisher
    │   ├── node
    │   ├── node_decorators
    │   ├── node_inherit
    │   ├── perf_test
    │   ├── ptopic_bridge
    │   ├── rpc_server
    │   ├── simple_action
    │   ├── simple_pubsub
    │   ├── simple_rpc
    │   ├── test_rpc_deletion
    │   └── topic_aggregator
    ├── requirements.txt
    ├── set_version.sh
    ├── setup.cfg
    ├── setup.py
    ├── tests
    │   ├── __init__.py
    │   ├── mqtt
    │   ├── redis
    │   ├── test_msgs.py
    │   ├── test_node.py
    │   ├── test_pubsub.py
    │   ├── test_rpc.py
    │   └── test_timer.py
    └── tox.ini
``` -->

## 📜 Project Index

<details open>
	<!-- brokers Submodule -->
		<summary><b>brokers</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ brokers</b></code>
			<!-- redis Submodule -->
			<details>
				<summary><b>redis</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ brokers.redis</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/brokers/redis/redis.conf'>redis.conf</a></b></td>
							<td style='padding: 8px;'>- The <code>redis.conf</code> file in the <code>brokers/redis</code> directory configures the Redis server instance used within the larger application<br>- It dictates settings such as memory allocation and potentially includes other configuration files for customized server behavior<br>- Essentially, this file is crucial for setting up and controlling the Redis message broker within the overall system architecture.</td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/brokers/redis/launch_redis_docker.sh'>launch_redis_docker.sh</a></b></td>
							<td style='padding: 8px;'>- The script launches a Redis instance within a Docker container<br>- It utilizes a provided configuration file (<code>redis.conf</code>) and maps port 6379 for external access<br>- This facilitates the use of Redis as a message broker within the larger application architecture, enabling efficient data exchange between application components<br>- The containers ephemeral nature ensures clean resource management.</td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- mqtt Submodule -->
			<details>
				<summary><b>mqtt</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ brokers.mqtt</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/brokers/mqtt/launch_emqx_docker.sh'>launch_emqx_docker.sh</a></b></td>
							<td style='padding: 8px;'>- The script launches an EMQX MQTT broker instance within a Docker container<br>- It exposes several ports for various MQTT protocols, including the management UI, enabling communication and administration<br>- This facilitates message queuing and data exchange within the broader application architecture<br>- The script simplifies deployment and management of the broker.</td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- kafka Submodule -->
			<details>
				<summary><b>kafka</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ brokers.kafka</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/brokers/kafka/start.sh'>start.sh</a></b></td>
							<td style='padding: 8px;'>- The <code>start.sh</code> script initiates the Kafka broker within the projects dockerized environment<br>- It leverages docker-compose to manage the lifecycle of the Kafka containers, ensuring a clean startup by first stopping any existing instances and then starting them, removing any orphaned containers<br>- This script is crucial for deploying and managing the Kafka message broker infrastructure.</td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/brokers/kafka/docker-compose.yml'>docker-compose.yml</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/brokers/kafka/docker-compose-2.yml'>docker-compose-2.yml</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- dragonfly Submodule -->
			<details>
				<summary><b>dragonfly</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ brokers.dragonfly</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/brokers/dragonfly/start.sh'>start.sh</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/brokers/dragonfly/docker-compose.yml'>docker-compose.yml</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- amqp Submodule -->
			<details>
				<summary><b>amqp</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ brokers.amqp</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/brokers/amqp/launch_rabbitmq_docker.sh'>launch_rabbitmq_docker.sh</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/brokers/amqp/docker-compose.yml'>docker-compose.yml</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
		</blockquote>
	</details>
	<details>
	<!-- examples Submodule -->
		<summary><b>examples</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ examples</b></code>
			<!-- topic_aggregator Submodule -->
			<details>
				<summary><b>topic_aggregator</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.topic_aggregator</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/topic_aggregator/topic_merge.py'>topic_merge.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/topic_aggregator/producers.py'>producers.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- test_rpc_deletion Submodule -->
			<details>
				<summary><b>test_rpc_deletion</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.test_rpc_deletion</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/test_rpc_deletion/test.py'>test.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- minimize_conns Submodule -->
			<details>
				<summary><b>minimize_conns</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.minimize_conns</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/minimize_conns/wsubscriber.py'>wsubscriber.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/minimize_conns/wpublisher.py'>wpublisher.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- simple_rpc Submodule -->
			<details>
				<summary><b>simple_rpc</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.simple_rpc</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/simple_rpc/simple_rpc_service.py'>simple_rpc_service.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/simple_rpc/simple_rpc_client.py'>simple_rpc_client.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- simple_pubsub Submodule -->
			<details>
				<summary><b>simple_pubsub</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.simple_pubsub</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/simple_pubsub/subscriber.py'>subscriber.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/simple_pubsub/publisher.py'>publisher.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- simple_action Submodule -->
			<details>
				<summary><b>simple_action</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.simple_action</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/simple_action/action_service.py'>action_service.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/simple_action/action_client.py'>action_client.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- rpc_server Submodule -->
			<details>
				<summary><b>rpc_server</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.rpc_server</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/rpc_server/rpc_server.py'>rpc_server.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/rpc_server/client.py'>client.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- ptopic_bridge Submodule -->
			<details>
				<summary><b>ptopic_bridge</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.ptopic_bridge</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/ptopic_bridge/redis_pub.py'>redis_pub.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/ptopic_bridge/mqtt_sub.py'>mqtt_sub.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/ptopic_bridge/bridge.py'>bridge.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- perf_test Submodule -->
			<details>
				<summary><b>perf_test</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.perf_test</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/perf_test/perf_test.py'>perf_test.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- node_inherit Submodule -->
			<details>
				<summary><b>node_inherit</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.node_inherit</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/node_inherit/node_inherit_example.py'>node_inherit_example.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- node_decorators Submodule -->
			<details>
				<summary><b>node_decorators</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.node_decorators</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/node_decorators/decor_node.py'>decor_node.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/node_decorators/client.py'>client.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- node Submodule -->
			<details>
				<summary><b>node</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.node</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/node/node_with_features.py'>node_with_features.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- multitopic_publisher Submodule -->
			<details>
				<summary><b>multitopic_publisher</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.multitopic_publisher</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/multitopic_publisher/psubscriber.py'>psubscriber.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/multitopic_publisher/mpublisher.py'>mpublisher.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- endpoint_factory Submodule -->
			<details>
				<summary><b>endpoint_factory</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.endpoint_factory</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/endpoint_factory/example.py'>example.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
			<!-- bridges Submodule -->
			<details>
				<summary><b>bridges</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ examples.bridges</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/bridges/typed_bridge_example.py'>typed_bridge_example.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/examples/bridges/bridge_example.py'>bridge_example.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
		</blockquote>
	</details>
	<!-- commlib Submodule -->
	<details>
		<summary><b>commlib</b></summary>
		<blockquote>
			<div class='directory-path' style='padding: 8px 0; color: #666;'>
				<code><b>⦿ commlib</b></code>
			<table style='width: 100%; border-collapse: collapse;'>
			<thead>
				<tr style='background-color: #f8f9fa;'>
					<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
					<th style='text-align: left; padding: 8px;'>Summary</th>
				</tr>
			</thead>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/utils.py'>utils.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/timer.py'>timer.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/tcp_proxy.py'>tcp_proxy.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/serializer.py'>serializer.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/rpc.py'>rpc.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/pubsub.py'>pubsub.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/node.py'>node.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/msg.py'>msg.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/exceptions.py'>exceptions.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/endpoints.py'>endpoints.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/connection.py'>connection.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/bridges.py'>bridges.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/async_utils.py'>async_utils.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/aggregation.py'>aggregation.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/action.py'>action.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/compression.py'>compression.py</a></b></td>
					<td style='padding: 8px;'>TODO</code></td>
				</tr>
			</table>
			<!-- transports Submodule -->
			<details>
				<summary><b>transports</b></summary>
				<blockquote>
					<div class='directory-path' style='padding: 8px 0; color: #666;'>
						<code><b>⦿ commlib.transports</b></code>
					<table style='width: 100%; border-collapse: collapse;'>
					<thead>
						<tr style='background-color: #f8f9fa;'>
							<th style='width: 30%; text-align: left; padding: 8px;'>File Name</th>
							<th style='text-align: left; padding: 8px;'>Summary</th>
						</tr>
					</thead>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/transports/redis.py'>redis.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/transports/mqtt.py'>mqtt.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/transports/mock.py'>mock.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/transports/kafka.py'>kafka.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/transports/base_transport.py'>base_transport.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
						<tr style='border-bottom: 1px solid #eee;'>
							<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/transports/amqp.py'>amqp.py</a></b></td>
							<td style='padding: 8px;'>TODO</code></td>
						</tr>
					</table>
				</blockquote>
			</details>
		</blockquote>
	</details>
</details>

---

## 🚀 Getting Started

### 🔖 Prerequisites

This project requires the following dependencies:

- **Programming Language:** Python
- **Packages:** Pydantic2, orjson|ujson (Optional for fast json serialization), paho-mqtt (Optional for MQTT support), redis-py (Optional for Redis Support), pika (Optional for AMQP support)
- **Package Manager:** Pip, Poetry, Conda, Tox

### 🛠️ Installation

Build commlib-py from the source and install dependencies:

#### PyPi Releases

1. **Using pip**

```sh
❯ pip install commlib-py
```

Or select version explicitly

```sh
❯ pip install commlib-py==0.11.5
```

1. **Using pipx**

```sh
❯ pipx install commlib-py
```

#### From Source

1. **Clone the repository:**

    ```sh
    ❯ git clone git@github.com:robotics-4-all/commlib-py.git
    ```

2. **Navigate to the project directory:**

    ```sh
    ❯ cd commlib-py
    ```

3. **Install the dependencies:**


<!-- SHIELDS BADGE CURRENTLY DISABLED -->
	<!-- [![pip][pip-shield]][pip-link] -->
	<!-- REFERENCE LINKS -->
	<!-- [pip-shield]: https://img.shields.io/badge/Pip-3776AB.svg?style={badge_style}&logo=pypi&logoColor=white -->
	<!-- [pip-link]: https://pypi.org/project/pip/ -->

	**Using [pip](https://pypi.org/project/pip/):**

	```sh
	❯ pip install .
	```
<!-- SHIELDS BADGE CURRENTLY DISABLED -->
	<!-- [![poetry][poetry-shield]][poetry-link] -->
	<!-- REFERENCE LINKS -->
	<!-- [poetry-shield]: https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json -->
	<!-- [poetry-link]: https://python-poetry.org/ -->

	**Using [poetry](https://python-poetry.org/):**

	```sh
	❯ poetry install
	```
<!-- SHIELDS BADGE CURRENTLY DISABLED -->
	<!-- [![conda][conda-shield]][conda-link] -->
	<!-- REFERENCE LINKS -->
	<!-- [conda-shield]: https://img.shields.io/badge/conda-342B029.svg?style={badge_style}&logo=anaconda&logoColor=white -->
	<!-- [conda-link]: https://docs.conda.io/ -->

	**Using [conda](https://docs.conda.io/):**

	```sh
	❯ conda env create -f environment.yml
	```
<!-- SHIELDS BADGE CURRENTLY DISABLED -->
	<!-- [![tox][tox-shield]][tox-link] -->
	<!-- REFERENCE LINKS -->
	<!-- [tox-shield]: None -->
	<!-- [tox-link]: None -->


#### JSON Serialization

It is recommended to use a fast json library, such as [orjson](https://github.com/ijl/orjson) or [ujson](https://github.com/ultrajson/ultrajson).

The framework will load and use the most performance optimal library based on installations, using the below priority:
- [ujson](https://github.com/ultrajson/ultrajson)
- [orjson](https://github.com/ijl/orjson)
- json

### 📺 Concepts

#### Node

A **Node** is a software component that follows the **Component-Port-Connector** model. It has input and output ports for communicating with the world. Each port defines an endpoint and can be of the following types.
<div align="center">

<table>
	<thead>
		<tr>
			<th><b>Port Type</b></th>
			<th><b>Description</b></th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td rowspan="4"><b>Input Port</b></td>
			<td><b>Subscriber</b>: Listens for messages on a specific topic.</td>
		</tr>
		<tr>
			<td><b>RPC Service</b>: Provides a Remote Procedure Call (RPC) service for handling requests.</td>
		</tr>
		<tr>
			<td><b>Action Service</b>: Executes long-running tasks and provides feedback during execution.</td>
		</tr>
		<tr>
			<td><b>RPC Server</b>: Handles RPC requests and sends responses.</td>
		</tr>
		<tr>
			<td rowspan="3"><b>Output Port</b></td>
			<td><b>Publisher</b>: Sends messages to a specific topic.</td>
		</tr>
		<tr>
			<td><b>RPC Client</b>: Sends RPC requests and waits for responses.</td>
		</tr>
		<tr>
			<td><b>Action Client</b>: Initiates actions and receives feedback during execution.</td>
		</tr>
		<tr>
			<td rowspan="3"><b>InOut Port</b></td>
			<td><b>RPCBridge</b>: Bridges RPC communication between two brokers. Directional.</td>
		</tr>
		<tr>
			<td><b>TopicBridge</b>: Bridges PubSub communication between two brokers. Directional.</td>
		</tr>
		<tr>
			<td><b>PTopicBridge</b>: Bridges PubSub communication between two brokers based on a topic pattern. Directional.</td>
		</tr>
	</tbody>
</table>

</div>


Furthermore, it implements several features:
- Publish Heartbeat messages in the background for as long as the node is active
- Provide control interfaces, to `start` and `stop` the execution of the Node
- Provides methods to create endpoints and bind to Node ports.

```python
from commlib.node import Node, TransportType
from commlib.msg import RPCMessage
## Import the Redis transports
## Imports are lazy handled internally
from commlib.transports.redis import ConnectionParameters

class AddTwoIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0

def add_two_int_handler(msg):
    print(f'On-Request: {msg}')
    resp = AddTwoIntMessage.Response(c = msg.a + msg.b)
    return resp

if __name__ == '__main__':
	conn_params = ConnectionParameters()
	node = Node(
		node_name='add_two_ints_node',
		connection_params=conn_params,
		heartbeats=True,
		heartbeat_uri='nodes.add_two_ints.heartbeat',
		heartbeat_interval=10,
		ctrl_services=True,
		debug=False
	)
	rpc = node.create_rpc(
		msg_type=AddTwoIntMessage,
		rpc_name='add_two_ints_node.add_two_ints',
		on_request=add_two_int_handler
	)
	node.run_forever(sleep_rate=1)
```

**A Node always binds to a specific broker** via where it provides input and output ports to the functionality. Of course, **several Nodes can be created and executed in a single-process application**.

Below is the list of currently supported interface/endpoint types and protocol transports.

| Interface Type          | Description                                      | Required Parameters                                                                 | Supported transports       |
|-------------------------|--------------------------------------------------|-------------------------------------------------------------------------------------|---------------------------|
| **RPCClient**          | Sends RPC requests and waits for responses.      | `rpc_name`, `connection_params`                                         | MQTT, Redis, AMQP, Kafka  |
| **RPCServer**          | Handles RPC requests and sends responses.        | `rpc_name`, `on_request`, `connection_params`                           | MQTT, Redis, AMQP, Kafka  |
| **Publisher**          | Sends messages to a specific topic.              | `topic`, `connection_params`                                           | MQTT, Redis, AMQP, Kafka  |
| **Subscriber**         | Listens for messages on a specific topic.        | `topic`, `on_message`, `connection_params`                              | MQTT, Redis, AMQP, Kafka  |
| **MPublisher**         | Publishes messages to multiple topics.           | `connection_params`                                                                 | MQTT, Redis, AMQP, Kafka  |
| **WPublisher**         | A wrapped publisher with additional features.    | `topic`, `connection_params`                                           | MQTT, Redis  |
| **PSubscriber**        | Subscribes to topics using patterns.             | `topic_pattern`, `on_message`, `connection_params`                                  | MQTT, Redis, AMQP, Kafka  |
| **WSubscriber**        | A wrapped subscriber with additional features.   | `topic`, `on_message`, `connection_params`                              | MQTT, Redis  |
| **ActionService**      | Provides preemptive services with feedback.      | `msg_type`, `action_name`, `on_goal`, `connection_params`                           | MQTT, Redis, AMQP  |
| **ActionClient**       | Sends goals to an action service and receives feedback. | `msg_type`, `action_name`, `on_feedback`, `on_result`, `connection_params`          | MQTT, Redis, AMQP  |

**Node class:**

```py
class Node:

    def __init__(self,
                 node_name: Optional[str] = "",
                 connection_params: Optional[Any] = None,
                 debug: Optional[bool] = False,
                 heartbeats: Optional[bool] = True,
                 heartbeat_interval: Optional[float] = 10.0,
                 heartbeat_uri: Optional[str] = None,
                 compression: CompressionType = CompressionType.NO_COMPRESSION,
                 ctrl_services: Optional[bool] = False,
                 workers_rpc: Optional[int] = 4):
```

Node methods to create and run Endpoints::

```py
Node:
   create_action(self, *args, **kwargs)
   create_action_client(self, *args, **kwargs)
   create_event_emitter(self, *args, **kwargs)
   create_heartbeat_thread(self)
   create_mpublisher(self, *args, **kwargs)
   create_psubscriber(self, *args, **kwargs)
   create_publisher(self, *args, **kwargs)
   create_rpc(self, *args, **kwargs)
   create_rpc_client(self, *args, **kwargs)
   create_start_service(self, uri: str = None)
   create_stop_service(self, uri: str = None)
   create_subscriber(self, *args, **kwargs)
   run_forever(self, sleep_rate: float = 0.001)
   run(self)
   stop(self)
```

<!-- #### Communication Patters

![image](https://github.com/robotics-4-all/commlib-py/assets/4770702/b1a27e08-0ddd-4498-a882-1c255e36a1c4) -->


#### Req/Resp - RPCs

This README provides an introduction to using **Remote Procedure Calls (RPCs)** with `commlib-py`.
RPCs allow you to execute functions or methods on a remote system as if they were local, enabling seamless communication between distributed systems. Commlib simplifies the implementation of RPCs by providing a high-level API for defining, invoking, and managing remote procedures.

With `commlib`, you can:
- Define RPC endpoints for exposing specific functionalities.
- Call remote procedures from clients with minimal setup.
- Handle asynchronous responses using callbacks.

The following simple example  will walk you through the basic setup and usage of RPCs using `commlib-py`, helping you build scalable and efficient distributed applications.


##### Server Side Example

```python
from commlib.msg import RPCMessage
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters

class AddTwoIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0

def add_two_int_handler(msg):
    print(f'Request Message: {msg.__dict__}')
    resp = AddTwoIntMessage.Response(c = msg.a + msg.b)
    return resp

if __name__ == '__main__':
    conn_params = ConnectionParameters()
    node = Node(
        node_name='add_two_ints_node',
        connection_params=conn_params,
        # heartbeat_uri='nodes.add_two_ints.heartbeat',
        debug=True
    )
    rpc = node.create_rpc(
        msg_type=AddTwoIntMessage,
        rpc_name='add_two_ints_node.add_two_ints',
        on_request=add_two_int_handler
    )
    node.run_forever(sleep_rate=1)
```

##### Client Side Example

```python
import time

from commlib.msg import RPCMessage
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters

class AddTwoIntMessage(RPCMessage):
    class Request(RPCMessage.Request):
        a: int = 0
        b: int = 0

    class Response(RPCMessage.Response):
        c: int = 0

if __name__ == '__main__':
    conn_params = ConnectionParameters()
    node = Node(node_name='myclient', connection_params=conn_params)
    rpc = node.create_rpc_client(
        msg_type=AddTwoIntMessage,
        rpc_name='add_two_ints_node.add_two_ints'
    )
    node.run()

    # Create an instance of the request object
    msg = AddTwoIntMessage.Request()
    while True:
        # returns AddTwoIntMessage.Response instance
        resp = rpc.call(msg)
        print(resp)
        msg.a += 1
        msg.b += 1
        time.sleep(1)
```

#### Pub/Sub

Publish/Subscribe (PubSub) is a messaging pattern where senders (publishers) send messages to a topic without knowing the recipients (subscribers). Subscribers express interest in specific topics and receive messages published to those topics. This decouples the producers and consumers, enabling scalable and flexible communication.

With `commlib-py`, implementing PubSub is straightforward. The library provides high-level abstractions for creating publishers and subscribers, allowing you to focus on your application's logic rather than the underlying transport mechanisms. You can define custom message types, publish data to topics, and handle incoming messages with ease.

Key features of PubSub in `commlib-py`:
- **Topic-based Communication**: Messages are categorized by topics, enabling selective subscription.
- **Broker Agnostic**: Supports multiple brokers like MQTT, Redis, and AMQP.
- **Typed Message-driven Communication**: Define structured messages using Python classes.
- **Ease of Use**: Simplified APIs for creating publishers and subscribers.

This section will guide you through creating a simple publisher and subscriber using `commlib-py`. You'll learn how to define message types, publish data, and process received messages effectively.

##### Write a Simple Publisher

```python
from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters

class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2

class SonarMessage(PubSubMessage):
    distance: float = 0.001
    horizontal_fov: float = 30.0
    vertical_fov: float = 14.0

if __name__ == "__main__":
    conn_params = ConnectionParameters(host='localhost', port=1883)
    node = Node(node_name='sensors.sonar.front', connection_params=conn_params)
    pub = node.create_publisher(msg_type=SonarMessage, topic='sensors.sonar.front')
    node.run()
    msg = SonarMessage()
    while True:
        pub.publish(msg)
        msg.range += 1
        time.sleep(1)
```

##### Write a Simple Subscriber

```python
#!/usr/bin/env python

import time
from commlib.msg import MessageHeader, PubSubMessage
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters

class SonarMessage(PubSubMessage):
    header: MessageHeader = MessageHeader()
    range: float = -1
    hfov: float = 30.6
    vfov: float = 14.2

def on_message(msg):
    print(f'Received front sonar data: {msg}')

if __name__ == '__main__':
    conn_params = ConnectionParameters()

    node = Node(node_name='node.obstacle_avoidance', connection_params=conn_params)

    node.create_subscriber(msg_type=SonarMessage,
                           topic='sensors.sonar.front',
                           on_message=on_message)  # Define a callback function

    node.run_forever(sleep_rate=1)  # Define a process-level sleep rate in hz
```

#### Wildcard Subscriptions

For pattern-based topic subscriptions using **wildcards** one can also use the `PSubscriber` class directly.

For multi-topic publisher one can also use the `MPublisher` class directly.


```python
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters

def on_msg_callback(msg, topic):
    print(f'Message at topic <{topic}>: {msg}')

if __name__ == '__main__':
    conn_params = ConnectionParameters()
    node = Node(node_name='wildcard_subscription_example',
                connection_params=conn_params)

    # Create a pattern subscriber
    node.create_psubscriber(topic='topic.*', on_message=on_msg_callback)
    # Create a multi-topic publisher instance.
    pub = node.create_mpublisher()
    node.run(wait=True)

    topicA = 'topic.a'
    topicB = 'topic.b'

    while True:
        pub.publish({'a': 1}, topicA)
        pub.publish({'b': 1}, topicB)
        time.sleep(1)
```

#### Preemptive Services with Feedback (Actions)

Actions are [pre-emptive services](https://en.wikipedia.org/wiki/Preemption_(computing)) with support for asynchronous feedback publishing. This communication pattern is used to implement services which can be stopped and can provide feedback data, such as the move command service of a robot.

The example below shows how to use Actions to implement preemptive robot motion services, with integrated feedback functionality. In this example we implement the `MoveByDistance` command service for our custom Lab robot. The message structure (`MoveByDistanceMsg`) is defined by the `Goal`, `Result` and `Feedback` classes. The logic is that we set a distance goal (in cm) and we monitor the progress through the feedback channel, which for commlib-py it is automatically captured.

##### Write an Action Service

```python
import time

from commlib.action import GoalStatus
from commlib.msg import ActionMessage
from commlib.transports.redis import ConnectionParameters
)

class MoveByDistanceMsg(ActionMessage):
    class Goal(ActionMessage.Goal):
        target_cm: int = 0

    class Result(ActionMessage.Result):
        dest_cm: int = 0

    class Feedback(ActionMessage.Feedback):
        current_cm: int = 0

def on_goal_request(goal_h):
    c = 0
	goal_req_data = goal_h.data  # Retrieve goal request data from goal handler
    res = MoveByDistanceMsg.Result()  # Goal Result Message
    while c < goal_h.data.target_cm:
        if goal_h.cancel_event.is_set():  # Use the cancel_event property of goal handler instance
            break
        goal_h.send_feedback(MoveByDistanceMsg.Feedback(current_cm=c))
        c += 1
        time.sleep(1)
    res.dest_cm = c
    return res

if __name__ == '__main__':
    action_name = 'myrobot.move.distance'
    conn_params = ConnectionParameters()
    node = Node(node_name='myrobot.node.motion',  # A node can provide several motion interfaces
                connection_params=conn_params)
    node.create_action(msg_type=MoveByDistanceMsg,
                       action_name=action_name,
                       on_goal=on_goal_request)
    node.run_forever()
```

##### Write an Action Client

```python
import time

from commlib.action import GoalStatus
from commlib.msg import ActionMessage
from commlib.transports.redis import ActionClient, ConnectionParameters


class MoveByDistanceMsg(ActionMessage):
    class Goal(ActionMessage.Goal):
        target_cm: int = 0

    class Result(ActionMessage.Result):
        dest_cm: int = 0

    class Feedback(ActionMessage.Feedback):
        current_cm: int = 0


def on_feedback(feedback):
    print(f'ActionClient <on-feedback> callback: {feedback}')


def on_result(result):
    print(f'ActionClient <on-result> callback: {result}')


def on_goal_reached(result):
    print(f'ActionClient <on-goal-reached> callback: {result}')


if __name__ == '__main__':
    action_name = 'testaction'
    conn_params = ConnectionParameters()
    node = Node(node_name='action_client_example_node',
                connection_params=conn_params)
    action_client = node.create_action_client(
        msg_type=MoveByDistanceMsg,
        action_name=action_name,
        on_goal_reached=on_goal_reached,
        on_feedback=on_feedback,
        on_result=on_result
    )
    node.run()
    goal_msg = MoveByDistanceMsg.Goal(target_cm=5)
    action_client.send_goal(goal_msg)
    resp = action_client.get_result(wait=True)
    print(f'Action Result: {resp}')
    node.stop()
```


## 📺 Advanced

### Endpoints (Low-level API)

It is possible to construct endpoints without binding them to a specific Node. This is a feature to support a wider range of applications, where the concept Node might not be usable.

One can create endpoint instances by using the following classes of each supported transport:

| Endpoint Type          | Description                                      | Required Parameters                                                                 | Supported Protocols       |
|-------------------------|--------------------------------------------------|-------------------------------------------------------------------------------------|---------------------------|
| **RPCClient**          | Sends RPC requests and waits for responses.      | `msg_type`, `rpc_name`, `connection_params`                                         | MQTT, Redis, AMQP, Kafka  |
| **RPCServer**          | Handles RPC requests and sends responses.        | `msg_type`, `rpc_name`, `on_request`, `connection_params`                           | MQTT, Redis, AMQP, Kafka  |
| **Publisher**          | Sends messages to a specific topic.              | `msg_type`, `topic`, `connection_params`                                           | MQTT, Redis, AMQP, Kafka  |
| **Subscriber**         | Listens for messages on a specific topic.        | `msg_type`, `topic`, `on_message`, `connection_params`                              | MQTT, Redis, AMQP, Kafka  |
| **MPublisher**         | Publishes messages to multiple topics.           | `connection_params`                                                                 | MQTT, Redis, AMQP, Kafka  |
| **WPublisher**         | A wrapped publisher with additional features.    | `msg_type`, `topic`, `connection_params`                                           | MQTT, Redis  |
| **PSubscriber**        | Subscribes to topics using patterns.             | `topic_pattern`, `on_message`, `connection_params`                                  | MQTT, Redis, AMQP, Kafka  |
| **WSubscriber**        | A wrapped subscriber with additional features.   | `msg_type`, `topic`, `on_message`, `connection_params`                              | MQTT, Redis  |
| **ActionService**      | Provides preemptive services with feedback.      | `msg_type`, `action_name`, `on_goal`, `connection_params`                           | MQTT, Redis, AMQP  |
| **ActionClient**       | Sends goals to an action service and receives feedback. | `msg_type`, `action_name`, `on_feedback`, `on_result`, `connection_params`          | MQTT, Redis, AMQP  |

```python
from commlib.transports.redis import RPCService
from commlib.transports.amqp import Subscriber
from commlib.transports.mqtt import Publisher, RPCClient
...
```

Or use the `endpoint_factory` to construct endpoints.

```python
import time
from commlib.endpoints import endpoint_factory, EndpointType, TransportType

def callback(data):
    print(data)

if __name__ == '__main__':
    topic = 'endpoints_factory_example'

    mqtt_sub = endpoint_factory(
        EndpointType.Subscriber,
        TransportType.MQTT)(topic=topic, on_message=callback)
    mqtt_sub.run()

    mqtt_pub = endpoint_factory(
        EndpointType.Publisher,
        TransportType.MQTT)(topic=topic, debug=True)
	mqtt_pub.run()

    data = {'a': 1, 'b': 2}
    while True:
        mqtt_pub.publish(data)
        time.sleep(1)
```

### B2B bridges
In the context of IoT and CPS, it is a common requirement to bridge messages between message brokers, based on application-specific rules. An example is to bridge analytics (preprocessed) data from the Edge to the Cloud. And what happens if the brokers use different communication protocols?

Commlib builds a thin layer on top of the internal PubSub and RPC API to provide a protocol-agnostic implementation of Broker-to-Broker bridges.

<div align="center">
<img src="https://github.com/robotics-4-all/commlib-py/assets/4770702/98993090-abfd-4e9f-b16e-ad9b7f436987">
</div>

Below are examples of:
1. A Redis-to-MQTT RPC Bridge
2. A Redis-to-MQTT Topic Bridge.

```python
#!/usr/bin/env python

import time

import commlib.transports.amqp as acomm
import commlib.transports.redis as rcomm
import commlib.transports.mqtt as mcomm

from commlib.bridges import (
    RPCBridge, RPCBridgeType, TopicBridge, TopicBridgeType
)


def redis_to_mqtt_rpc_bridge():
    """
    [RPC Client] ----> [Broker A] ------> [Broker B] ---> [RPC Service]
    """
    bA_params = rcomm.ConnectionParameters()
    bB_params = mcomm.ConnectionParameters()
    bA_uri = 'ops.start_navigation'
    bB_uri = 'thing.robotA.ops.start_navigation'
    br = RPCBridge(RPCBridgeType.REDIS_TO_MQTT,
                   from_uri=bA_uri, to_uri=bB_uri,
                   from_broker_params=bA_params,
                   to_broker_params=bB_params,
                   debug=False)
    br.run()


def redis_to_mqtt_topic_bridge():
    """
    [Producer Endpoint] ---> [Broker A] ---> [Broker B] ---> [Consumer Endpoint]
    """
    bA_params = rcomm.ConnectionParameters()
    bB_params = mcomm.ConnectionParameters()
    bA_uri = 'sonar.front'
    bB_uri = 'thing.robotA.sensors.sonar.font'
    br = TopicBridge(TopicBridgeType.REDIS_TO_MQTT,
                     from_uri=bA_uri, to_uri=bB_uri,
                     from_broker_params=bA_params,
                     to_broker_params=bB_params,
                     debug=False)
    br.run()


if __name__ == '__main__':
    redis_to_mqtt_rpc_bridge()
    redis_to_mqtt_topic_bridge()
```

A Pattern-based Topic Bridge (PTopicBridge) example is also shown below. In this example, we use static definition of messages (`SonarMessage`), also referred as `typed communication`.

### TCP Bridge

TCP bridge forwards tcp packages between two endpoints:

```

[Client] -------> [TCPBridge, port=xxxx] ---------> [TCP endpoint, port=xxxx]

```

A one-to-one connection is performed between the bridge and the endpoint.

## REST Proxy

Implements a **REST proxy**, that enables ***invocation of REST services via message brokers***. The proxy uses an RPCService to run the broker endpoint and an http client for calling REST services. An RPC call is transformed into proper, REST-compliant, http request, based on the input parameters.

<div align="center">
<img src="https://github.com/robotics-4-all/commlib-py/assets/4770702/1507cb10-00ec-49ce-8159-967c23d1ba72">
</div>

Responses from the REST services have the following **RESTProxyMessage** schema:

```python
class RESTProxyMessage(RPCMessage):
    class Request(RPCMessage.Request):
        base_url: str
        path: str = '/'
        verb: str = 'GET'
        query_params: Dict[str, Any] = {}
        path_params: Dict[str, Any] = {}
        body_params: Dict[str, Any] = {}
        headers: Dict[str, Any] = {}

    class Response(RPCMessage.Response):
        data: Union[str, Dict, int]
        headers: Dict[str, Any]
        status_code: int = 200
```

Head to [this repo](https://github.com/robotics-4-all/commlib-rest-proxy) for an implementation of a dockerized application that implements a REST Proxy using commlib-py.

## 🧪 Testing

Commlib-py uses the pytest framework. Run the test suite with:

**Using [pip](https://pypi.org/project/pip/):**
```sh
pytest
```
**Using [poetry](https://python-poetry.org/):**
```sh
poetry run pytest
```
**Using [conda](https://docs.conda.io/):**
```sh
conda activate {venv}
pytest
```

---

## 🎞️ Roadmap

- [X] **`Task 1`**: <strike>Protocol-agnostic architecture</strike>
- [x] **`Task 2`**: <strike>Support the AMQP and MQTT protocols</strike>
- [x] **`Task 3`**: <strike>Support Redis protocol</strike>
- [ ] **`Task 4`**: Support Kafka protocol (Under development / Partial Support)
- [ ] **`Task 5`**: RPCServer implementation for AMQP and Kafka transports
- [ ] **`Task 6`**: Comprehensive testing

---

## 🤝 Contributing

- **💬 [Join the Discussions](https://github.com/robotics-4-all/commlib-py/discussions)**: Share your insights, provide feedback, or ask questions.
- **🐛 [Report Issues](https://github.com/robotics-4-all/commlib-py/issues)**: Submit bugs found or log feature requests for the `commlib-py-2` project.
- **💡 [Submit Pull Requests](https://github.com/robotics-4-all/commlib-py/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your LOCAL account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone https://github.com/{FORKED_ACCOUNT}/commlib-py.git
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to LOCAL**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
8. **Review**: Once your PR is reviewed and approved, it will be merged into the main branch. Congratulations on your contribution!
</details>

<details closed>
<summary>Contributor Graph</summary>
<br>
<p align="left">
   <a href="https://github.com/robotics-4-all/commlib-py/graphs/contributors">
      <img src="https://contrib.rocks/image?repo=robotics-4-all/commlib-py">
   </a>
</p>
</details>

---

## 📜 License

Commlib-py is protected under the [MIT ](https://choosealicense.com/licenses/mit/) License. For more details, refer to the [MIT LICENSE](https://choosealicense.com/licenses/mit/) uri.

---

## 🎩 Acknowledgments

- Credit `contributors`, `inspiration`, `references`, etc.

<div align="right">

[![][back-to-top]](#top)

</div>


[back-to-top]: https://img.shields.io/badge/-BACK_TO_TOP-151515?style=flat-square


---
