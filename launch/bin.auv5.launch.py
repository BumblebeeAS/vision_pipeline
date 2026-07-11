import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode, Node, PushRosNamespace


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "auv5",
        "bin.yaml",
    )

    launch_objects = [PushRosNamespace("/auv5/bin")]

    yolo_nodes = [
        # bin + lightbox share bot_cam/color/image; run them in ONE node so
        # the frame is decoded once (instead of one yolo_node + one decode
        # per model). Same pattern as gate_vision_node in gate.launch.py.
        LifecycleNode(
            package="yolo_ros_trt",
            executable="multi_yolo_node",
            name="bin_vision_node",
            parameters=[config],
            namespace="",
        ),
        # LifecycleNode(
        #     package="yolo_ros_trt",
        #     executable="yolo_node",
        #     name="light_box_face_plate_yolo_node",
        #     parameters=[config],
        #     namespace="",
        # ),
        # Node(
        #     package="pose_estimator",
        #     executable="light_box_pose_estimator_node",
        #     name="light_box_pose_estimator_node",
        #     parameters=[config],
        # ),
        Node(
            package="pose_estimator",
            executable="light_box_pose_estimator_node",
            name="light_box_pose_estimator_node",
            parameters=[config],
        ),
        # Structure-level particle filter over the whole rigid bin setup:
        # one 4-DOF state (x, y, z, yaw) derives all 4 bins + 2 light boxes.
        # Dormant until enabled via its SetBool service (~/track/enable:
        # true = reset + accumulate, false = stop + latch final landmarks
        # PoseArray -- no TF output), so it
        # is safe to run alongside the per-detection estimators above.
        Node(
            package="pose_estimator",
            executable="bin_structure_pf_node",
            name="bin_structure_pf_node",
            parameters=[config],
        ),
        Node(
            package="vision_pipeline",
            executable="lifecycle_manager_node",
            name="lifecycle_manager_node",
            parameters=[config],
        ),
    ]

    vis_nodes = []

    return LaunchDescription(launch_objects + yolo_nodes + vis_nodes)
