import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    # We can use the same config for both front and back, unused configs will be ignored
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "auv5",
        "gate.yaml",
    )

    launch_objects = [PushRosNamespace("/auv5/gate")]

    pipeline_nodes = [
        # gate + symbol share front_cam/color/image; run them in ONE node so the
        # debayer publishes to a single reader and the 9.4 MB frame is decoded
        # once (instead of one yolo_node + one decode per model). They are always
        # activated together by the lifecycle manager, so merging them does not
        # change the activation API -- node_names below now lists this one node.
        Node(
            package="yolo_ros_trt",
            executable="multi_yolo_node",
            name="gate_vision_node",
            parameters=[config],
        ),
        # Node(
        #     package="pose_estimator",
        #     executable="gate_pose_estimator_node",
        #     name="gate_front_pose_estimator_node",
        #     parameters=[config],
        # ),
        Node(
            package="pose_estimator",
            executable="gate_pose_estimator_node",
            name="gate_back_pose_estimator_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="gate_structure_pose_estimator_node",
            name="gate_structure_pose_estimator_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="sos_repair_estimator_node",
            name="sos_repair_estimator_node",
            parameters=[config],
        ),
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
