from launch import LaunchDescription
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    return LaunchDescription([
        ComposableNodeContainer(
            name="orin_repub_container",
            namespace="auv4/front_cam",
            package="rclcpp_components",
            executable="component_container",
            composable_node_descriptions=[
                ComposableNode(
                    package="image_proc",
                    plugin="image_proc::RectifyNode",
                    name="front_cam_rectify_node",
                    namespace="auv4/front_cam",
                    parameters=[{"image_transport": "raw"}],
                    remappings=[
                        ("image", "color/image"),
                        ("camera_info", "color/camera_info"),
                        ("image_rect", "color/rect/image"),
                        ("image_rect/compressed", "color/rect/image/compressed"),
                    ],
                ),
            ],
            output="screen",
        ),
    ])
