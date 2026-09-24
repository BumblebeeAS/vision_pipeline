import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace

from vision_pipeline.common.image_transport import republisher_parameters


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "auv4_orin",
        "torpedo_image_matching.yaml",
    )

    # Share namespace with torpedo.launch.py so image_matching/* topics and the
    # toggle_template service line up with the rest of the torpedo pipeline.
    launch_objects = [PushRosNamespace("/auv4/torpedo")]

    # Brighten the rectified front_cam image, run XFeat template matching against
    # the robosub26 templates, then solve a PnP pose from the correspondences.
    image_matching_nodes = [
        Node(
            package="image_processing",
            executable="image_brighten_node",
            name="image_brighten_node",
            parameters=[config],
        ),
        Node(
            package="image_matching",
            executable="simple_matcher_node",
            name="simple_matcher_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="points_pose_estimator_node",
            name="points_pose_estimator_node",
            parameters=[config],
        ),
    ]

    vis_nodes = [
        Node(
            package="image_transport",
            executable="republish",
            name="brighten_compression_node",
            output="screen",
            parameters=[
                config,
                republisher_parameters(
                    "/auv4/front_cam/color/brighten/image",
                    "/auv4/front_cam/color/brighten/image/compressed",
                ),
            ],
            remappings=[
                ("in", "/auv4/front_cam/color/brighten/image"),
                ("out/compressed", "/auv4/front_cam/color/brighten/image/compressed"),
            ],
        ),
    ]

    return LaunchDescription(launch_objects + image_matching_nodes + vis_nodes)
