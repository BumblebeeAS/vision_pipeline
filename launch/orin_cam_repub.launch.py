from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    repub_nodes = []

    for cam_name in ["front_cam", "bot_cam"]:
        repub_node = Node(
            package="image_transport",
            executable="republish",
            name="sbc2orin_repub_node",
            arguments=["compressed", "raw"],
            output="screen",
            parameters=[],
            namespace=f"auv4/{cam_name}/",
            remappings=[
                ("in/compressed", "color/image/compressed"),
                ("out", "color/image/orin"),
            ],
        )
        repub_nodes.append(repub_node)

    return LaunchDescription(repub_nodes)
