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
	- [📺 Usage](#-usage)
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

### 📜 Project Index

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
				<tr style='border-bottom: 1px solid #eee;'>
					<td style='padding: 8px;'><b><a href='https://github.com/robotics-4-all/commlib-py/commlib/.editorconfig'>.editorconfig</a></b></td>
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

	**Using [tox](None):**

	```sh
	❯ echo 'INSERT-INSTALL-COMMAND-HERE'
	```

### 📺 Usage

Run the project with:

**Using [docker](https://www.docker.com/):**
```sh
docker run -it {image_name}
```
**Using [pip](https://pypi.org/project/pip/):**
```sh
python {entrypoint}
```
**Using [poetry](https://python-poetry.org/):**
```sh
poetry run python {entrypoint}
```
**Using [conda](https://docs.conda.io/):**
```sh
conda activate {venv}
python {entrypoint}
```
**Using [tox](None):**
```sh
echo 'INSERT-RUN-COMMAND-HERE'
```

## 🧪 Testing

Commlib-py-2 uses the {__test_framework__} test framework. Run the test suite with:

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
**Using [tox](None):**
```sh
echo 'INSERT-TEST-COMMAND-HERE'
```

---

## 🎞️ Roadmap

- [X] **`Task 1`**: <strike>Implement feature one.</strike>
- [ ] **`Task 2`**: Implement feature two.
- [ ] **`Task 3`**: Implement feature three.

---

## 🤝 Contributing

- **💬 [Join the Discussions](https://LOCAL/commlib/commlib-py-2/discussions)**: Share your insights, provide feedback, or ask questions.
- **🐛 [Report Issues](https://LOCAL/commlib/commlib-py-2/issues)**: Submit bugs found or log feature requests for the `commlib-py-2` project.
- **💡 [Submit Pull Requests](https://LOCAL/commlib/commlib-py-2/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your LOCAL account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone /home/klpanagi/Development/commlib/commlib-py-2
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
   <a href="https://LOCAL{/commlib/commlib-py-2/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=commlib/commlib-py-2">
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
