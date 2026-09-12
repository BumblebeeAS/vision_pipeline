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
        "uav",
        "aruco.yaml",
    )

    launch_objects = [
        DeclareLaunchArgument(
            "camera_name",
            default_value="",
        ),
        PushRosNamespace(["/uav/", LaunchConfiguration("camera_name")]),
    ]

    pipeline_nodes = [
        Node(
            package="aruco_loco",
            executable="aruco_detector_node",
            name="aruco_detector_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="points_pose_estimator_node",
            name="points_pose_estimator_node",
            parameters=[config],
        ),
    ]

    vis_nodes = []

    return LaunchDescription(launch_objects + pipeline_nodes + vis_nodes)
