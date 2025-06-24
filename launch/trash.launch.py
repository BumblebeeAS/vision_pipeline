import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "auv4_orin",
        "trash.yaml",
    )

    launch_objects = [PushRosNamespace("/auv4/trash")]

    pipeline_nodes = [
        Node(
            package="yolo_ros_trt",
            executable="yolo_node",
            name="trash_yolo_node",
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
            executable="trash_table_pose_estimator_node",
            name="trash_table_pose_estimator_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="trash_pose_estimator_node",
            name="trash_pose_estimator_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="shark_fish_pose_estimator_node",
            name="shark_fish_pose_estimator_node",
            parameters=[config],
        ),
        Node(
            package="vision_pipeline",
            executable="lifecycle_manager_node",
            name="trash_lifecycle_manager_node",
            parameters=[config],
        ),
    ]

    vis_nodes = [
        Node(
            package="image_transport",
            executable="republish",
            name="trash_compression_node",
            arguments=["raw", "compressed"],
            output="screen",
            parameters=[config],
            remappings=[
                ("in", "trash/yolo/image"),
                ("out/compressed", "trash/yolo/image/compressed"),
            ],
        ),
        Node(
            package="image_transport",
            executable="republish",
            name="symbol_compression_node",
            arguments=["raw", "compressed"],
            output="screen",
            parameters=[config],
            remappings=[
                ("in", "symbol/yolo/image"),
                ("out/compressed", "symbol/yolo/image/compressed"),
            ],
        ),
    ]

    return LaunchDescription(launch_objects + pipeline_nodes + vis_nodes)
