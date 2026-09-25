import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode, Node, PushRosNamespace


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "asv5",
        "dock.yaml",
    )

    return LaunchDescription(
        [
            PushRosNamespace("/asv5/dock"),
            LifecycleNode(
                package="yolo_ros_trt",
                executable="yolo_node",
                name="led_yolo_node",
                parameters=[config],
                namespace="",
            ),
            LifecycleNode(
                package="yolo_ros_trt",
                executable="yolo_node",
                name="dock_window_yolo_node",
                parameters=[config],
                namespace="",
            ),
            
            LifecycleNode(
                package="yolo_ros_trt",
                executable="yolo_node",
                name="dock_beacon_yolo_node",
                parameters=[config],
                namespace="",
            ),
            
            LifecycleNode(
                package="yolo_ros_trt",
                executable="yolo_node",
                name="dock_window_plane_yolo_node",
                parameters=[config],
                namespace="",
            ),
            

            Node(
                package="vision_pipeline",
                executable="lifecycle_manager_node",
                name="lifecycle_manager_node",
                output="screen",
                parameters=[config],
            ),
        ]
    )
