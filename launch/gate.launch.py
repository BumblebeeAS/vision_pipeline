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

    launch_objects = [PushRosNamespace("/auv4/gate")]

    pipeline_nodes = [
        # Single gate model on auv4 -- the symbol model was dropped here, so this
        # is a plain yolo_node rather than the multi_yolo_node auv5 uses. See
        # gate.auv5.launch.py for the two-model variant.
        Node(
            package="yolo_ros_trt",
            executable="yolo_node",
            name="gate_vision_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="gate_pose_estimator_node",
            name="gate_front_pose_estimator_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="gate_pose_estimator_node",
            name="gate_back_pose_estimator_node",
            parameters=[config],
        ),
        # Node(
        #     package="pose_estimator",
        #     executable="sos_repair_estimator_node",
        #     name="sos_repair_estimator_node",
        #     parameters=[config],
        # ),
        Node(
            package="vision_pipeline",
            executable="lifecycle_manager_node",
            name="lifecycle_manager_node",
            output="screen",
            parameters=[config],
        ),
    ]

    vis_nodes = []

    return LaunchDescription(launch_objects + pipeline_nodes + vis_nodes)
