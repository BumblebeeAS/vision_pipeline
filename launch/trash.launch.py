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
        # items + table share bot_cam/color/image; run them in ONE
        # multi_yolo_node so the debayer publishes to a single reader and the
        # frame is decoded once. `items` runs in track mode; `table` stays in
        # plain predict mode -- the baskets are labelled by image-x /
        # table-pose / symbols, never by track id, so the per-frame ByteTrack
        # association is wasted cost.
        Node(
            package="yolo_ros_trt",
            executable="multi_yolo_node",
            name="trash_bot_vision_node",
            parameters=[config],
        ),
        # Second item tracker on the claw camera. Feeds the claw item stream the
        # dual-cam depth estimators prefer (from_odom) / supplement with
        # (from_table). Same trash item engine as the bot_cam tracker; it stays
        # a separate node because multi_yolo_node is single-camera.
        Node(
            package="yolo_ros_trt",
            executable="tracking_node",
            name="trash_claw_tracking_node",
            parameters=[config],
        ),
        # Node(
        #     package="yolo_ros_trt",
        #     executable="yolo_node",
        #     name="trash_image_yolo_node",
        #     parameters=[config],
        # ),
        Node(
            package="pose_estimator",
            executable="trash_table_pose_estimator_node_new",
            name="trash_table_pose_estimator_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="trash_pose_estimator_depth_from_odom_dual_cam_node",
            name="trash_pose_estimator_depth_from_odom_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="trash_pose_estimator_depth_from_table_dual_cam_node",
            name="trash_pose_estimator_depth_from_table_node",
            parameters=[config],
        ),
        # Node(
        #     package="pose_estimator",
        #     executable="trash_image_pose_estimator_node",
        #     name="trash_image_pose_estimator_node",
        #     parameters=[config],
        # ),
        Node(
            package="pose_estimator",
            executable="trash_detections_processor_node",
            name="trash_detections_processor_node",
            parameters=[config],
        ),
        # Object-in-grabber check off the CLAW item stream (rigid down-looking
        # camera over the arms). Plain node, no inference -- IoA of claw item
        # detections vs. the grab ROI -> trash/in_grabber/yolo/detections.
        Node(
            package="pose_estimator",
            executable="trash_object_in_grabber_node",
            name="trash_object_in_grabber_node",
            parameters=[config],
        ),
        Node(
            package="vision_pipeline",
            executable="lifecycle_manager_node",
            name="trash_lifecycle_manager_node",
            parameters=[config],
        ),
    ]

    vis_nodes = []

    return LaunchDescription(launch_objects + pipeline_nodes + vis_nodes)
