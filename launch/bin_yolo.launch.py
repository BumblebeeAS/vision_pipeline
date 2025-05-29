import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "auv4_orin",
        "bin_yolo.yaml",
    )

    launch_objects = [
        DeclareLaunchArgument(
            "camera_name",
            default_value="bot_cam",
        ),
        PushRosNamespace(["/auv4/", LaunchConfiguration("camera_name")]),
    ]

    pipeline_nodes = [
        Node(
            package="yolo_ros_trt",
            executable="yolo_node",
            name="bin_yolo_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="bin_pose_estimator_node",
            name="bin_pose_estimator_node",
            parameters=[config],
        ),
    ]

    repub_nodes = [
        Node(
            package="image_transport",
            executable="republish",
            name="bin_compression_node",
            arguments=["raw", "compressed"],
            output="screen",
            parameters=[{"out.jpeg_quality": 50}],
            remappings=[
                ("in", "bin/yolo/image"),
                ("out/compressed", "bin/yolo/image/compressed"),
            ],
        ),
    ]

    return LaunchDescription(launch_objects + pipeline_nodes + repub_nodes)
