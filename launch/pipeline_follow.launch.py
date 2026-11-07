import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "auv5",
        "pipeline.yaml",
    )

    # Kept out of pipeline.launch.py so the follower can be relaunched without
    # restarting the models. Run alongside it; do not start a second copy, or
    # /auv5/pipeline/follow will have two action servers.
    return LaunchDescription(
        [
            PushRosNamespace("/auv5/pipeline"),
            # Action server /auv5/pipeline/follow (node-relative name "follow").
            Node(
                package="pipeline_vision_tracker",
                executable="pipeline_follow_node",
                name="pipeline_follow_node",
                parameters=[config],
                output="screen",
            ),
            # Action server /auv5/pipeline/light_box/dock.
            Node(
                package="pipeline_vision_tracker",
                executable="light_box_dock_node",
                name="light_box_dock_node",
                parameters=[config],
                output="screen",
            ),
            # Action server /auv5/pipeline/light_box/centre: the same node in
            # mode centre, for the find-pipe light box fallback.
            Node(
                package="pipeline_vision_tracker",
                executable="light_box_dock_node",
                name="light_box_centre_node",
                parameters=[config],
                output="screen",
            ),
        ]
    )
