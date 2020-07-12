from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

from concurrent.futures import ThreadPoolExecutor
import concurrent.futures.thread
import threading
import time
import uuid
from enum import IntEnum
import datetime

from .serializer import JSONSerializer, Serializer
from .msg import BaseMessage
from .logger import Logger


class GoalStatus(IntEnum):
    ACCEPTED = 1
    EXECUTING = 2
    CANCELING = 3
    SUCCEDED = 4
    ABORTED = 5
    CANCELED = 6


class GoalHandler(object):
    def __init__(self, status_publisher, feedback_publisher, on_goal=None,
                 on_cancel=None):
        self.status = 1
        self.id = self._gen_random_id()
        self.data = {}
        self._pub_status = status_publisher
        self._pub_feedback = feedback_publisher
        self.result = None
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
            print('Goal Cancelled')
            self.set_status(GoalStatus.CANCELED)
        elif future.done():
            print('Goal Completed')
            self.set_status(GoalStatus.SUCCEDED)
        else:
            print('Whaaaaaat?..')
        self.result = future.result()

    def is_finished(self):
        if self.status in (GoalStatus.SUCCEDED,
                           GoalStatus.CANCELED,
                           GoalStatus.ABORTED):
            return True
        else:
            return False

    def start(self):
        self._goal_task = self._executor.submit(self._on_goal, self)
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
            self.cancel_event.set()
            # self._executor.shutdown(wait=False)
            self._executor._threads.clear()
            concurrent.futures.thread._threads_queues.clear()
        except Exception as exc:
            return 0
        return 1

    def set_status(self, status):
        if status not in GoalStatus:
            raise ValueError()
        status = int(status)
        self.status = status
        pmsg = {
            'goal_id': self.id,
            'status': status
        }
        self._pub_status.publish(pmsg)

    def send_feedback(self, feedback_msg):
        assert isinstance(feedback_msg, dict)
        self._pub_feedback.publish(feedback_msg)

    def set_result(self, result):
        assert isinstance(result, dict)
        self.result = result

    def _gen_random_id(self):
        """Generate correlationID."""
        return str(uuid.uuid4()).replace('-', '')

    def to_dict(self):
        return {
            'status': self.status,
            'goal_id': self.id,
            'data': self.data,
            'result': self.result
        }


class BaseActionServer(object):
    def __init__(self, action_name, logger=None, debug=True,
                 workers=4, on_goal=None, on_cancel=None,
                 on_getresult=None):
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

    def _gen_random_id(self):
        """Generate correlationID."""
        return str(uuid.uuid4()).replace('-', '')

    def _handle_send_goal(self, msg, meta):
        self.logger.info('Goal Received!')
        if self._current_goal is None:
            self._current_goal = GoalHandler(self._status_pub,
                                             self._feedback_pub,
                                             self._on_goal,
                                             self._on_cancel)
            self._current_goal.data = msg
        elif self._current_goal.status in (GoalStatus.SUCCEDED,
                                           GoalStatus.CANCELED,
                                           GoalStatus.ABORTED):
            # Final States - Completed Goal Task
            self._current_goal = GoalHandler(self._status_pub,
                                             self._feedback_pub,
                                             self._on_goal,
                                             self._on_cancel)
            self._current_goal.data = msg
        elif self._current_goal.status == GoalStatus.ACCEPTED:
            pass
        else:
            resp = {
                'status': 0,
                'goal_id': ''
            }
            return resp
        if self._on_goal is not None:
            resp = {
                'status': 1,
                'goal_id': self._current_goal.id
            }
            self._current_goal.start()
        else:
            resp = {
                'status': 0,
                'goal_id': self._current_goal.id
            }
        return resp

    def _handle_cancel_goal(self, msg, meta):
        resp = {
            'status': 0,
            'result': {}
        }
        if 'goal_id' not in msg:
            resp['result'] = {'error': 'Missing goal_id parameter'}
            return resp
        _goal_id = msg['goal_id']
        if self._current_goal is None:
            resp['result'] = {
                'error': 'Goal <{}> does not exist'.format(_goal_id)
            }
            return resp
        if self._current_goal.id != _goal_id:
            resp['result'] = {
                'error': 'Goal <{}> does not exist'.format(_goal_id)
            }
            return resp
        _status =  self._current_goal.cancel()
        resp['status'] = _status
        return resp

    def _handle_get_result(self, msg, meta):
        resp = {
            'status': 0,
            'result': {}
        }
        if 'goal_id' not in msg:
            resp['result'] = {'error': 'Missing goal_id parameter'}
            return resp
        _goal_id = msg['goal_id']
        if self._current_goal is None:
            resp['result'] = {
                'error': 'Goal <{}> does not exist'.format(_goal_id)
            }
            return resp
        if self._current_goal.id != _goal_id:
            resp['result'] = {
                'error': 'Goal <{}> does not exist'.format(_goal_id)
            }
            return resp
        resp['status'] = self._current_goal.status
        if self._current_goal.result is not None:
            resp['result'] = self._current_goal.result
        return resp

    def run(self):
        self._goal_rpc.run()
        self._cancel_rpc.run()
        self._result_rpc.run()


class BaseActionClient(object):
    def __init__(self, action_name, logger=None, debug=True, serializer=None,
                 on_feedback=None):
        self._debug = debug
        self._action_name = action_name

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

        self._status = None
        self._on_feedback_ext = on_feedback

        self._logger = Logger(self.__class__.__name__) if \
            logger is None else logger

        assert isinstance(self._logger, Logger)
        self._executor = ThreadPoolExecutor(max_workers=2)

    @property
    def debug(self):
        return self._debug

    @property
    def logger(self):
        return self._logger

    def _gen_random_id(self):
        """Generate correlationID."""
        return str(uuid.uuid4()).replace('-', '')

    def send_goal(self, goal_data, timeout=10):
        assert isinstance(goal_data, dict)
        return self._goal_client.call(goal_data, timeout=timeout)

    def cancel_goal(self, goal_id, timeout=10):
        assert isinstance(goal_id, str)
        req = {
            'goal_id': goal_id,
            'timestamp': datetime.datetime.now(
            datetime.timezone.utc).timestamp()
        }
        return self._cancel_client.call(req, timeout=timeout)

    def get_result(self, goal_id, timeout=10, wait=True):
        assert isinstance(goal_id, str)
        req = {
            'goal_id': goal_id
        }
        if wait:
            while True:
                if self._status in (GoalStatus.ABORTED,
                                    GoalStatus.SUCCEDED,
                                    GoalStatus.CANCELED):
                    break
                time.sleep(0.001)
        return self._result_client.call(req, timeout=timeout)

    def _on_status(self, msg, meta):
        self.logger.info(msg)
        self._status = msg['status']
        # self._status = 

    def _on_feedback(self, msg, meta):
        self.logger.info(msg)
