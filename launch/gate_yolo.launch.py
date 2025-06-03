import os

from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node, PushRosNamespace

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "auv4_orin",
        "gate_yolo.yaml",
    )

    launch_objects = [
        DeclareLaunchArgument(
            "camera_name",
            default_value="front_cam",
        ),
        PushRosNamespace(["/auv4/", LaunchConfiguration("camera_name")]),
    ]

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
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="shark_fish_estimator_node",
            name="gate_shark_fish_estimator_node",
            parameters=[config],
        ),
    ]

    repub_nodes = [
        Node(
            package="image_transport",
            executable="republish",
            name="gate_compression_node",
            arguments=["raw", "compressed"],
            output="screen",
            parameters=[{"out.jpeg_quality": 50}],
            remappings=[
                ("in", "gate/yolo/image"),
                ("out/compressed", "gate/yolo/image/compressed"),
            ],
        ),
        Node(
            package="image_transport",
            executable="republish",
            name="symbol_compression_node",
            arguments=["raw", "compressed"],
            output="screen",
            parameters=[{"out.jpeg_quality": 50}],
            remappings=[
                ("in", "symbol/yolo/image"),
                ("out/compressed", "symbol/yolo/image/compressed"),
            ],
        ),
    ]

    return LaunchDescription(launch_objects + pipeline_nodes + repub_nodes)
