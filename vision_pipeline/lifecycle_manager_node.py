# Lifecycle Manager for normal ROS 2 Lifecycle Nodes
# References:
# https://github.com/ros-navigation/navigation2/tree/main/nav2_lifecycle_manager

import asyncio
from typing import Sequence

import rclpy
from lifecycle_msgs.msg import State, TransitionDescription
from lifecycle_msgs.srv import ChangeState, GetAvailableTransitions, GetState
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.client import Client
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from vision_pipeline.utils.lifecycle_manager import (
    call_change_state,
    call_get_state,
    call_get_transitions,
    lifecycle_transitions,
)


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
        # It seems that creating a list of clients in init does not work with rclpy.spin
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

    async def get_current_state(self, node_name: str) -> State | None:
        """Get the current state of a node using the GetState service.

        Args:
            node_name (str): Name of the node to get the state of.

        Returns:
            State | None: Current state of the node, or None if the service call fails.
        """
        self.get_logger().info(f"Getting current state")

        service_name = f"{node_name}/get_state"
        get_state_client = self.get_client_and_check_service(GetState, service_name)
        if get_state_client is None:
            self.get_logger().error(f"Client for {service_name} is not available")
            return None

        state = await call_get_state(get_state_client)

        self.destroy_client(get_state_client)
        return state

    async def get_available_transitions(
        self, node_name: str
    ) -> Sequence[TransitionDescription] | None:
        """Get the available transitions of a node using the GetAvailableTransitions service.

        Args:
            node_name (str): Name of the node to get the transitions of.

        Returns:
            Sequence[TransitionDescription] | None: List of available transitions for the node,
            or None if the service call fails.
        """
        self.get_logger().info(f"Getting available states")

        service_name = f"{node_name}/get_available_transitions"
        get_transitions_client = self.get_client_and_check_service(
            GetAvailableTransitions, service_name
        )
        if get_transitions_client is None:
            self.get_logger().error(f"Client for {service_name} is not available")
            return None

        available_transitions = await call_get_transitions(get_transitions_client)

        self.destroy_client(get_transitions_client)
        return available_transitions

    async def change_state(self, node_name: str, transition_id: int) -> bool:
        """Change the state of a node using the ChangeState service.

        Args:
            node_name (str): Name of the node to change the state of.
            transition_id (int): ID of the transition to change to.

        Returns:
            bool: True if the state was changed successfully, False otherwise.
        """
        self.get_logger().info(f"Changing state")

        service_name = f"{node_name}/change_state"
        change_state_client = self.get_client_and_check_service(
            ChangeState, service_name
        )
        if change_state_client is None:
            self.get_logger().error(f"Client for {service_name} is not available")
            return False

        is_state_changed = await call_change_state(change_state_client, transition_id)

        self.destroy_client(change_state_client)
        return is_state_changed

    async def manage_nodes(
        self, request: ChangeState.Request, response: ChangeState.Response
    ) -> ChangeState.Response:
        for node_name in self.node_names:
            self.get_logger().info(f"--- Managing {node_name} ---")

            # If a node is in the requested state, skip it
            state = await self.get_current_state(node_name)
            if state is None:
                response.success = False
                return response
            state: State
            self.get_logger().info(f"Current state: {state.label} (id: {state.id})")
            if state.id == request.transition.id:
                self.get_logger().info(f"{node_name} already in state: {state.label}")
                continue

            # Otherwise, if the requested transition is not available, return failure
            available_transitions = await self.get_available_transitions(node_name)
            if available_transitions is None:
                response.success = False
                return response
            available_transitions: Sequence[TransitionDescription]

            transition_ids = [t.transition.id for t in available_transitions]
            if request.transition.id not in transition_ids:
                transition_name = lifecycle_transitions[request.transition.id]
                self.get_logger().error(
                    f"""Transition {transition_name} (id: {request.transition.id}) not available for {node_name}"""
                )
                response.success = False
                return response

            # Change the state of the node
            is_state_changed = await self.change_state(node_name, request.transition.id)
            if not is_state_changed:
                self.get_logger().error(
                    f"Failed to change state of {node_name} to {request.transition.label}"
                )
                response.success = False
                return response

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
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
