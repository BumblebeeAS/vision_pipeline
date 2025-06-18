# Lifecycle Manager for normal ROS 2 Lifecycle Nodes
# References:
# https://github.com/ros-navigation/navigation2/tree/main/nav2_lifecycle_manager
# https://github.com/ros2/rclpy/issues/1313#issuecomment-2307615945

from typing import Sequence

import rclpy
from lifecycle_msgs.msg import State, TransitionDescription
from lifecycle_msgs.srv import ChangeState, GetAvailableTransitions, GetState
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.client import Client
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

# NOTE: TRANSITION_DESTROY is not available
# This is required since the ChangeState service request allows arbitrary labels
lifecycle_transitions = {
    0: "TRANSITION_CREATE",
    1: "TRANSITION_CONFIGURE",
    2: "TRANSITION_CLEANUP",
    3: "TRANSITION_ACTIVATE",
    4: "TRANSITION_DEACTIVATE",
    5: "TRANSITION_UNCONFIGURED_SHUTDOWN",
    6: "TRANSITION_INACTIVE_SHUTDOWN",
    7: "TRANSITION_ACTIVE_SHUTDOWN",
    8: "TRANSITION_DESTROY",
}


class LifecycleManager(Node):
    def __init__(self):
        super().__init__("lifecycle_manager")

        self.node_names = (
            self.declare_parameter(
                "node_names", value=rclpy.Parameter.Type.STRING_ARRAY
            )
            .get_parameter_value()
            .string_array_value
        )
        self.wait_timeout_sec = (
            self.declare_parameter("wait_timeout_sec", 1.0)
            .get_parameter_value()
            .double_value
        )

        self.srv = self.create_service(ChangeState, "manage_nodes", self.manage_nodes)

        # Required to create clients in the service callback
        # without blocking the main thread
        # TODO: See if MutuallyExclusiveCallbackGroup can be used instead
        self.client_cb_group = ReentrantCallbackGroup()

    def get_client_and_check_service(
        self, service_type: type, service_name: str
    ) -> Client | None:
        client = self.create_client(
            service_type, service_name, callback_group=self.client_cb_group
        )
        if not client.wait_for_service(timeout_sec=self.wait_timeout_sec):
            self.get_logger().error(f"Service {service_name} not available")
            return None
        return client

    async def call_get_state(self, client: Client) -> State:
        req = GetState.Request()
        future = client.call_async(req)
        result: GetState.Response = await future
        return result.current_state

    async def call_get_transitions(
        self, client: Client
    ) -> Sequence[TransitionDescription]:
        req = GetAvailableTransitions.Request()
        future = client.call_async(req)
        result: GetAvailableTransitions.Response = await future
        return result.available_transitions

    async def call_change_state(self, client: Client, transition_id: int) -> bool:
        req = ChangeState.Request()
        req.transition.id = transition_id
        future = client.call_async(req)
        result: ChangeState.Response = await future
        return result.success

    async def manage_nodes(
        self, request: ChangeState.Request, response: ChangeState.Response
    ) -> ChangeState.Response:
        for node_name in self.node_names:
            self.get_logger().info(f"--- Managing {node_name} ---")

            # If a node is in the requested state, skip it
            self.get_logger().info(f"Getting current state")
            get_state_client = self.get_client_and_check_service(
                GetState, f"{node_name}/get_state"
            )
            if get_state_client is None:
                response.success = False
                return response
            state = await self.call_get_state(get_state_client)
            self.get_logger().info(f"Current state: {state.label} (id: {state.id})")
            if state.id == request.transition.id:
                self.get_logger().info(f"{node_name} already in state: {state.label}")
                continue
            self.destroy_client(get_state_client)

            # Otherwise, raise an error if the requested transition is not available
            self.get_logger().info(f"Getting available states")
            get_transitions_client = self.get_client_and_check_service(
                GetAvailableTransitions, f"{node_name}/get_available_transitions"
            )
            if get_transitions_client is None:
                response.success = False
                return response
            available_transitions = await self.call_get_transitions(
                get_transitions_client
            )
            transition_ids = [t.transition.id for t in available_transitions]
            if request.transition.id not in transition_ids:
                transition_name = lifecycle_transitions[request.transition.id]
                self.get_logger().error(
                    f"""Transition {transition_name} (id: {request.transition.id}) not available for {node_name}"""
                )
                response.success = False
                return response
            self.destroy_client(get_transitions_client)

            # Change the state of the node
            self.get_logger().info(f"Changing state")
            change_state_client = self.get_client_and_check_service(
                ChangeState, f"{node_name}/change_state"
            )
            if change_state_client is None:
                response.success = False
                return response
            is_state_changed = await self.call_change_state(
                change_state_client, request.transition.id
            )
            if not is_state_changed:
                self.get_logger().error(
                    f"Failed to change state of {node_name} to {request.transition.label}"
                )
                response.success = False
                return response
            self.destroy_client(change_state_client)

        response.success = True
        return response


def main(args=None):
    rclpy.init(args=args)
    node = LifecycleManager()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        executor.shutdown()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
