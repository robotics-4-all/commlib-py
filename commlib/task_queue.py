"""Task queue producer and worker implementations.

Provides base classes for the task/job queue communication pattern with
competing consumers, priorities, retries, DLQ, progress reporting, and
configurable acknowledgment semantics.
"""

import logging
import threading
import time
import uuid
from enum import IntEnum
from typing import Any, Callable, Dict, Optional, Type

from pydantic import BaseModel, Field

from commlib.endpoints import BaseEndpoint
from commlib.msg import TaskMessage

task_queue_logger = None


class TaskStatus(IntEnum):
    PENDING = 1
    PROCESSING = 2
    COMPLETED = 3
    FAILED = 4
    RETRYING = 5
    DEAD_LETTER = 6


class AckPolicy(IntEnum):
    AUTO = 1
    MANUAL = 2


class TaskQueueConfig(BaseModel):
    queue_name: str = "default"
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff_multiplier: float = 2.0
    task_ttl: Optional[float] = None
    dlq_name: Optional[str] = None
    max_concurrent: int = 1
    ack_policy: int = AckPolicy.AUTO
    result_ttl: float = 3600.0
    progress_enabled: bool = True

    def get_dlq_name(self) -> str:
        if self.dlq_name is not None:
            return self.dlq_name
        return f"{self.queue_name}.dlq"


class TaskEnvelope(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    queue_name: str = ""
    priority: int = 0
    status: int = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = Field(default_factory=time.time)
    ttl: Optional[float] = None
    task_data: Dict[str, Any] = {}


class TaskResult(BaseModel):
    task_id: str = ""
    status: int = TaskStatus.COMPLETED
    result_data: Dict[str, Any] = {}
    error: str = ""
    completed_at: float = Field(default_factory=time.time)


class TaskProgress(BaseModel):
    task_id: str = ""
    progress_data: Dict[str, Any] = {}
    percent: float = 0.0


class TaskHandle:
    """Handle for a submitted task, used to track status and retrieve results."""

    def __init__(self, task_id: str, msg_type: Optional[Type[TaskMessage]] = None):
        self._task_id = task_id
        self._msg_type = msg_type
        self._status: int = TaskStatus.PENDING
        self._result: Optional[TaskResult] = None
        self._result_event = threading.Event()

    @property
    def task_id(self) -> str:
        return self._task_id

    @property
    def status(self) -> TaskStatus:
        return TaskStatus(self._status)

    @property
    def result(self) -> Optional[TaskResult]:
        return self._result

    @property
    def is_done(self) -> bool:
        return self._status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.DEAD_LETTER,
        )

    def wait_result(self, timeout: Optional[float] = None) -> Optional[TaskResult]:
        self._result_event.wait(timeout=timeout)
        return self._result

    def set_result(self, result: TaskResult) -> None:
        self._result = result
        self._status = result.status
        self._result_event.set()

    def _set_status(self, status: TaskStatus) -> None:
        self._status = status


class WorkerTaskContext:
    """Context passed to the worker's on_task callback."""

    def __init__(
        self,
        envelope: TaskEnvelope,
        msg_type: Optional[Type[TaskMessage]],
        progress_callback: Optional[Callable] = None,
        ack_callback: Optional[Callable] = None,
        nack_callback: Optional[Callable] = None,
    ):
        self._envelope = envelope
        self._msg_type = msg_type
        self._progress_callback = progress_callback
        self._ack_callback = ack_callback
        self._nack_callback = nack_callback
        self._acked = False

    @property
    def task_id(self) -> str:
        return self._envelope.task_id

    @property
    def data(self) -> Any:
        if self._msg_type is not None:
            return self._msg_type.Task(**self._envelope.task_data)
        return self._envelope.task_data

    @property
    def retry_count(self) -> int:
        return self._envelope.retry_count

    @property
    def priority(self) -> int:
        return self._envelope.priority

    def send_progress(self, progress_data: Any, percent: float = 0.0) -> None:
        if self._progress_callback is None:
            return
        if isinstance(progress_data, TaskMessage.Progress):
            pdata = progress_data.model_dump()
        elif isinstance(progress_data, dict):
            pdata = progress_data
        else:
            pdata = {"value": progress_data}
        progress = TaskProgress(
            task_id=self._envelope.task_id,
            progress_data=pdata,
            percent=percent,
        )
        self._progress_callback(progress)

    def ack(self) -> None:
        if self._ack_callback is not None and not self._acked:
            self._ack_callback(self._envelope.task_id)
            self._acked = True

    def nack(self) -> None:
        if self._nack_callback is not None:
            self._nack_callback(self._envelope.task_id)


class BaseTaskProducer(BaseEndpoint):
    @classmethod
    def logger(cls) -> logging.Logger:
        global task_queue_logger
        if task_queue_logger is None:
            task_queue_logger = logging.getLogger(__name__)
        return task_queue_logger

    def __init__(
        self,
        *args,
        queue_name: str,
        msg_type: Optional[Type[TaskMessage]] = None,
        config: Optional[TaskQueueConfig] = None,
        on_result: Optional[Callable] = None,
        on_progress: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._queue_name = queue_name
        self._msg_type = msg_type
        self._config = config or TaskQueueConfig(queue_name=queue_name)
        self._on_result = on_result
        self._on_progress = on_progress
        self._pending_tasks: Dict[str, TaskHandle] = {}
        self._lock = threading.Lock()

    @property
    def queue_name(self) -> str:
        return self._queue_name

    def submit(
        self,
        task_msg: Any,
        priority: int = 0,
        ttl: Optional[float] = None,
        fire_and_forget: bool = False,
    ) -> TaskHandle:
        if isinstance(task_msg, TaskMessage.Task):
            task_data = task_msg.model_dump()
        elif isinstance(task_msg, dict):
            task_data = task_msg
        else:
            task_data = {"value": task_msg}

        envelope = TaskEnvelope(
            queue_name=self._queue_name,
            priority=priority,
            status=TaskStatus.PENDING,
            max_retries=self._config.max_retries,
            ttl=ttl or self._config.task_ttl,
            task_data=task_data,
        )

        handle = TaskHandle(envelope.task_id, self._msg_type)

        if not fire_and_forget:
            with self._lock:
                self._pending_tasks[envelope.task_id] = handle

        self._send_task(envelope)
        return handle

    def _send_task(self, envelope: TaskEnvelope) -> None:
        raise NotImplementedError()

    def _handle_result(self, result: TaskResult) -> None:
        with self._lock:
            handle = self._pending_tasks.pop(result.task_id, None)

        if handle is not None:
            handle.set_result(result)

        if self._on_result is not None:
            if self._msg_type is not None:
                typed_result = self._msg_type.Result(**result.result_data)
                self._on_result(result.task_id, typed_result)
            else:
                self._on_result(result.task_id, result.result_data)

    def _handle_progress(self, progress: TaskProgress) -> None:
        if self._on_progress is not None:
            if self._msg_type is not None:
                typed_progress = self._msg_type.Progress(**progress.progress_data)
                self._on_progress(progress.task_id, typed_progress, progress.percent)
            else:
                self._on_progress(
                    progress.task_id, progress.progress_data, progress.percent
                )

    def _send_to_dlq(self, envelope: TaskEnvelope, error: str) -> None:
        envelope.status = TaskStatus.DEAD_LETTER
        self.log.warning(
            "Task %s sent to DLQ '%s': %s",
            envelope.task_id,
            self._config.get_dlq_name(),
            error,
        )


class BaseTaskWorker(BaseEndpoint):
    @classmethod
    def logger(cls) -> logging.Logger:
        global task_queue_logger
        if task_queue_logger is None:
            task_queue_logger = logging.getLogger(__name__)
        return task_queue_logger

    def __init__(
        self,
        *args,
        queue_name: str,
        msg_type: Optional[Type[TaskMessage]] = None,
        config: Optional[TaskQueueConfig] = None,
        on_task: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if on_task is None:
            raise ValueError("on_task callback is required")
        self._queue_name = queue_name
        self._msg_type = msg_type
        self._config = config or TaskQueueConfig(queue_name=queue_name)
        self._on_task = on_task
        self._stop_event = threading.Event()
        self._active_tasks: Dict[str, TaskEnvelope] = {}
        self._active_lock = threading.Lock()
        self._semaphore = threading.Semaphore(self._config.max_concurrent)

    @property
    def queue_name(self) -> str:
        return self._queue_name

    def _process_task(self, envelope: TaskEnvelope) -> None:
        self._semaphore.acquire()
        try:
            with self._active_lock:
                self._active_tasks[envelope.task_id] = envelope

            envelope.status = TaskStatus.PROCESSING

            ctx = WorkerTaskContext(
                envelope=envelope,
                msg_type=self._msg_type,
                progress_callback=self._publish_progress,
                ack_callback=self._ack_task,
                nack_callback=self._nack_task,
            )

            try:
                result_data = self._on_task(ctx)

                if self._config.ack_policy == AckPolicy.AUTO:
                    ctx.ack()

                if result_data is None:
                    result_dict: Dict[str, Any] = {}
                elif isinstance(result_data, TaskMessage.Result):
                    result_dict = result_data.model_dump()
                elif isinstance(result_data, dict):
                    result_dict = result_data
                else:
                    result_dict = {"value": result_data}

                task_result = TaskResult(
                    task_id=envelope.task_id,
                    status=TaskStatus.COMPLETED,
                    result_data=result_dict,
                )
                self._publish_result(task_result)

            except Exception as exc:
                self.log.error(
                    "Task %s failed (attempt %d/%d): %s",
                    envelope.task_id,
                    envelope.retry_count + 1,
                    envelope.max_retries,
                    exc,
                )

                if envelope.retry_count < envelope.max_retries - 1:
                    envelope.retry_count += 1
                    envelope.status = TaskStatus.RETRYING
                    delay = self._config.retry_delay * (
                        self._config.retry_backoff_multiplier**envelope.retry_count
                    )
                    threading.Timer(delay, self._process_task, args=[envelope]).start()
                else:
                    task_result = TaskResult(
                        task_id=envelope.task_id,
                        status=TaskStatus.FAILED,
                        error=str(exc),
                    )
                    self._publish_result(task_result)
                    self._send_to_dlq(envelope, str(exc))
        finally:
            with self._active_lock:
                self._active_tasks.pop(envelope.task_id, None)
            self._semaphore.release()

    def _publish_result(self, result: TaskResult) -> None:
        raise NotImplementedError()

    def _publish_progress(self, progress: TaskProgress) -> None:
        raise NotImplementedError()

    def _send_to_dlq(self, envelope: TaskEnvelope, error: str) -> None:
        envelope.status = TaskStatus.DEAD_LETTER
        self.log.warning(
            "Task %s sent to DLQ '%s': %s",
            envelope.task_id,
            self._config.get_dlq_name(),
            error,
        )

    def _ack_task(self, task_id: str) -> None:
        self.log.debug("Task %s acknowledged", task_id)

    def _nack_task(self, task_id: str) -> None:
        self.log.debug("Task %s negatively acknowledged", task_id)
