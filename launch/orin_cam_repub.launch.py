from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

from launch import LaunchDescription


def generate_launch_description():
    repub_nodes = []

    for cam_name in ["front_cam", "bot_cam"]:
        cam_container_nodes = []

        if cam_name == "front_cam":
            cam_container_nodes.extend(
                [
                    ComposableNode(
                        package="image_proc",
                        plugin="image_proc::RectifyNode",
                        name="front_cam_rectify_node",
                        namespace=f"auv4/{cam_name}/",
                        parameters=[{"image_transport": "raw"}],
                        remappings=[
                            ("image", "color/image"),
                            ("camera_info", "color/camera_info"),
                            ("image_rect", "color/rect/image"),
                            ("image_rect/compressed", "color/rect/image/compressed"),
                        ],
                    ),
                ]
            )

        container = ComposableNodeContainer(
            name="orin_repub_container",
            namespace=f"auv4/{cam_name}/",
            package="rclcpp_components",
            executable="component_container",
            composable_node_descriptions=cam_container_nodes,
            output="screen",
        )
        repub_nodes.append(container)

    return LaunchDescription(repub_nodes)
