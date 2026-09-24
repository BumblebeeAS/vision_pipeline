import os

from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import ComposableNodeContainer, Node, PushRosNamespace

from launch import LaunchDescription

from vision_pipeline.common.image_transport import republisher_parameters


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "auv5",
        "slalom.yaml",
    )
    launch_objects = [PushRosNamespace("/auv5/slalom")]

    pipeline_nodes = [
        Node(
            package="yolo_ros_trt",
            executable="yolo_node",
            name="slalom_yolo_node",
            parameters=[config],
        ),
        # Node(
        #     package="pose_estimator",
        #     executable="slalom_pose_estimator_node",
        #     name="slalom_pose_estimator_node",
        #     output="screen",
        #     parameters=[config],
        # ),
        # Node(
        #     package="pose_estimator",
        #     executable="slalom_pose_estimator_node",
        #     name="slalom_pose_estimator_near_node",
        #     output="screen",
        #     parameters=[config],
        # ),
        # ComposableNodeContainer(
        #     package="rclcpp_components",
        #     executable="component_container",
        #     name="depth_anything_container",
        #     composable_node_descriptions=[],
        #     output="screen",
        #     arguments=["--ros-args", "--log-level", "INFO"],
        #     namespace="",
        # ),
        # Node(
        #     package="vision_pipeline",
        #     executable="component_manager_node",
        #     name="slalom_component_manager_node",
        #     output="screen",
        #     parameters=[config],
        # ),
        Node(
            package="pose_estimator",
            executable="slalom_structure_pf_node",
            name="slalom_structure_pf_node",
            output="screen",
            parameters=[config],
        ),
        Node(
            package="vision_pipeline",
            executable="lifecycle_manager_node",
            name="slalom_lifecycle_manager_node",
            output="screen",
            parameters=[config],
        ),
    ]

    vis_nodes = [
        Node(
            package="image_processing",
            executable="depth_to_rgb_node",
            name="slalom_depth_to_rgb_node",
            output="screen",
            parameters=[config],
        ),
        Node(
            package="image_transport",
            executable="republish",
            name="slalom_depth_compression_node",
            output="screen",
            parameters=[
                config,
                republisher_parameters(
                    "depth/color/image",
                    "depth/color/image/compressed",
                ),
            ],
            remappings=[
                ("in", "depth/color/image"),
                ("out/compressed", "depth/color/image/compressed"),
            ],
        ),
    ]

    # return LaunchDescription(launch_objects + pipeline_nodes + vis_nodes)
    return LaunchDescription(launch_objects + pipeline_nodes)
