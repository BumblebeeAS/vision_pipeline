from typing import Dict

import rclpy
from composition_interfaces.srv import ListNodes, LoadNode, UnloadNode
from rclpy.executors import MultiThreadedExecutor
from std_srvs.srv import SetBool

from vision_pipeline.utils.component_manager import (
    load_yaml_config,
    parse_list_nodes_response,
)
from vision_pipeline.utils.service_caller_node import ServiceCallerNode


class ComponentManagerNode(ServiceCallerNode):
    def __init__(self):
        super().__init__("component_manager_node")

        self.container_name = (
            self.declare_parameter("container_name", "ComponentManager")
            .get_parameter_value()
            .string_value
        )
        self.config_path = (
            self.declare_parameter("config_path", "").get_parameter_value().string_value
        )

        self.node_request_dict = load_yaml_config(self.config_path)
        self.get_logger().info(f"Params_config: {self.node_request_dict}")
        self.container_service_ns = f"{self.container_name}/_container"

        self.srv = self.create_service(SetBool, "manage_components", self.manage_nodes)

    async def list_nodes(self) -> ListNodes.Response | None:
        """Get the list of nodes in the component container.

        Returns:
            ListNodes.Response | None: List of nodes in the component container
            or None if the service call fails.
        """
        self.get_logger().info(f"Listing nodes")

        service_name = f"{self.container_service_ns}/list_nodes"
        request = ListNodes.Request()
        result = await self.call_service(ListNodes, service_name, request)

        return result

    async def load_nodes(self, node_request_dict: Dict[str, LoadNode.Request]) -> bool:
        for node_name, request in node_request_dict.items():
            self.get_logger().info(f"Loading node {node_name}")
            service_name = f"{self.container_service_ns}/load_node"

            result = await self.call_service(LoadNode, service_name, request)
            if result is None or not result.success:
                self.get_logger().error(f"Failed to load node {node_name}")
                return False

        return True

    async def unload_nodes(self, curr_nodes_dict: Dict[str, int]) -> bool:
        for node_name, unique_id in curr_nodes_dict.items():
            self.get_logger().info(f"Unloading node {node_name}")
            service_name = f"{self.container_service_ns}/unload_node"
            request = UnloadNode.Request()
            request.unique_id = unique_id

            result = await self.call_service(UnloadNode, service_name, request)
            if result is None or not result.success:
                self.get_logger().error(f"Failed to unload node {node_name}")
                return False

        return True

    async def manage_nodes(
        self, request: SetBool.Request, response: SetBool.Response
    ) -> SetBool.Response:
        is_load_nodes = request.data

        # List the nodes in the component container
        self.get_logger().info(f"Listing nodes in {self.container_name}")

        list_nodes_response = await self.list_nodes()
        if list_nodes_response is None:
            self.get_logger().error(f"Failed to list nodes in {self.container_name}")
            response.success = False
            return response
        list_nodes_response: ListNodes.Response

        curr_nodes_dict = parse_list_nodes_response(list_nodes_response)

        # Load nodes
        if is_load_nodes:
            filtered_node_request_dict = {
                k: v
                for k, v in self.node_request_dict.items()
                if k not in curr_nodes_dict
            }
            response.success = await self.load_nodes(filtered_node_request_dict)
            return response

        # Unload nodes
        else:
            response.success = await self.unload_nodes(curr_nodes_dict)
            return response


def main(args=None):
    rclpy.init(args=args)
    node = ComponentManagerNode()
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
