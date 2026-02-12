#!/usr/bin/env python3

import argparse
import time
import statistics
import threading
import os
import multiprocessing
from typing import List, Any, Optional
import psutil

from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)
from rich.panel import Panel
from rich import box

from commlib.node import Node
from commlib.msg import PubSubMessage
from commlib.utils import get_timestamp_ns

try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

console = Console()


class PerfMessage(PubSubMessage):
    data: str
    ts: int


class ResourceMonitor:
    def __init__(self, interval: float = 0.1):
        self.interval = interval
        self.cpu_usages = []
        self.mem_usages = []
        self.stop_event = threading.Event()
        self.process = psutil.Process(os.getpid())
        self.process.cpu_percent(None)
        self.thread: Optional[threading.Thread] = None

    def _monitor(self):
        while not self.stop_event.is_set():
            try:
                cpu = self.process.cpu_percent(None)
                mem = self.process.memory_info().rss / (1024 * 1024)  # MB
                self.cpu_usages.append(cpu)
                self.mem_usages.append(mem)
            except Exception:
                pass
            time.sleep(self.interval)

    def start(self):
        self.stop_event.clear()
        self.cpu_usages = []
        self.mem_usages = []
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        return {
            "avg_cpu": statistics.mean(self.cpu_usages) if self.cpu_usages else 0,
            "avg_mem": statistics.mean(self.mem_usages) if self.mem_usages else 0,
        }


class RealTimePlotter:
    def __init__(self, data_queue: multiprocessing.Queue):
        self.data_queue = data_queue
        self.xs = []
        self.ys = []
        self.zs = []
        self.cs = []  # Colors (Size)
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.sc = None

    def update(self, _frame):
        try:
            while not self.data_queue.empty():
                data = self.data_queue.get_nowait()
                if data is None:
                    return
                self.xs.append(data["num_subs"])
                self.ys.append(data["target_freq"])
                self.zs.append(data["avg_latency"])
                self.cs.append(data["data_size_kb"])
        except Exception:
            pass

        if not self.xs:
            return

        self.ax.clear()
        self.ax.set_xlabel("Subscribers")
        self.ax.set_ylabel("Frequency (Hz)")
        self.ax.set_zlabel("Latency (ms)")
        self.ax.set_title("Real-time Performance Metrics")

        # Scatter plot
        self.sc = self.ax.scatter(
            self.xs, self.ys, self.zs, c=self.cs, cmap="viridis", marker="o"
        )
        # Colorbar might be tricky to update repeatedly
        # self.fig.colorbar(self.sc, label='Data Size (KB)')

    def start(self):
        ani = animation.FuncAnimation(self.fig, self.update, interval=1000)
        plt.show()


class PubSubPerfTest:
    def __init__(self, broker: str, topic: str = "perf.test"):
        self.broker = broker
        self.topic = topic
        self.conn_params = self._get_conn_params(broker)
        self.latencies = []
        self.msg_count = 0
        self.first_msg_ts = 0
        self.last_msg_ts = 0
        self.monitor = ResourceMonitor()

    def _get_conn_params(self, broker: str):
        if broker == "redis":
            from commlib.transports.redis import ConnectionParameters
        elif broker == "amqp":
            from commlib.transports.amqp import ConnectionParameters
        elif broker == "mqtt":
            from commlib.transports.mqtt import ConnectionParameters
        elif broker == "kafka":
            from commlib.transports.kafka import ConnectionParameters
        else:
            raise ValueError(f"Unsupported broker: {broker}")
        return ConnectionParameters(reconnect_attempts=0)

    def on_message(self, msg: PerfMessage):
        now = get_timestamp_ns()
        if self.msg_count == 0:
            self.first_msg_ts = now
        self.last_msg_ts = now

        latency_ms = (now - msg.ts) / 1_000_000.0
        self.latencies.append(latency_ms)
        self.msg_count += 1

    def run_single_size(
        self,
        num_subs: int,
        size_kb: int,
        target_freq: int,
        num_messages: int,
        _node: Node,
        pub: Any,
    ):
        # Reset counters for this data size
        self.latencies = []
        self.msg_count = 0
        self.first_msg_ts = 0
        self.last_msg_ts = 0

        data_str = "x" * (size_kb * 1024)
        self.monitor.start()

        pub_start_ns = get_timestamp_ns()
        pub_start = time.time()
        for i in range(num_messages):
            msg = PerfMessage(data=data_str, ts=get_timestamp_ns())
            pub.publish(msg)
            if target_freq > 0 and i < num_messages - 1:
                time.sleep(1.0 / target_freq)
        pub_end = time.time()

        expected_total_msgs = num_messages * num_subs
        timeout = 20 + (expected_total_msgs * 0.05)
        wait_start = time.time()
        while (
            self.msg_count < expected_total_msgs
            and (time.time() - wait_start) < timeout
        ):
            time.sleep(0.1)

        resources = self.monitor.stop()

        pub_duration = pub_end - pub_start
        pub_freq = num_messages / pub_duration if pub_duration > 0 else 0

        # Measure receive duration from the moment the publisher started
        recv_duration_ns = self.last_msg_ts - pub_start_ns
        recv_duration = recv_duration_ns / 1_000_000_000.0
        # Calculate per-subscriber receive frequency
        recv_freq = (
            (self.msg_count / num_subs) / recv_duration if recv_duration > 0 else 0
        )

        avg_latency = statistics.mean(self.latencies) if self.latencies else 0
        success_rate = (
            (self.msg_count / expected_total_msgs) * 100
            if expected_total_msgs > 0
            else 0
        )

        return {
            "num_subs": num_subs,
            "data_size_kb": size_kb,
            "target_freq": target_freq,
            "avg_latency": avg_latency,
            "pub_freq": pub_freq,
            "recv_freq": recv_freq,
            "avg_cpu": resources["avg_cpu"],
            "avg_mem": resources["avg_mem"],
            "success_rate": success_rate,
        }

    def _worker_run_subs(
        self,
        num_subs: int,
        sizes_list: List[int],
        freqs_list: List[int],
        num_messages: int,
        results_queue: multiprocessing.Queue,
    ):
        for size_kb in sizes_list:
            # Start Node for this run
            node = Node(
                node_name=f"perf_node_s{num_subs}_d{size_kb}",
                connection_params=self.conn_params,
                heartbeats=False,
            )
            for i in range(num_subs):
                node.create_subscriber(
                    topic=self.topic, msg_type=PerfMessage, on_message=self.on_message
                )
            pub = node.create_publisher(topic=self.topic, msg_type=PerfMessage)
            node.run(wait=True)
            time.sleep(1.0)

            for target_freq in freqs_list:
                res = self.run_single_size(
                    num_subs, size_kb, target_freq, num_messages, node, pub
                )
                results_queue.put(res)
                time.sleep(0.5)

            node.stop(wait=True)
            time.sleep(1.0)  # Cool down between sizes

        # Signal completion for this sub block
        results_queue.put(None)

    def run_benchmark(
        self,
        subs_list: List[int],
        sizes_list: List[int],
        freqs_list: List[int],
        num_messages: int,
        plot_queue: multiprocessing.Queue = None,
    ):
        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            total_steps = len(subs_list) * len(sizes_list) * len(freqs_list)
            overall_task = progress.add_task(
                "[yellow]Benchmarking...", total=total_steps
            )

            for num_subs in subs_list:
                results_queue = multiprocessing.Queue()
                process = multiprocessing.Process(
                    target=self._worker_run_subs,
                    args=(
                        num_subs,
                        sizes_list,
                        freqs_list,
                        num_messages,
                        results_queue,
                    ),
                )
                process.start()

                while True:
                    res = results_queue.get()
                    if res is None:  # Sub block finished
                        break
                    results.append(res)
                    if plot_queue:
                        plot_queue.put(res)
                    progress.update(
                        overall_task,
                        advance=1,
                        description=(
                            f"[cyan]Subs={res['num_subs']},"
                            f" Size={res['data_size_kb']}KB,"
                            f" Freq={res['target_freq']}Hz"
                        ),
                    )

                process.join()
                time.sleep(1.0)  # Cool down between subscriber counts

        return results


def main():
    parser = argparse.ArgumentParser(description="PubSub Performance Test")
    parser.add_argument(
        "--broker",
        type=str,
        required=True,
        choices=["redis", "amqp", "mqtt", "kafka"],
        help="Broker to use",
    )
    parser.add_argument(
        "--num-messages", type=int, default=100, help="Number of messages per data size"
    )
    parser.add_argument(
        "--max-size-kb", type=int, default=512, help="Maximum data size in KB to test"
    )
    parser.add_argument(
        "--start-size-kb", type=int, default=2, help="Starting data size in KB"
    )
    parser.add_argument(
        "--step-size-kb",
        type=int,
        default=2,
        help="Step size in KB (for linear strategy)",
    )
    parser.add_argument(
        "--size-strategy",
        type=str,
        default="predefined",
        choices=["linear", "exponential", "predefined"],
        help="Strategy for increasing data size",
    )
    parser.add_argument(
        "--max-subs", type=int, default=16, help="Maximum number of subscribers to test"
    )
    parser.add_argument(
        "--start-subs", type=int, default=1, help="Starting number of subscribers"
    )
    parser.add_argument(
        "--step-subs",
        type=int,
        default=2,
        help="Step for subscriber count (for linear strategy)",
    )
    parser.add_argument(
        "--subs-strategy",
        type=str,
        default="exponential",
        choices=["linear", "exponential", "predefined"],
        help="Strategy for increasing subscriber count",
    )
    parser.add_argument(
        "--subs",
        type=int,
        nargs="+",
        default=[1, 5, 10],
        help="Predefined list of subscriber counts (used if strategy is 'predefined')",
    )
    parser.add_argument("--topic", type=str, default="perf.test", help="Topic to use")
    parser.add_argument(
        "--start-freq-exp",
        type=int,
        default=0,
        help="Starting exponent for frequency (2^x)",
    )
    parser.add_argument(
        "--max-freq-exp",
        type=int,
        default=6,
        help="Maximum exponent for frequency (2^x)",
    )
    parser.add_argument(
        "--plot", action="store_true", help="Enable real-time 3D plotting"
    )

    args = parser.parse_args()

    console.print(
        Panel.fit(
            f"[bold blue]PubSub Performance Benchmark[/bold blue]\n"
            f"Broker: [green]{args.broker}[/green]\n"
            f"Messages/Size: [green]{args.num_messages}[/green]\n"
            f"Max Size: [green]{args.max_size_kb} KB[/green]"
            f" (Strategy: [green]{args.size_strategy}[/green])\n"
            f"Max Subs: [green]{args.max_subs}[/green]"
            f" (Strategy: [green]{args.subs_strategy}[/green])\n"
            f"Freq Range: [green]2^{args.start_freq_exp} - 2^{args.max_freq_exp} Hz[/green]\n"
            f"Logic: [italic]Fixed Subs -> Variable Data Size -> Variable Freq[/italic]",
            box=box.DOUBLE,
        )
    )

    tester = PubSubPerfTest(args.broker, args.topic)

    # Generate Subscriber List
    if args.subs_strategy == "linear":
        subs_list = []
        curr = args.start_subs
        while curr <= args.max_subs:
            subs_list.append(curr)
            curr += args.step_subs
    elif args.subs_strategy == "exponential":
        subs_list = []
        curr = args.start_subs
        while curr <= args.max_subs:
            subs_list.append(curr)
            curr *= 2
    else:  # predefined
        subs_list = args.subs

    if (
        args.max_subs not in subs_list
        and args.max_subs > 0
        and args.subs_strategy != "predefined"
    ):
        subs_list.append(args.max_subs)
        subs_list.sort()

    # Generate Size List
    if args.size_strategy == "linear":
        sizes_list = []
        curr = args.start_size_kb
        while curr <= args.max_size_kb:
            sizes_list.append(curr)
            curr += args.step_size_kb
    elif args.size_strategy == "exponential":
        sizes_list = []
        curr = args.start_size_kb
        while curr <= args.max_size_kb:
            sizes_list.append(curr)
            curr *= 2
    else:  # predefined
        all_sizes = [2, 4, 8, 16, 32, 64, 128, 256, 512]
        sizes_list = [s for s in all_sizes if s <= args.max_size_kb]

    # Ensure at least the max size is tested if it's not in the list
    if args.max_size_kb not in sizes_list and args.max_size_kb > 0:
        sizes_list.append(args.max_size_kb)
        sizes_list.sort()

    # Generate Frequency List
    freqs_list = [2**x for x in range(args.start_freq_exp, args.max_freq_exp + 1)]

    plot_queue = None
    plot_process = None
    if args.plot:
        if not HAS_MATPLOTLIB:
            console.print("[red]matplotlib not installed. Plotting disabled.[/red]")
        else:
            plot_queue = multiprocessing.Queue()
            plotter = RealTimePlotter(plot_queue)
            plot_process = multiprocessing.Process(target=plotter.start)
            plot_process.start()

    try:
        results = tester.run_benchmark(
            subs_list, sizes_list, freqs_list, args.num_messages, plot_queue
        )
    finally:
        if plot_process:
            plot_process.terminate()
            plot_process.join()

    # Final Table
    table = Table(
        title=f"Benchmark Results - {args.broker.upper()}",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    table.add_column("Subs", justify="right", style="cyan")
    table.add_column("Size (KB)", justify="right", style="cyan")
    table.add_column("Target Hz", justify="right", style="magenta")
    table.add_column("Lat (ms)", justify="right", style="green")
    table.add_column("Pub (Hz)", justify="right", style="yellow")
    table.add_column("Recv (Hz)", justify="right", style="yellow")
    table.add_column("CPU (%)", justify="right", style="red")
    table.add_column("MEM (MB)", justify="right", style="red")
    table.add_column("Succ (%)", justify="right", style="blue")

    for r in results:
        table.add_row(
            str(r["num_subs"]),
            str(r["data_size_kb"]),
            str(r["target_freq"]),
            f"{r['avg_latency']:.2f}",
            f"{r['pub_freq']:.2f}",
            f"{r['recv_freq']:.2f}",
            f"{r['avg_cpu']:.1f}",
            f"{r['avg_mem']:.1f}",
            f"{r['success_rate']:.1f}",
        )

    console.print("\n")
    console.print(table)


if __name__ == "__main__":
    main()
