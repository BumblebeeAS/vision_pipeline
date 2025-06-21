# References:
# https://github.com/ros2/rclpy/issues/1313#issuecomment-2307615945


from typing import Any

from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.client import Client
from rclpy.node import Node


class ServiceCallerNode(Node):
    def __init__(self, node_name: str):
        super().__init__(node_name)

        self.wait_timeout_sec = (
            self.declare_parameter("wait_timeout_sec", 1.0)
            .get_parameter_value()
            .double_value
        )

        # Required to create clients in the service callback
        # without blocking the main thread
        # It seems that creating a list of clients in __init__ does not work with rclpy.spin
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

    async def call_service(
        self, service_type: type, service_name: str, request
    ) -> Any | None:
        """Call a service and return the response.

        Args:
            service_type (type): Type of the service to call.
            service_name (str): Name of the service to call.
            request: Request object for the service.

        Returns:
            Any: Response from the service call.
        """
        client = self.get_client_and_check_service(service_type, service_name)
        if client is None:
            self.get_logger().error(f"Client for {service_name} is not available")
            return None

        future = client.call_async(request)
        response = await future

        self.destroy_client(client)
        return response
