from launch import LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import ComposableNodeContainer, Node

from vision_pipeline.common.uav_image_proc import get_image_proc_nodes


def evaluate_launch(context, *args, **kwargs):
    restamp_camera_node = Node(
        package="image_processing",
        executable="restamp_camera_node",
        name="uav_restamp_camera_node",
        parameters=[
            {
                "in_image": "unstamped/image",
                "out_image": "image",
                "in_info": "unstamped/camera_info",
                "out_info": "camera_info",
            }
        ],
        output="screen",
    )

    image_proc_container = ComposableNodeContainer(
        name="image_proc_container",
        package="rclcpp_components",
        executable="component_container_mt",
        composable_node_descriptions=get_image_proc_nodes(),
        namespace="",
        output="screen",
        arguments=["--ros-args", "--log-level", "info"],
    )

    return [image_proc_container, restamp_camera_node]


def generate_launch_description():
    return LaunchDescription([OpaqueFunction(function=evaluate_launch)])


if __name__ == "__main__":
    generate_launch_description()
