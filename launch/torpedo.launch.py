import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode, Node, PushRosNamespace


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "auv4_orin",
        "torpedo.yaml",
    )

    launch_objects = [PushRosNamespace("/auv4/torpedo")]

    yolo_nodes = [
        LifecycleNode(
            package="yolo_ros_trt",
            executable="yolo_node",
            name="torpedo_yolo_node",
            parameters=[config],
            namespace="",
        ),
        LifecycleNode(
            package="yolo_ros_trt",
            executable="yolo_node",
            name="torpedo_hole_yolo_node",
            parameters=[config],
            namespace="",
        ),
        Node(
            package="pose_estimator",
            executable="torpedo_pose_estimator_node",
            name="torpedo_pose_estimator_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="torpedo_pose_estimator_node",
            name="torpedo_hole_pose_estimator_node",
            parameters=[config],
        ),
        Node(
            package="vision_pipeline",
            executable="lifecycle_manager_node",
            name="lifecycle_manager_node",
            parameters=[config],
        ),
    ]

    # image_matching_nodes = [
    #     Node(
    #         package="image_processing",
    #         executable="image_brighten_node",
    #         name="image_brighten_node",
    #         parameters=[config],
    #     ),
    #     Node(
    #         package="image_matching",
    #         executable="simple_matcher_node",
    #         name="simple_matcher_node",
    #         parameters=[config],
    #     ),
    #     Node(
    #         package="pose_estimator",
    #         executable="points_pose_estimator_node",
    #         name="points_pose_estimator_node",
    #         parameters=[config],
    #     ),
    # ]

    vis_nodes = []

    return LaunchDescription(launch_objects + yolo_nodes + vis_nodes)
