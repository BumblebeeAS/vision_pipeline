import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    # We can use the same config for both front and back, unused configs will be ignored
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "auv4_orin",
        "gate.yaml",
    )

    launch_objects = [PushRosNamespace("/auv4/gate_front")]

    pipeline_nodes = [
        Node(
            package="yolo_ros_trt",
            executable="yolo_node",
            name="gate_yolo_node",
            parameters=[config],
        ),
        Node(
            package="yolo_ros_trt",
            executable="yolo_node",
            name="symbol_yolo_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="gate_pose_estimator_node",
            name="gate_pose_estimator_node",
            parameters=[config, {"from_front": True}],
        ),
        Node(
            package="pose_estimator",
            executable="shark_fish_estimator_node",
            name="gate_shark_fish_estimator_node",
            parameters=[config],
        ),
        Node(
            package="vision_pipeline",
            executable="lifecycle_manager_node",
            name="lifecycle_manager_node",
            output="screen",
            parameters=[
                config,
                {"node_names": ["gate_yolo_node", "symbol_yolo_node"]},
            ],
        ),
    ]

    vis_nodes = []

    return LaunchDescription(launch_objects + pipeline_nodes + vis_nodes)
