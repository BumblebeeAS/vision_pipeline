# Lifecycle Manager for normal ROS 2 Lifecycle Nodes
# References:
# https://github.com/ros-navigation/navigation2/tree/main/nav2_lifecycle_manager

from typing import Sequence

import rclpy
from lifecycle_msgs.msg import State, TransitionDescription
from lifecycle_msgs.srv import ChangeState, GetAvailableTransitions, GetState
from rclpy.executors import MultiThreadedExecutor

from vision_pipeline.utils.lifecycle_manager import lifecycle_transitions
from vision_pipeline.utils.service_caller_node import ServiceCallerNode


class LifecycleManager(ServiceCallerNode):
    def __init__(self):
        super().__init__("lifecycle_manager")

        self.node_names = (
            self.declare_parameter(
                "node_names", value=rclpy.Parameter.Type.STRING_ARRAY
            )
            .get_parameter_value()
            .string_array_value
        )

        self.srv = self.create_service(ChangeState, "manage_nodes", self.manage_nodes)

    async def get_current_state(self, node_name: str) -> GetState.Response | None:
        """Get the current state of a node using the GetState service.

        Args:
            node_name (str): Name of the node to get the state of.

        Returns:
            GetState.Response | None: Current state of the node, or None if the service call fails.
        """
        self.get_logger().info(f"Getting current state")

        service_name = f"{node_name}/get_state"
        request = GetState.Request()
        result = await self.call_service(GetState, service_name, request)

        return result

    async def get_available_transitions(
        self, node_name: str
    ) -> GetAvailableTransitions.Response | None:
        """Get the available transitions of a node using the GetAvailableTransitions service.

        Args:
            node_name (str): Name of the node to get the transitions of.

        Returns:
            GetAvailableTransitions.Response | None: Available transitions for the node,
            or None if the service call fails.
        """
        self.get_logger().info(f"Getting available states")

        service_name = f"{node_name}/get_available_transitions"
        request = GetAvailableTransitions.Request()
        result = await self.call_service(GetAvailableTransitions, service_name, request)

        return result

    async def change_state(
        self, node_name: str, transition_id: int
    ) -> ChangeState.Response | None:
        """Change the state of a node using the ChangeState service.

        Args:
            node_name (str): Name of the node to change the state of.
            transition_id (int): ID of the transition to change to.

        Returns:
            ChangeState.Response | None: True if the state was changed successfully, False otherwise,
            or None if the service call fails.
        """
        self.get_logger().info(f"Changing state")

        service_name = f"{node_name}/change_state"
        request = ChangeState.Request()
        request.transition.id = transition_id
        result = await self.call_service(ChangeState, service_name, request)

        return result

    async def manage_nodes(
        self, request: ChangeState.Request, response: ChangeState.Response
    ) -> ChangeState.Response:
        for node_name in self.node_names:
            self.get_logger().info(f"--- Managing {node_name} ---")

            # If a node is in the requested state, skip it
            get_state_response = await self.get_current_state(node_name)
            if get_state_response is None:
                response.success = False
                return response
            state = get_state_response.current_state
            self.get_logger().info(f"Current state: {state.label} (id: {state.id})")
            if state.id == request.transition.id:
                self.get_logger().info(f"{node_name} already in state: {state.label}")
                continue

            # Otherwise, if the requested transition is not available, return failure
            get_available_transitions_response = await self.get_available_transitions(
                node_name
            )
            if get_available_transitions_response is None:
                response.success = False
                return response
            available_transitions: Sequence[TransitionDescription] = (
                get_available_transitions_response.available_transitions
            )

            transition_ids = [t.transition.id for t in available_transitions]
            if request.transition.id not in transition_ids:
                transition_name = lifecycle_transitions[request.transition.id]
                self.get_logger().error(
                    f"""Transition {transition_name} (id: {request.transition.id}) not available for {node_name}"""
                )
                response.success = False
                return response

            # Change the state of the node
            change_state_response = await self.change_state(
                node_name, request.transition.id
            )
            if change_state_response is None or not change_state_response.success:
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
