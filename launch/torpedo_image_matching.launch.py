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
        "torpedo_image_matching.yaml",
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
            package="image_processing",
            executable="image_brighten_node",
            name="image_brighten_node",
            parameters=[config],
        ),
        Node(
            package="image_matching",
            executable="simple_matcher_node",
            name="simple_matcher_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="points_pose_estimator_node",
            name="points_pose_estimator_node",
            parameters=[config],
        ),
    ]

    repub_nodes = [
        Node(
            package="image_transport",
            executable="republish",
            name="image_republisher",
            arguments=["raw", "compressed"],
            output="screen",
            parameters=[{"out.jpeg_quality": 30}],
            remappings=[
                ("in", "color/brighten/image"),
                ("out/compressed", "color/brighten/image/compressed"),
            ],
        ),
        Node(
            package="image_transport",
            executable="republish",
            name="image_republisher",
            arguments=["raw", "compressed"],
            output="screen",
            parameters=[{"out.jpeg_quality": 30}],
            remappings=[
                ("in", "image_matching/image"),
                ("out/compressed", "image_matching/image/compressed"),
            ],
        ),
    ]

    return LaunchDescription(launch_objects + pipeline_nodes + repub_nodes)
