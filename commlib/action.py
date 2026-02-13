"""Action service and client implementations.

Provides goal-based action client and service classes for handling asynchronous
goal execution with feedback and result reporting.
"""

import concurrent.futures.thread
import logging
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from enum import IntEnum
from functools import partial
from typing import Any, Dict, Optional, Callable, Type

from commlib.compression import CompressionType
from commlib.connection import BaseConnectionParameters
from commlib.msg import ActionMessage, PubSubMessage, RPCMessage
from commlib.utils import gen_random_id, gen_timestamp

actions_logger = None


class GoalStatus(IntEnum):
    """GoalStatus.
    Enumeration of possible goal statuses for an action.

    ACCEPTED: The goal has been accepted and is waiting to be executed.
    EXECUTING: The goal is currently being executed.
    CANCELING: The goal is in the process of being canceled.
    SUCCEEDED: The goal has been successfully executed.
    ABORTED: The goal has been aborted due to an error or failure.
    CANCELED: The goal has been canceled.
    """

    ACCEPTED = 1
    RUNNING = 2
    CANCELING = 3
    SUCCEDED = 4
    ABORTED = 5
    CANCELED = 6


class _ActionGoalMessage(RPCMessage):
    """_ActionGoalMessage.
    Internal Action Goal (RPC) Message
    """

    class Request(RPCMessage.Request):
        """Request payload."""

        description: str = ""
        goal_data: Dict[str, Any] = {}

    class Response(RPCMessage.Response):
        """Response payload."""

        status: int = 0
        timestamp: int = -1
        goal_id: str = ""
        error: str = ""

        def __post_init__(self):
            self.timestamp = int(time.time())


class _ActionResultMessage(RPCMessage):
    """_ActionResultMessage.
    Internal Action Result (RPC) Message
    """

    class Request(RPCMessage.Request):
        """Request payload."""

        goal_id: Optional[str] = ""

    class Response(RPCMessage.Response):
        """Response payload."""

        status: int = 0
        timestamp: int = -1
        result: Dict[str, Any] = {}
        error: str = ""

        def __post_init__(self):
            self.timestamp = int(time.time())


class _ActionCancelMessage(RPCMessage):
    """_ActionCancelMessage.
    Internal Action Cancel (RPC) Message
    """

    class Request(RPCMessage.Request):
        """Request payload."""

        goal_id: Optional[str] = ""
        timestamp: int = gen_timestamp()

    class Response(RPCMessage.Response):
        """Response payload."""

        status: int = 0
        timestamp: int = gen_timestamp()
        result: Dict[str, Any] = {}
        error: str = ""


class _ActionStatusMessage(PubSubMessage):
    """_ActionStatusMessage.
    Internal Action Status Message.
    """

    goal_id: Optional[str] = ""
    status: int = 0


class _ActionFeedbackMessage(PubSubMessage):
    """_ActionFeedbackMessage.
    Internal Action Feedback Message
    """

    feedback_data: Optional[Dict[str, Any]] = {}
    goal_id: Optional[str] = ""


class _ActionNotifyMessage(PubSubMessage):
    """_ActionStatusMessage.
    Internal Action Status Message.
    """

    msg: Optional[str] = ""
    status: Optional[int] = 0
    goal_id: Optional[str] = ""
    goal_data: Optional[Dict[str, Any]] = {}
    goal_description: Optional[str] = ""


class GoalHandler:
    """Goal Handler."""

    @classmethod
    def logger(cls) -> logging.Logger:
        """Logger."""
        global actions_logger  # pylint: disable=global-statement
        if actions_logger is None:
            actions_logger = logging.getLogger(__name__)
        return actions_logger

    def __init__(
        self,
        msg_type: Optional[Type[ActionMessage]],
        status_publisher: Any,
        feedback_publisher: Any,
        on_goal: Callable,
        on_cancel: Optional[Callable],
    ):
        """__init__.
        Initializes a GoalHandler instance with the provided parameters.

        Args:
            msg_type (ActionMessage): The type of action message.
            status_publisher (callable): A callable to publish the status of the goal.
            feedback_publisher (callable): A callable to publish feedback for the goal.
            on_goal (callable): A callable to be executed when the goal is started.
            on_cancel (callable): A callable to be executed when the goal is canceled.

        The GoalHandler manages the execution of an action goal.
        It sets initial status, generates a unique ID, stores the
        provided data/publishers/callables, and creates a
        ThreadPoolExecutor with max 2 workers.
        """

        self._msg_type = msg_type
        self.status: Optional[GoalStatus] = None
        self.id = gen_random_id()
        self.data: Any = (
            msg_type.Result() if isinstance(msg_type, ActionMessage) else {}
        )
        self._pub_status = status_publisher
        self._pub_feedback = feedback_publisher
        self.result: Any = (
            msg_type.Result() if isinstance(msg_type, ActionMessage) else {}
        )
        self._task: Any = None
        self._goal_task: Any = None
        self._on_goal = on_goal
        self._on_cancel = on_cancel
        self._cancel_event = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=2)
        self.set_status(GoalStatus.ACCEPTED)

    @property
    def log(self):
        """Log."""
        return self.logger()

    @property
    def cancel_event(self):
        """Cancel event."""
        return self._cancel_event

    def _done_callback(self, future: Future):
        """_done_callback.
        Callback called when the goal has reached a final state
        (succeded/cancel/aborted).

        Args:
            future:
        """
        if future.cancelled() or self._cancel_event.is_set():
            self.set_status(GoalStatus.CANCELED)
        elif future.done():
            self.set_status(GoalStatus.SUCCEDED)
        else:
            self.log.warning("Unknown future state for goal %s", self.id)
        res = future.result()
        self.result = res

    def is_finished(self):
        """is_finished.
        Check wheather the current goal has reached a final state.
        """
        if self.status in (
            GoalStatus.SUCCEDED,
            GoalStatus.CANCELED,
            GoalStatus.ABORTED,
        ):
            return True
        return False

    def start(self):
        """
        Starts the execution of the goal handler.

        This method submits the `_on_goal` callback to the thread pool executor,
        which will execute the goal handler. It also adds a `_done_callback` to
        the submitted task, which will be called when the goal has reached a
        final state (succeeded, canceled, or aborted).
        """

        self._goal_task = self._executor.submit(partial(self._on_goal, self))
        # self._cancel_task = self._executor.submit(self._on_cancel, self)
        self._goal_task.add_done_callback(self._done_callback)
        self.set_status(GoalStatus.RUNNING)

    def cancel(self):
        """
        Cancels the current goal if it is in a state that allows cancellation.

        This method sets the goal status to `GoalStatus.CANCELING`, cancels the
        `_goal_task` that is executing the goal handler, and sets the `_cancel_event`
        to signal that the goal has been canceled. It then waits for the goal task to
        complete and clears the thread pool executor's internal state.

        If the goal is already in a final state (aborted, canceled, succeeded), this
        method simply returns 0 without performing any action.

        Returns:
            int: 1 if the goal was successfully canceled, 0 otherwise.
        """

        if self.status in (
            GoalStatus.ABORTED,
            GoalStatus.CANCELED,
            GoalStatus.CANCELING,
            GoalStatus.SUCCEDED,
        ):
            return 0
        try:
            self.set_status(GoalStatus.CANCELING)
            self._goal_task.cancel()
            self._cancel_event.set()
            _ = self._goal_task.result()
            # self._executor.shutdown(wait=False)
            self._executor._threads.clear()  # type: ignore  # pylint: disable=protected-access
            concurrent.futures.thread._threads_queues.clear()  # type: ignore  # pylint: disable=protected-access
        except (RuntimeError, concurrent.futures.TimeoutError) as exc:
            self.log.error("Error canceling goal: %s", exc)
            return 0
        return 1

    def set_status(self, status: GoalStatus):
        """
        Sets the status of the goal and publishes a status message.

        Args:
            status (GoalStatus): The new status of the goal.

        Raises:
            ValueError: If the provided status is not a valid GoalStatus.

        Returns:
            None
        """

        if status not in GoalStatus:
            raise ValueError("Wrong status code!")
        self.status = status
        msg = _ActionStatusMessage(status=status, goal_id=self.id)
        assert self._pub_status is not None
        if self._pub_status is not None:
            self._pub_status.publish(msg)

    def send_feedback(self, feedback_msg: _ActionFeedbackMessage):
        """
        Publishes a feedback message for the current goal.

        Args:
            feedback_msg (_ActionFeedbackMessage): The feedback message to publish.

        Returns:
            None
        """

        _fb = feedback_msg.feedback_data
        msg = _ActionFeedbackMessage(  # type: ignore[reportArgumentType]
            feedback_data=_fb, goal_id=self.id
        )
        assert self._pub_feedback is not None
        if self._pub_feedback is not None:
            self._pub_feedback.publish(msg)

    def set_result(self, result):
        """Set result."""
        self.result = result


class BaseActionService:
    """
    Base class for implementing action services.

    Provides the core functionality for managing action-based communication,
    including goal handling, status tracking, feedback publishing, and
    result reporting.
    """

    _LOOP_INTERVAL = 0.001

    @classmethod
    def logger(cls) -> logging.Logger:
        """Logger."""
        global actions_logger  # pylint: disable=global-statement
        if actions_logger is None:
            actions_logger = logging.getLogger(__name__)
        return actions_logger

    def __init__(
        self,
        action_name: str,
        msg_type: Optional[Type[ActionMessage]] = None,
        debug: bool = True,
        compression: int = CompressionType.NO_COMPRESSION,
        conn_params: Optional[BaseConnectionParameters] = None,
        on_goal: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        on_getresult: Optional[Callable] = None,
    ):
        """__init__.
        Initializes a BaseActionService instance.

        Args:
            action_name (str): The name of the action.
            msg_type (ActionMessage, optional): The type of action message to use.
            debug (bool, optional): Whether to enable debug mode. Defaults to True.
            compression (CompressionType, optional): Compression type.
                Defaults to NO_COMPRESSION.
            conn_params (BaseConnectionParameters, optional): The connection parameters to use.
            on_goal (callable, optional): A callback function to be called when a goal is received.
            on_cancel (callable, optional): Callback for
                when a goal is canceled.
            on_getresult (callable, optional): Callback for
                when a result is requested.
        """
        if on_goal is None:
            raise ValueError("No on_goal callback provided")
        self._msg_type = msg_type
        self._debug = debug
        self._compression = compression
        self._action_name = action_name
        self._on_goal = on_goal
        self._on_cancel = on_cancel
        self._on_getresult = on_getresult
        self._conn_params = conn_params

        self._notify_topic = f"{self._action_name}.notify"
        self._status_topic = f"{self._action_name}.status"
        self._feedback_topic = f"{self._action_name}.feedback"
        self._goal_rpc_uri = f"{self._action_name}.send_goal"
        self._cancel_rpc_uri = f"{self._action_name}.cancel_goal"
        self._result_rpc_uri = f"{self._action_name}.get_result"

        # To be instantiated by the child classes
        self._mpublisher: Optional[Any] = None
        self._notify_pub: Optional[Any] = None
        self._feedback_pub: Optional[Any] = None
        self._status_pub: Optional[Any] = None
        self._goal_rpc: Optional[Any] = None
        self._cancel_rpc: Optional[Any] = None
        self._result_rpc: Optional[Any] = None
        self._current_goal: Optional[GoalHandler] = None

        self.log.info(
            "Initiating Action Service:\n"
            " - Name: %s\n"
            " - Status Topic: %s\n"
            " - Feedback Topic: %s\n"
            " - Notify Topic: %s\n"
            " - Goal RPC: %s\n"
            " - Cancel RPC: %s\n"
            " - Result RPC: %s",
            self._action_name,
            self._status_topic,
            self._feedback_topic,
            self._notify_topic,
            self._goal_rpc_uri,
            self._cancel_rpc_uri,
            self._result_rpc_uri,
        )

    @property
    def debug(self):
        """Debug."""
        return self._debug

    @property
    def log(self):
        """Log."""
        return self.logger()

    @property
    def connected(self):
        """Connected."""
        assert self._goal_rpc is not None
        assert self._cancel_rpc is not None
        assert self._result_rpc is not None
        assert self._status_pub is not None
        assert self._feedback_pub is not None
        return (
            self._goal_rpc.connected
            and self._cancel_rpc.connected
            and self._result_rpc.connected
            and self._status_pub.connected
            and self._feedback_pub.connected
        )

    def run(self):
        """
        Start the Action Service RPC handlers.

        This method starts the RPC handlers for sending goals, canceling goals,
        and getting results. It ensures that the Action Service is properly
        running and ready to handle requests.
        """

        if self._goal_rpc is not None:
            self._goal_rpc.run()
        if self._cancel_rpc is not None:
            self._cancel_rpc.run()
        if self._result_rpc is not None:
            self._result_rpc.run()
        if self._mpublisher is not None:
            self._mpublisher.run()
        else:
            if self._status_pub is not None:
                self._status_pub.run()
            if self._feedback_pub is not None:
                self._feedback_pub.run()

    def stop(self):
        """
        Stop the Action Service.

        This method stops the RPC handlers for sending goals, canceling goals,
        and getting results. It ensures that the Action Service is properly
        shut down and releases any resources it was using.
        """

        if self._goal_rpc is not None:
            self._goal_rpc.stop()
        if self._cancel_rpc is not None:
            self._cancel_rpc.stop()
        if self._result_rpc is not None:
            self._result_rpc.stop()
        if self._mpublisher is not None:
            self._mpublisher.stop()
        else:
            if self._status_pub is not None:
                self._status_pub.stop()
            if self._feedback_pub is not None:
                self._feedback_pub.stop()

    def _handle_send_goal(self, msg: _ActionGoalMessage.Request):
        """_handle_send_goal.

        Args:
            msg (_ActionGoalMessage.Request): Set Goal Request Message
        """
        self._notify(
            msg="Set Goal Request", data=msg.goal_data, description=msg.description
        )
        resp = _ActionGoalMessage.Response()

        if self._current_goal is None or self._current_goal.status in (
            GoalStatus.SUCCEDED,
            GoalStatus.CANCELED,
            GoalStatus.ABORTED,
        ):
            self._current_goal = GoalHandler(
                self._msg_type,
                self._status_pub,
                self._feedback_pub,
                self._on_goal,
                self._on_cancel,
            )
            if self._msg_type is not None:
                self._current_goal.data = self._msg_type.Goal(**msg.goal_data)
            else:
                self._current_goal.data = msg.goal_data
        elif self._current_goal.status == GoalStatus.ACCEPTED:
            pass
        else:
            resp.error = (
                f"Cannot make the transition - Goal {self._current_goal.id} is running!"
            )
            return resp
        assert self._current_goal is not None
        self._current_goal.start()
        resp.status = 1
        resp.goal_id = self._current_goal.id
        self._notify(
            msg="Goal Started",
            goal_id=self._current_goal.id,
            data=msg.goal_data,
            description=msg.description,
        )
        return resp

    def _handle_cancel_goal(self, msg: _ActionCancelMessage.Request):
        """_handle_cancel_goal.

        Args:
            msg (_ActionCancelMessage.Request): Cancel Request Message
        """
        resp = _ActionCancelMessage.Response()
        _goal_id = msg.goal_id
        if self._current_goal is None:
            return resp
        if self._current_goal.id != _goal_id:
            return resp
        _status = self._current_goal.cancel()
        resp.status = _status
        self._notify(msg="Goal Cancelled", goal_id=_goal_id, status=_status)
        return resp

    def _handle_get_result(self, msg: _ActionResultMessage.Request):
        """_handle_get_result.

        Args:
            msg (_ActionResultMessage.Request): Result Request Message
        """
        resp = _ActionResultMessage.Response()
        _goal_id = msg.goal_id
        if _goal_id == "":
            pass
        elif self._current_goal is None:
            return resp
        elif self._current_goal.id != _goal_id:
            return resp
        assert self._current_goal is not None
        resp.status = (
            int(self._current_goal.status)
            if self._current_goal.status is not None
            else 0
        )
        # Set Result data
        if self._msg_type is not None:
            assert self._current_goal.result is not None
            resp.result = (  # type: ignore[reportAttributeAccessIssue]
                self._current_goal.result.model_dump()
            )
        else:
            resp.result = self._current_goal.result  # type: ignore[reportAttributeAccessIssue]
        return resp

    def _notify(
        self,
        msg: str = "",
        description: str = "",
        goal_id: Optional[str] = "",
        status: int = 0,
        data: Optional[Dict[str, Any]] = None,
    ):
        if data is None:
            data = {}
        if self._notify_pub is not None:
            _msg = _ActionNotifyMessage(
                msg=msg,
                goal_description=description,
                status=status,
                goal_data=data,
                goal_id=goal_id,
            )
            self._notify_pub.publish(_msg)

    def __del__(self):
        self.stop()


class BaseActionClient:
    """
    Base class for Action Clients.

    This class provides the basic functionality for an Action Client, including
    sending goals, canceling goals, and receiving feedback and results from
    an Action Service.
    """

    _LOOP_INTERVAL = 0.001

    @classmethod
    def logger(cls) -> logging.Logger:
        """Logger."""
        global actions_logger  # pylint: disable=global-statement
        if actions_logger is None:
            actions_logger = logging.getLogger(__name__)
        return actions_logger

    def __init__(
        self,
        action_name: str,
        msg_type: Optional[Type[ActionMessage]] = None,
        debug: bool = False,
        compression: int = CompressionType.NO_COMPRESSION,
        conn_params: Optional[BaseConnectionParameters] = None,
        on_feedback: Optional[Callable] = None,
        on_result: Optional[Callable] = None,
        on_goal_reached: Optional[Callable] = None,
    ):
        """
        Initializes an instance of the `BaseActionClient` class.

        Args:
            action_name (str): The name of the action.
            msg_type (ActionMessage, optional): The type of the action message.
            debug (bool, optional): Whether to enable debug mode.
            compression (CompressionType, optional): The type of compression to use.
            conn_params (BaseConnectionParameters, optional): The connection parameters.
            on_feedback (callable, optional): A callback function for handling feedback.
            on_result (callable, optional): A callback function for handling results.
            on_goal_reached (callable, optional): Callback
                for handling when a goal is reached.
        """

        self._debug = debug
        self._action_name = action_name
        self._msg_type = msg_type
        self._compression = compression
        self._conn_params = conn_params

        self._status_topic = f"{self._action_name}.status"
        self._feedback_topic = f"{self._action_name}.feedback"
        self._goal_rpc_uri = f"{self._action_name}.send_goal"
        self._cancel_rpc_uri = f"{self._action_name}.cancel_goal"
        self._result_rpc_uri = f"{self._action_name}.get_result"

        # To be instantiated by the child classes
        self._goal_client: Optional[Any] = None
        self._cancel_client: Optional[Any] = None
        self._result_client: Optional[Any] = None
        self._status_sub: Optional[Any] = None
        self._feedback_sub: Optional[Any] = None
        self._goal_id = None
        self._result = None
        self._status = _ActionStatusMessage()

        self.on_feedback = on_feedback
        self.on_result = on_result
        self.on_goal_reached = on_goal_reached

    @property
    def debug(self) -> bool:
        """Debug."""
        return self._debug

    @property
    def log(self):
        """Log."""
        return self.logger()

    @property
    def result(self):
        """Result."""
        return self._result

    @property
    def status(self):
        """Status."""
        return self._status

    @property
    def goal_id(self):
        """Goal id."""
        return self._goal_id

    @property
    def connected(self):
        """Connected."""
        assert self._status_sub is not None
        assert self._feedback_sub is not None
        assert self._goal_client is not None
        assert self._cancel_client is not None
        assert self._result_client is not None
        return (
            self._status_sub.connected
            and self._feedback_sub.connected
            and self._goal_client.connected
            and self._cancel_client.connected
            and self._result_client.connected
        )

    def send_goal(
        self,
        goal_msg: ActionMessage.Goal,
        timeout: int = 10,
        _wait_for_result: bool = False,
    ) -> _ActionGoalMessage.Response:
        """send_goal.
        Send a new goal to the Action service.

        Args:
            goal_msg (ActionMessage.Goal): The Action Goal Message
            timeout (int): timeout
            wait_for_result (bool): Weather to wait for result or not.

        Returns:
            _ActionGoalMessage.Response:
        """
        _data = {}
        if isinstance(goal_msg, dict) or isinstance(goal_msg, Dict):
            _data = goal_msg
        elif isinstance(goal_msg, ActionMessage.Goal):
            _data = goal_msg.model_dump()
        req = _ActionGoalMessage.Request(goal_data=_data)
        assert self._goal_client is not None
        self._status = _ActionStatusMessage()
        resp = self._goal_client.call(req, timeout=timeout)
        self._result = None  # Reset result
        self._goal_id = resp.goal_id
        return resp

    def cancel_goal(
        self, timeout: float = 10.0, _wait_for_result: bool = False
    ) -> _ActionCancelMessage.Response:
        """cancel_goal.
        Cancel the current goal.

        Args:
            timeout (float): timeout
            wait_for_result (bool): Weather to wait for result or not.

        Returns:
            _ActionCancelMessage.Response:
        """
        assert self._goal_id is not None
        req = _ActionCancelMessage.Request(goal_id=self._goal_id)
        assert self._cancel_client is not None
        resp = self._cancel_client.call(req, timeout=timeout)
        # TODO Check response status
        # res = self.get_result(wait=wait_for_result)
        # return res
        return resp

    def get_result(
        self, timeout: float = 10.0, _wait: bool = False, _wait_max_sec: float = 30.0
    ) -> ActionMessage.Result:
        """get_result.
        Returns the result of the goal.

        Args:
            timeout (float): timeout
            wait (bool): Wait for the goal to finish if result does not exist.
            wait_max_sec (float): Maximum time to wait for result if `wait`
                is set to True.

        Returns:
            ActionMessage.Result:
        """
        assert self._goal_id is not None
        req = _ActionResultMessage.Request(goal_id=self._goal_id)
        assert self._result_client is not None
        resp = self._result_client.call(req, timeout=timeout)
        if self._msg_type is None:
            res = resp.result
        else:
            res = self._msg_type.Result(**resp.result)
        return res

    def _on_status(self, msg: _ActionStatusMessage) -> None:
        """_on_status.
        Internal on_status event callback.

        Args:
            msg (_ActionStatusMessage): Action status message (Internal use)

        Returns:
            None:
        """
        self.log.debug("ActionClient <on-status> callback: %s", msg)
        # Check if the goal_id matches the one of the current goal.
        if msg.goal_id != self._goal_id:
            return
        self._status = msg
        # If it reaches a final state F
        if self._status.status in (
            GoalStatus.SUCCEDED,
            GoalStatus.CANCELED,
            GoalStatus.ABORTED,
        ):
            resp = self._call_get_result()  # type: ignore[attr-defined]
            self._result = resp

            # Call the on_goal_reached callback
            if (
                self._status.status == GoalStatus.SUCCEDED
                and self.on_goal_reached is not None
            ):
                self.on_goal_reached(resp)

            # If the on_result callback was declared
            if self.on_result is not None:
                self.on_result(resp)

    def _on_feedback(self, msg: _ActionFeedbackMessage) -> None:
        """_on_feedback.
        Internal on_feedback event callback.

        Args:
            msg (_ActionFeedbackMessage): Action feedback Message
                (Internal use)

        Returns:
            None:
        """
        # Check if the goal_id matches the one of the current goal.
        if msg.goal_id != self._goal_id:
            return
        fb: Any
        if self._msg_type is not None and msg.feedback_data is not None:
            fb = self._msg_type.Feedback(**msg.feedback_data)
        else:
            fb = msg.feedback_data
        if self.on_feedback is not None:
            self.on_feedback(fb)

    def run(self):
        """
        Run the action client endpoints.

        Starts the action client endpoints: status subscriber,
        feedback subscriber, goal client, cancel client, and result
        client.
        """
        self._goal_id = None
        self._result = None
        if self._status_sub is not None:
            self._status_sub.run()
        if self._feedback_sub is not None:
            self._feedback_sub.run()
        if self._goal_client is not None:
            self._goal_client.run()
        if self._cancel_client is not None:
            self._cancel_client.run()
        if self._result_client is not None:
            self._result_client.run()

    def stop(self) -> None:
        """stop.
        Stop action client endpoints.

        Args:

        Returns:
            None:
        """
        if self._status_sub is not None:
            self._status_sub.stop()
        if self._feedback_sub is not None:
            self._feedback_sub.stop()
        if self._goal_client is not None:
            self._goal_client.stop()
        if self._cancel_client is not None:
            self._cancel_client.stop()
        if self._result_client is not None:
            self._result_client.stop()

    def __del__(self):
        self.stop()
