import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "uav",
        "tins.yaml",
    )

    launch_objects = [PushRosNamespace("/uav/tins")]

    pipeline_nodes = [
        Node(
            package="pose_estimator",
            executable="helipad_pose_estimator_node",
            name="helipad_pose_estimator_node",
            namespace="/uav/wide_a",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="helipad_pose_estimator_node",
            name="helipad_pose_estimator_node",
            namespace="/uav/narrow_a",
            parameters=[config, {
                "camera_info_topic": "/uav/narrow_a/rect/camera_info",
                "input_detections_topic": "/uav/narrow_a/rfdetr/detections",
                "output_pose_topic": "helipad/pose",
                "object_frame_id": "uav/narrow_a/helipad",
            }],
        ),
        Node(
            package="pose_estimator",
            executable="tins_pad_pose_estimator_node",
            name="tins_pad_pose_estimator_node",
            namespace="/uav/wide_a",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="tins_pad_pose_estimator_node",
            name="tins_pad_pose_estimator_node",
            namespace="/uav/narrow_a",
            parameters=[config, {
                "camera_info_topic": "/uav/narrow_a/rect/camera_info",
                "input_detections_topic": "/uav/narrow_a/rfdetr/detections",
                "output_pose_topic": "tins_pad/pose",
                "object_frame_id": "uav/narrow_a/tins_pad",
            }],
        ),
        Node(
            package="pose_estimator",
            executable="tins_pose_estimator_depth_from_odom_node",
            name="tins_pose_estimator_depth_from_odom_node",
            namespace="/uav/wide_a/tins",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="tins_pose_estimator_depth_from_odom_node",
            name="tins_pose_estimator_depth_from_odom_node",
            namespace="/uav/narrow_a/tins",
            parameters=[config, {
                "camera_info_topic": "/uav/narrow_a/rect/camera_info",
                "input_track_detections_topic": "/uav/narrow_a/rfdetr/detections",
            }],
        ),
        Node(
            package="vision_pipeline",
            executable="lifecycle_manager_node",
            name="lifecycle_manager_node",
            output="screen",
            parameters=[config],
        ),
    ]

    return LaunchDescription(launch_objects + pipeline_nodes)
