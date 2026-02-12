#!/usr/bin/env python

import time
import argparse
from commlib.msg import ActionMessage
from commlib.node import Node


class ExampleAction(ActionMessage):
    class Goal(ActionMessage.Goal):
        target: int = 0

    class Result(ActionMessage.Result):
        final_pos: int = 0

    class Feedback(ActionMessage.Feedback):
        current_pos: int = 0


def main():
    parser = argparse.ArgumentParser(description="Test Action communication")
    parser.add_argument(
        "--broker",
        type=str,
        default="redis",
        choices=["redis", "amqp", "mqtt", "kafka"],
        help="Broker type",
    )
    parser.add_argument(
        "--action-name",
        type=str,
        default="test.action.example",
        help="Action name to use",
    )
    parser.add_argument(
        "--target", type=int, default=5, help="Target value for the action"
    )

    args = parser.parse_args()

    broker = args.broker

    if broker == "redis":
        from commlib.transports.redis import ConnectionParameters
    elif broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters
    elif broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    elif broker == "kafka":
        from commlib.transports.kafka import ConnectionParameters

    print(f"Connecting to {broker} broker...")

    conn_params = ConnectionParameters()

    node = Node(
        node_name="test_action_node", connection_params=conn_params, heartbeats=False
    )

    # --- Action Server Logic ---
    def on_goal(goal_h):
        target = goal_h.data.target
        print(f"Server received goal: target={target}")
        c = 0
        while c < target:
            if goal_h.cancel_event.is_set():
                print("Server: Goal cancelled")
                break
            c += 1
            print(f"Server sending feedback: current_pos={c}")
            goal_h.send_feedback(ExampleAction.Feedback(current_pos=c))
            time.sleep(0.2)

        print(f"Server sending result: final_pos={c}")
        return ExampleAction.Result(final_pos=c)

    action_server = node.create_action(
        msg_type=ExampleAction, action_name=args.action_name, on_goal=on_goal
    )

    # --- Action Client Logic ---
    feedback_received = []

    def on_feedback(msg):
        print(f"Client received feedback: current_pos={msg.current_pos}")
        feedback_received.append(msg.current_pos)

    def on_result(msg):
        print(f"Client received result callback: final_pos={msg.final_pos}")

    action_client = node.create_action_client(
        msg_type=ExampleAction,
        action_name=args.action_name,
        on_feedback=on_feedback,
        on_result=on_result,
    )

    node.run()

    # Wait for connection/initialization
    time.sleep(2)

    print(f"Sending goal: target={args.target}...")
    goal = ExampleAction.Goal(target=args.target)

    try:
        # Send goal
        action_client.send_goal(goal)
        # Wait for result
        result = action_client.get_result(wait=True, wait_max_sec=10.0)

        if result is None:
            print("FAILURE: Goal timed out or returned None.")
        else:
            print(f"Client received final result object: final_pos={result.final_pos}")

            if result.final_pos == args.target:
                print("SUCCESS: Final result matches target.")
            else:
                print(
                    f"FAILURE: Expected final_pos={args.target}, got {result.final_pos}"
                )

            if len(feedback_received) > 0:
                print(f"SUCCESS: Received {len(feedback_received)} feedback messages.")
            else:
                print("FAILURE: No feedback received.")

            # Verify feedback sequence (roughly)
            if feedback_received[-1] == args.target:
                print("SUCCESS: Last feedback matches target.")
            else:
                print(
                    f"FAILURE: Last feedback"
                    f" {feedback_received[-1]}"
                    f" does not match target {args.target}"
                )

    except Exception as e:
        print(f"FAILURE: Action execution failed: {e}")
        import traceback

        traceback.print_exc()

    node.stop()


if __name__ == "__main__":
    main()
