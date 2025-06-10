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
        "slalom.yaml",
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
            name="slalom_yolo_node",
            parameters=[config],
        ),
        Node(
            package="depth_anything_ros2_trt",
            executable="depth_anything_node",
            name="slalom_depth_anything_node",
            output="screen",
            parameters=[config],
            remappings=[
                ("~/input/image", "color/image/orin"),
                ("~/output/depth_image", "slalom/depth/image"),
            ],
        ),
        Node(
            package="pose_estimator",
            executable="slalom_pose_estimator_node",
            name="slalom_pose_estimator_node",
            output="screen",
            parameters=[config],
        ),
    ]

    vis_nodes = [
        Node(
            package="image_processing",
            executable="depth_to_rgb_node",
            name="slalom_depth_to_rgb_node",
            output="screen",
            parameters=[config],
        ),
        Node(
            package="image_transport",
            executable="republish",
            name="slalom_yolo_compression_node",
            arguments=["raw", "compressed"],
            output="screen",
            remappings=[
                ("in", "slalom/yolo/image"),
                ("out/compressed", "slalom/yolo/image/compressed"),
            ],
        ),
        Node(
            package="image_transport",
            executable="republish",
            name="slalom_depth_compression_node",
            arguments=["raw", "compressed"],
            output="screen",
            remappings=[
                ("in", "slalom/depth/color/image"),
                ("out/compressed", "slalom/depth/color/image/compressed"),
            ],
        ),
    ]

    return LaunchDescription(launch_objects + pipeline_nodes + vis_nodes)
