from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)

from concurrent.futures import ThreadPoolExecutor
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
    def __init__(self, status_publisher, feedback_publisher):
        self.status = 1
        self.id = self._gen_random_id()
        self.data = {}
        self._pub_status = status_publisher
        self._pub_feedback = feedback_publisher
        self.result = None
        self._task = None

    @property
    def task(self):
        return self._task

    @task.setter
    def task(self, val):
        ## TODO Typechecking
        self._task = val
        self._task.add_done_callback(self._done_callback)

    def _done_callback(self, future):
        if future.cancelled():
            print('Goal Cancelled')
            self.set_status(GoalStatus.CANCELED)
        elif future.done():
            print('Goal Completed')
            self.set_status(GoalStatus.SUCCEDED)
        self.result = future.result()

    def is_finished(self):
        if self.status in (GoalStatus.SUCCEDED,
                           GoalStatus.CANCELED,
                           GoalStatus.ABORTED):
            return True
        else:
            return False

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
                 workers=4, on_goal=None, on_cancel=None, on_getresult=None):
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

    def _handle_send_goal(self, msg, meta):
        self.logger.info('Goal Received!')
        if self._current_goal is None:
            self._current_goal = GoalHandler(self._status_pub,
                                             self._feedback_pub)
        if self._current_goal.status in (GoalStatus.SUCCEDED,
                                         GoalStatus.CANCELED,
                                         GoalStatus.ABORTED):
            # Final States - Completed Goal Task
            self._current_goal = GoalHandler(self._status_pub,
                                             self._feedback_pub)
            self._current_goal.data = msg
        if self._on_goal is not None:
            resp = {
                'status': self._current_goal.status,
                'goal_id': self._current_goal.id
            }
            self._current_goal.task = _goal_task
            _goal_task = self._executor.submit(
                self._on_goal, self._current_goal)
            self._current_goal.set_status(GoalStatus.EXECUTING)
        else:
            resp = {
                'status': GoalStatus.ABORTED,
                'goal_id': self._current_goal.id
            }
        return resp

    def _handle_cancel_goal(self, msg, meta):
        raise NotImplementedError()

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
        resp['status'] = self._current_goal.status
        if self._current_goal.result is not None:
            resp['result'] = self._current_goal.result
        return resp

    # def run(self):
    #     self._main_thread = threading.Thread(target=self.run_forever)
    #     self._main_thread.daemon = True
    #     self._t_stop_event = threading.Event()
    #     self._main_thread.start()

    # def stop(self):
    #     if self._t_stop_event is not None:
    #         self._t_stop_event.set()

    def run(self):
        self._goal_rpc.run()
        self._cancel_rpc.run()
        self._result_rpc.run()


class BaseActionClient(object):
    def __init__(self, action_name, logger=None, debug=True, serializer=None):
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

    def get_result(self, goal_id, timeout=10):
        assert isinstance(goal_id, str)
        req = {
            'goal_id': goal_id
        }
        return self._goal_client.call(req, timeout=timeout)
