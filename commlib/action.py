from concurrent.futures import ThreadPoolExecutor
import concurrent.futures.thread
import threading
import time
import uuid
from enum import IntEnum
import datetime

from .serializer import JSONSerializer, Serializer
from .logger import Logger
from .msg import ActionMessage, RPCMessage, PubSubMessage, DataClass, DataField
from .utils import gen_random_id
from functools import partial


class GoalStatus(IntEnum):
    ACCEPTED = 1
    EXECUTING = 2
    CANCELING = 3
    SUCCEDED = 4
    ABORTED = 5
    CANCELED = 6


class GoalHandler(object):
    def __init__(self, msg_type: ActionMessage,
                 status_publisher: callable,
                 feedback_publisher: callable,
                 on_goal: callable,
                 on_cancel: callable):
        self._msg_type = msg_type
        self.status = GoalStatus.ACCEPTED
        self.id = gen_random_id()
        self.data = msg_type.Result()
        self._pub_status = status_publisher
        self._pub_feedback = feedback_publisher
        self.result = msg_type.Result()
        self._task = None
        self._on_goal = on_goal
        self._on_cancel = on_cancel
        self._cancel_event = threading.Event()

        self._executor = ThreadPoolExecutor(max_workers=2)

    @property
    def cancel_event(self):
        return self._cancel_event

    def _done_callback(self, future):
        if future.cancelled() or self._cancel_event.is_set():
            self.set_status(GoalStatus.CANCELED)
        elif future.done():
            self.set_status(GoalStatus.SUCCEDED)
        else:
            print('Whaaaaaat?..')
        res = future.result()
        assert isinstance(res, ActionMessage.Result)
        self.result = res

    def is_finished(self):
        if self.status in (GoalStatus.SUCCEDED,
                           GoalStatus.CANCELED,
                           GoalStatus.ABORTED):
            return True
        else:
            return False

    def start(self):
        self._goal_task = self._executor.submit(
            partial(self._on_goal, self, self._msg_type.Result,
                    self._msg_type.Feedback)
        )
        # self._cancel_task = self._executor.submit(self._on_cancel, self)
        self._goal_task.add_done_callback(self._done_callback)

    def cancel(self):
        if self.status in (GoalStatus.ABORTED,
                           GoalStatus.CANCELED,
                           GoalStatus.CANCELING,
                           GoalStatus.SUCCEDED):
            return 0
        try:
            self.set_status(GoalStatus.CANCELING)
            self._goal_task.cancel()
            self._cancel_event.set()
            s = self._goal_task.result()
            # self._executor.shutdown(wait=False)
            self._executor._threads.clear()
            concurrent.futures.thread._threads_queues.clear()
        except Exception as exc:
            print(exc)
            return 0
        return 1

    def set_status(self, status):
        if status not in GoalStatus:
            raise ValueError()
        status = int(status)
        self.status = status
        msg = _ActionStatusMessage(status=status, goal_id=self.id)
        self._pub_status.publish(msg)

    def send_feedback(self, feedback_msg):
        assert isinstance(feedback_msg, ActionMessage.Feedback)
        msg = _ActionFeedbackMessage(feedback_data=feedback_msg.as_dict(),
                                     goal_id=self.id)
        self._pub_feedback.publish(msg)

    def set_result(self, result):
        assert isinstance(result, dict)
        self.result = result


class _ActionGoalMessage(RPCMessage):
    @DataClass
    class Request(RPCMessage.Request):
        description: str = ''
        goal_data: dict = DataField(default_factory=dict)

    @DataClass
    class Response(RPCMessage.Response):
        status: int = 0
        timestamp: int = -1
        goal_id: str = ''


class _ActionResultMessage(RPCMessage):
    @DataClass
    class Request(RPCMessage.Request):
        goal_id: str = ''

    @DataClass
    class Response(RPCMessage.Response):
        status: int = 0
        timestamp: int = -1
        result: dict = DataField(default_factory=dict)

class _ActionCancelMessage(RPCMessage):
    @DataClass
    class Request(RPCMessage.Request):
        goal_id: str = ''
        timestamp: int = -1  ## Timestamp of when the request was made

    @DataClass
    class Response(RPCMessage.Response):
        status: int = 0
        timestamp: int = -1  ## Timestamp of when it was canceled
        result: dict = DataField(default_factory=dict)

@DataClass
class _ActionStatusMessage(PubSubMessage):
    goal_id: str = ''
    status: int = 0


@DataClass
class _ActionFeedbackMessage(PubSubMessage):
    feedback_data: dict = DataField(default_factory=dict)
    goal_id: str = ''


class BaseActionServer(object):
    def __init__(self,
                 action_name: str,
                 msg_type: ActionMessage,
                 logger: Logger = None,
                 debug: bool = True,
                 workers: int = 4,
                 on_goal: callable = None,
                 on_cancel: callable = None,
                 on_getresult: callable = None):
        self._msg_type = msg_type
        self._debug = debug
        self._num_workers = workers
        self._action_name = action_name
        self._on_goal = on_goal
        self._on_cancel = on_cancel
        self._on_getresult = on_getresult

        self._status_topic = '{}.status'.format(self._action_name)
        self._feedback_topic = '{}.feedback'.format(self._action_name)
        self._goal_rpc_uri = '{}.send_goal'.format(self._action_name)
        self._cancel_rpc_uri = '{}.cancel_goal'.format(self._action_name)
        self._result_rpc_uri = '{}.get_result'.format(self._action_name)

        ## To be instantiated by the child classes
        self._feedback_pub = None
        self._status_pub = None
        self._goal_rpc = None
        self._cancel_rpc = None
        self._result_rpc = None

        self._current_goal = None

        self._logger = Logger(self.__class__.__name__) if \
            logger is None else logger

        assert isinstance(self._logger, Logger)

    @property
    def debug(self):
        return self._debug

    @property
    def logger(self):
        return self._logger

    def run(self):
        self._goal_rpc.run()
        self._cancel_rpc.run()
        self._result_rpc.run()

    def stop(self):
        self._goal_rpc.stop()
        self._cancel_rpc.stop()
        self._result_rpc.stop()

    def _handle_send_goal(self, msg: _ActionGoalMessage.Request):
        resp = _ActionGoalMessage.Response()
        if self._current_goal is None:
            self._current_goal = GoalHandler(self._msg_type,
                                             self._status_pub,
                                             self._feedback_pub,
                                             self._on_goal,
                                             self._on_cancel)
            self._current_goal.data = self._msg_type.Goal(**msg.goal_data)
        elif self._current_goal.status in (GoalStatus.SUCCEDED,
                                           GoalStatus.CANCELED,
                                           GoalStatus.ABORTED):
            # Final States - Completed Goal Task
            self._current_goal = GoalHandler(self._msg_type,
                                             self._status_pub,
                                             self._feedback_pub,
                                             self._on_goal,
                                             self._on_cancel)
            self._current_goal.data = self._msg_type.Goal(**msg.goal_data)
        elif self._current_goal.status == GoalStatus.ACCEPTED:
            pass
        else:
            return resp
        ## Execute user-defined callback
        if self._on_goal is not None:
            resp.status = 1
            resp.goal_id = self._current_goal.id
            self._current_goal.start()
        else:
            resp.goal_id = self._current_goal.id
        return resp

    def _handle_cancel_goal(self, msg: _ActionCancelMessage.Request):
        resp = _ActionCancelMessage.Response()
        _goal_id = msg.goal_id
        if self._current_goal is None:
            return resp
        if self._current_goal.id != _goal_id:
            return resp
        _status =  self._current_goal.cancel()
        resp.status = _status
        return resp

    def _handle_get_result(self, msg: _ActionResultMessage.Request):
        resp = _ActionResultMessage.Response()
        _goal_id = msg.goal_id
        if _goal_id == '':
            return resp
        if self._current_goal is None:
            return resp
        if self._current_goal.id != _goal_id:
            return resp
        resp.status = self._current_goal.status
        if self._current_goal.result is not None:
            resp.result = self._current_goal.result.as_dict()
        return resp

    def __del__(self):
        self.stop()


class BaseActionClient(object):
    def __init__(self,
                 action_name: str,
                 msg_type: ActionMessage,
                 logger: Logger = None,
                 debug: bool = False,
                 serializer=None,
                 on_feedback: callable = None,
                 on_result: callable = None,
                 on_goal_reached: callable = None):
        self._debug = debug
        self._action_name = action_name
        self._msg_type = msg_type

        self._status_topic = '{}.status'.format(self._action_name)
        self._feedback_topic = '{}.feedback'.format(self._action_name)
        self._goal_rpc_uri = '{}.send_goal'.format(self._action_name)
        self._cancel_rpc_uri = '{}.cancel_goal'.format(self._action_name)
        self._result_rpc_uri = '{}.get_result'.format(self._action_name)

        ## To be instantiated by the child classes
        self._goal_client = None
        self._cancel_client = None
        self._result_client = None
        self._status_sub = None
        self._feedback_sub = None

        self._goal_id = None

        self._status = _ActionStatusMessage()
        self.on_feedback = on_feedback
        self.result = None
        self.on_result = on_result
        self.on_goal_reached = on_goal_reached

        self._logger = Logger(self.__class__.__name__) if \
            logger is None else logger

    @property
    def debug(self):
        return self._debug

    @property
    def logger(self):
        return self._logger

    def stop(self):
        self._status_sub.stop()
        self._feedback_sub.stop()

    def send_goal(self,
                  goal_msg: ActionMessage.Goal,
                  timeout: int = 10,
                  wait_for_result: bool = False) -> None:
        assert isinstance(goal_msg, self._msg_type.Goal)
        req = _ActionGoalMessage.Request()
        resp = self._goal_client.call(req, timeout=timeout)
        self.result = None
        self._goal_id = resp.goal_id
        self._status = _ActionStatusMessage()
        return resp

    def cancel_goal(self, timeout: float = 10.0, wait_for_result: bool = False):
        req = _ActionCancelMessage.Request(goal_id=self._goal_id)
        resp = self._cancel_client.call(req, timeout=timeout)
        res = self.get_result(wait=wait_for_result)
        return res

    def get_result(self,
                   timeout: float = 10.0,
                   wait: bool = False,
                   wait_max_sec: float = 30.0):
        if self.result is not None:
            return self.result
        req = _ActionResultMessage.Request(goal_id=self._goal_id)
        if wait:
            t_start = time.time()
            t_elapsed = 0
            while t_elapsed < wait_max_sec:
                if self._status.status in (GoalStatus.ABORTED,
                                           GoalStatus.SUCCEDED,
                                           GoalStatus.CANCELED):
                    resp = self._result_client.call(req, timeout=timeout)
                    res = self._msg_type.Result(**resp.result)
                    self.result = res
                    return res
                time.sleep(0.001)
                t_elapsed = time.time() - t_start
        return None

    def _on_status(self, msg):
        if msg.goal_id != self._goal_id:
            return
        self._status = msg
        if self._status.status in (GoalStatus.SUCCEDED,
                                   GoalStatus.CANCELED,
                                   GoalStatus.ABORTED):
            res = self.get_result(wait=True, wait_max_sec=10)
            self.result = res
            if self._status.status == GoalStatus.SUCCEDED and \
                    self.on_goal_reached is not None:
                self.on_goal_reached(res)

            if self.on_result is not None:
                self.on_result(res)

    def _on_feedback(self, msg):
        if msg.goal_id != self._goal_id:
            return
        fb = self._msg_type.Feedback(**msg.feedback_data)
        if self.on_feedback is not None:
            self.on_feedback(fb)

    def __del__(self):
        self.stop()

