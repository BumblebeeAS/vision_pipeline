from launch import LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

from vision_pipeline.common.uav2_image_proc import get_image_proc_nodes


def evaluate_launch(context, *args, **kwargs):
    image_proc_container = ComposableNodeContainer(
        name="image_proc_container",
        package="rclcpp_components",
        executable="component_container_mt",
        composable_node_descriptions=get_image_proc_nodes(),
        namespace="",
        output="screen",
        arguments=["--ros-args", "--log-level", "info"],
    )

    return [image_proc_container]


def generate_launch_description():
    return LaunchDescription([OpaqueFunction(function=evaluate_launch)])


if __name__ == "__main__":
    generate_launch_description()
