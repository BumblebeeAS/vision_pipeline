from typing import Dict

import rcl_interfaces.msg
import rclpy
import rclpy.parameter
import yaml
from composition_interfaces.srv import ListNodes, LoadNode


def parse_list_nodes_response(response: ListNodes.Response) -> Dict[str, int]:
    """Parse the ListNodes response and return a dictionary of node names and their unique ids."""
    node_states = {}
    for name, unique_id in zip(response.full_node_names, response.unique_ids):
        node_states[name] = unique_id
    return node_states


def are_node_names_equal(node_name_1: str, node_name_2: str) -> bool:
    """Check if two node names are equal, ignoring first front slash."""
    node_name_1 = node_name_1.lstrip("/")
    node_name_2 = node_name_2.lstrip("/")
    return node_name_1 == node_name_2


def load_yaml_config(config_path: str) -> Dict[str, LoadNode.Request]:
    """Load the YAML configuration file and return a dictionary of node parameters.

    Args:
        config_path (str): Path to the YAML configuration file.

    Returns:
        Dict[str, LoadNode.Request]: Dictionary where keys are node names and values
        are LoadNode.Request objects.
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    config: Dict

    node_names = config.keys()
    node_params_dict = {}
    for node_name in node_names:
        param_reprs = config.get(node_name, {})

        request = LoadNode.Request()
        request.package_name = param_reprs.pop("package_name", "")
        request.plugin_name = param_reprs.pop("plugin_name", "")
        request.remap_rules = param_reprs.pop("remap_rules", [])
        request.node_name = node_name

        parameters = [
            rclpy.parameter.Parameter(name, value=value)
            for name, value in param_reprs.items()
        ]
        request.parameters = [
            rcl_interfaces.msg.Parameter(
                name=param.name, value=param.get_parameter_value()
            )
            for param in parameters
        ]

        node_params_dict[node_name] = request

    return node_params_dict
