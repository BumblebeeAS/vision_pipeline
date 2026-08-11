import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "auv4_orin",
        "torpedo.yaml",
    )

    launch_objects = [PushRosNamespace("/auv4/torpedo")]

    yolo_nodes = [
        # symbols + board share front_cam/color/image; run them in ONE
        # multi_yolo_node so the debayer publishes to a single reader and the
        # frame is decoded once. The `symbols` model runs in track mode
        # (replacing the old tracking_node), `board` in plain predict mode.
        Node(
            package="yolo_ros_trt",
            executable="multi_yolo_node",
            name="torpedo_vision_node",
            parameters=[config],
        ),
        # Node(
        #     package="image_processing",
        #     executable="image_brighten_node",
        #     name="image_brighten_node",
        #     parameters=[config],
        # ),
        Node(
            package="pose_estimator",
            executable="torpedo_pose_estimator_node",
            name="torpedo_pose_estimator_node",
            parameters=[config],
        ),
        # Node(
        #     package="pose_estimator",
        #     executable="red_circle_pose_estimator_node",
        #     name="torpedo_hole_pose_estimator_node",
        #     parameters=[config],
        # ),
        # Shared-shift board-pose variant, running alongside for A/B. Publishes
        # to torpedo/hole_board/* (distinct from the per-hole node's
        # torpedo/hole/*); annotation topics remapped so the two don't collide.
        Node(
            package="pose_estimator",
            executable="red_circle_board_pose_estimator_node",
            name="torpedo_hole_board_pose_estimator_node",
            parameters=[config],
            remappings=[
                ("ellipse_annotation", "board_ellipse_annotation"),
                ("inlier_points_annotation", "board_inlier_points_annotation"),
            ],
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
    # vis_nodes = [
    #     Node(
    #         package="custom_image_republisher",
    #         executable="republish",
    #         name="brighten_compression_node",
    #         output="screen",
    #         parameters=[config],
    #         remappings=[
    #             ("in", "/auv4/front_cam/color/brighten/image"),
    #             ("out/compressed", "/auv4/front_cam/color/brighten/image/compressed"),
    #         ],
    #     ),
    # ]

    vis_nodes = []

    return LaunchDescription(launch_objects + yolo_nodes + vis_nodes)
