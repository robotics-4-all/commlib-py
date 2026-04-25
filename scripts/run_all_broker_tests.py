#!/usr/bin/env python3
"""Run all broker integration tests with Docker."""

import socket
import subprocess
import time
import sys
import os
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.panel import Panel
from rich import box

# Mapping of docker-compose services to broker types used in test scripts
SERVICES = {
    "emqx": "mqtt",
    "mosquitto": "mqtt",
    "redis": "redis",
    "dragonfly": "redis",
    "rabbitmq": "amqp",
    "kafka": "kafka",
}

TEST_SCRIPTS = [
    "scripts/test_action_basic.py",
    "scripts/test_rpc_basic.py",
    "scripts/test_pubsub_basic.py",
]

COMPOSE_FILE = "brokers/docker-compose.yml"
console = Console()


def run_command(cmd, timeout=None, env=None):
    """Run command."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=env
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        partial_stdout = e.stdout or b""
        partial_stderr = e.stderr or b""
        if isinstance(partial_stdout, bytes):
            partial_stdout = partial_stdout.decode(errors="replace")
        if isinstance(partial_stderr, bytes):
            partial_stderr = partial_stderr.decode(errors="replace")
        return (
            -1,
            partial_stdout,
            f"Timeout expired after {timeout}s\n{partial_stderr}",
        )
    except Exception as e:
        return -1, "", str(e)


# Per-service TCP readiness probe: (host, port)
SERVICE_PROBE = {
    "kafka": ("127.0.0.1", 9092),
}

# Extra seconds to wait after TCP probe succeeds (broker initialisation)
SERVICE_EXTRA_WAIT = {
    "emqx": 10,
    "mosquitto": 10,
    "redis": 10,
    "dragonfly": 10,
    "rabbitmq": 10,
    "kafka": 30,
}


def _tcp_probe(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def _kafka_ready(host: str = "127.0.0.1", port: int = 9092) -> bool:
    try:
        from confluent_kafka.admin import AdminClient, NewTopic

        admin = AdminClient(
            {"bootstrap.servers": f"{host}:{port}", "socket.timeout.ms": 2000}
        )
        fs = admin.create_topics(
            [NewTopic("__readiness_probe__", num_partitions=1, replication_factor=1)]
        )
        for _, f in fs.items():
            try:
                f.result()
            except Exception:
                pass
        admin.delete_topics(["__readiness_probe__"])
        return True
    except Exception:
        return False


def wait_for_healthy(service, progress, task_id, timeout=90):
    """Wait for healthy."""
    start_time = time.time()
    probe = SERVICE_PROBE.get(service)
    while time.time() - start_time < timeout:
        rc, stdout, _stderr = run_command(
            f"docker-compose -f {COMPOSE_FILE} ps {service} --format json"
        )
        if rc == 0 and stdout:
            if '"Health":"healthy"' in stdout or '"State":"running"' in stdout:
                if probe:
                    probe_start = time.time()
                    while time.time() - probe_start < 60:
                        if _tcp_probe(*probe):
                            break
                        time.sleep(2)
                        progress.update(task_id, advance=2)
                    kafka_probe_start = time.time()
                    while time.time() - kafka_probe_start < 60:
                        if _kafka_ready(*probe):
                            break
                        time.sleep(3)
                        progress.update(task_id, advance=3)
                extra = SERVICE_EXTRA_WAIT.get(service, 5)
                for _ in range(extra):
                    progress.update(task_id, advance=1)
                    time.sleep(1)
                return True
        time.sleep(2)
        progress.update(task_id, advance=2)
    return False


def main():
    """Main."""
    results = []

    # Setup environment
    env = os.environ.copy()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env["PYTHONPATH"] = project_root

    # Use venv python if available
    venv_python = os.path.join(project_root, "venv", "bin", "python3")
    python_exe = venv_python if os.path.exists(venv_python) else sys.executable

    console.print(
        Panel.fit(
            "[bold blue]Commlib-py Broker Test Suite[/bold blue]\n"
            f"[dim]Python: {python_exe}[/dim]\n"
            f"[dim]Project Root: {project_root}[/dim]",
            box=box.DOUBLE,
        )
    )

    run_command(f"docker-compose -f {COMPOSE_FILE} down --remove-orphans")

    for service, broker_type in SERVICES.items():
        console.print(
            f"\n[bold yellow]Testing Service:[/bold yellow]"
            f" [bold cyan]{service}[/bold cyan]"
            f" [dim]({broker_type})[/dim]"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            # Start Service
            start_task = progress.add_task(f"Starting {service}...", total=10)
            services_to_start = (
                f"zookeeper {service}" if service == "kafka" else service
            )
            rc, stdout, stderr = run_command(
                f"docker-compose -f {COMPOSE_FILE} up -d {services_to_start}"
            )
            progress.update(start_task, completed=10)

            if rc != 0:
                console.print(
                    f"[bold red]✘ Failed to start {service}:[/bold red] {stderr}"
                )
                results.append(
                    {
                        "service": service,
                        "broker": broker_type,
                        "status": "FAILED (Start)",
                        "details": stderr,
                    }
                )
                continue

            # Wait for Health
            health_task = progress.add_task(
                f"Waiting for {service} health...", total=60
            )
            if not wait_for_healthy(service, progress, health_task):
                console.print(
                    f"[bold orange3]⚠ Service {service}"
                    " health check timed out,"
                    " proceeding anyway...[/bold orange3]"
                )
            progress.update(health_task, completed=60)

            service_results = []
            all_passed = True

            log_dir = os.path.join(project_root, "logs", "integration")
            os.makedirs(log_dir, exist_ok=True)

            for script in TEST_SCRIPTS:
                script_name = os.path.basename(script)
                test_task = progress.add_task(f"Running {script_name}...", total=1)

                test_timeout = 180 if service == "kafka" else 60
                cmd = f"{python_exe} -u {script} --broker {broker_type}"
                rc, stdout, stderr = run_command(cmd, timeout=test_timeout, env=env)

                log_path = os.path.join(
                    log_dir, f"{service}_{script_name.replace('.py', '')}.log"
                )
                with open(log_path, "w") as fh:
                    fh.write(f"# cmd: {cmd}\n# rc: {rc}\n# timeout: {test_timeout}s\n")
                    fh.write("\n===== STDOUT =====\n")
                    fh.write(stdout or "")
                    fh.write("\n===== STDERR =====\n")
                    fh.write(stderr or "")

                if rc == 0 and "SUCCESS" in stdout and "FAILURE" not in stdout:
                    service_results.append(
                        (script_name, "[bold green]PASSED[/bold green]")
                    )
                else:
                    service_results.append(
                        (
                            script_name,
                            f"[bold red]FAILED[/bold red] [dim](rc={rc}, log={log_path})[/dim]",
                        )
                    )
                    all_passed = False

                progress.update(test_task, completed=1)

            results.append(
                {
                    "service": service,
                    "broker": broker_type,
                    "status": "[bold green]PASSED[/bold green]"
                    if all_passed
                    else "[bold red]FAILED[/bold red]",
                    "tests": service_results,
                }
            )

            # Stop Service
            stop_task = progress.add_task(f"Stopping {service}...", total=10)
            run_command(f"docker-compose -f {COMPOSE_FILE} stop {service}")
            if service == "kafka":
                run_command(f"docker-compose -f {COMPOSE_FILE} stop zookeeper")
            progress.update(stop_task, completed=10)

    # Final Report
    console.print("\n")
    table = Table(
        title="[bold blue]Final Test Report[/bold blue]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Service", style="cyan", no_wrap=True)
    table.add_column("Broker", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Test Details", ratio=1)

    total_passed = 0
    for res in results:
        if "PASSED" in res["status"]:
            total_passed += 1

        test_details = ""
        if "tests" in res:
            test_details = "\n".join(
                [f"• {name}: {stat}" for name, stat in res["tests"]]
            )
        elif "details" in res:
            test_details = f"[dim]{res['details'].strip()}[/dim]"

        table.add_row(res["service"], res["broker"], res["status"], test_details)

    console.print(table)

    summary_color = "green" if total_passed == len(SERVICES) else "yellow"
    console.print(
        Panel(
            f"[{summary_color}]Summary:"
            f" {total_passed}/{len(SERVICES)}"
            f" services passed all tests."
            f"[/{summary_color}]",
            box=box.ROUNDED,
            expand=False,
        )
    )


if __name__ == "__main__":
    main()
