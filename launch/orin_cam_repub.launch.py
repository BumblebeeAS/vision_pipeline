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

        # Lossy compression for visualization
        # (SBC -> Orin is lossless)
        compress_node = Node(
            package="image_transport",
            executable="republish",
            name="orin_compression_node",
            arguments=["raw", "compressed"],
            output="screen",
            parameters=[{".out.jpeg_quality": 50}],
            namespace=f"auv4/{cam_name}/",
            remappings=[
                ("in", "color/image/orin"),
                ("out/compressed", "color/vis/image/compressed"),
            ],
        )

        repub_nodes.append(repub_node)
        repub_nodes.append(compress_node)

    return LaunchDescription(repub_nodes)
