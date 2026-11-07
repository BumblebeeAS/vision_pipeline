import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "auv5",
        "front_decoder_test.yaml",
    )

    # Bench test: bottom-cam light box model on the front cam, fed to the light
    # sequence decoder. Own namespace and node names, so it does not clash with
    # pipeline.launch.py. Both nodes start active.
    return LaunchDescription(
        [
            PushRosNamespace("/auv5/front_decoder_test"),
            Node(
                package="yolo_ros_trt",
                executable="yolo_node",
                name="front_light_box_yolo_node",
                parameters=[config],
                # Per-frame ultralytics prints would bury the decoder's lines.
                output="log",
            ),
            # Logs every pulse/gap and "SEQUENCE LOCKED: ..." to the screen.
            Node(
                package="rx_light_sequence_decoder",
                executable="lightbox_sequence_decoder_node",
                name="front_lightbox_sequence_decoder_node",
                parameters=[config],
                output="screen",
            ),
        ]
    )
