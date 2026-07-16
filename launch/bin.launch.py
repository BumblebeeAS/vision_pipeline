import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode, Node, PushRosNamespace


def launch_setup(context, *args, **kwargs):
    vehicle = LaunchConfiguration("vehicle").perform(context)
    namespace = vehicle.split("_")[0]

    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        vehicle,
        "bin.yaml",
    )

    yolo_nodes = [
        LifecycleNode(
            package="yolo_ros_trt",
            executable="yolo_node",
            name="bin_yolo_node",
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
        # Sim lightbox detector: feeds the bin structure PF's secondary
        # detections topic (bin/lightbox/yolo/detections), which until now had
        # no publisher.
        # LifecycleNode(
        #     package="yolo_ros_trt",
        #     executable="yolo_node",
        #     name="bin_lightbox_yolo_node",
        #     parameters=[config],
        #     namespace="",
        # ),
        # _nw: publishes per-class center poses as PoseArray (<= 2) so the
        # array-based cluster nodes can't drop a same-timestamp bin. Must run
        # INSTEAD of the original (same topic names, different message type).
        # Node(
        #     package="pose_estimator",
        #     executable="bin_pose_estimator_node",
        #     name="bin_pose_estimator_node",
        #     parameters=[config],
        # ),
        # Disabled: running the bin structure PF only for now.
        # Node(
        #     package="pose_estimator",
        #     executable="bin_pose_estimator_node_nw",
        #     # Keep the node NAME as bin_pose_estimator_node so the
        #     # /**/bin_pose_estimator_node param block in bin.yaml still applies
        #     # (only the executable changed). Renaming would orphan its params.
        #     name="bin_pose_estimator_node",
        #     parameters=[config],
        # ),
        # Ray-triangulation estimator for the light box: aggregates mask
        # centroids across the search pattern into world-fixed (odom_ned)
        # positions. Its PoseArray output is already aggregated/outlier-gated,
        # so it does NOT go through the clustering stage.
        # Node(
        #     package="pose_estimator",
        #     executable="light_box_triangulation_pose_estimator_node",
        #     name="light_box_triangulation_pose_estimator_node",
        #     parameters=[config],
        # ),
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

    return [
        GroupAction(
            [PushRosNamespace(f"/{namespace}/bin"), *yolo_nodes, *vis_nodes]
        )
    ]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "vehicle",
                default_value="auv4_orin",
                description=(
                    "Config dir under config/ (e.g. auv4_orin, auv5). The ROS "
                    "namespace is the part before the first underscore."
                ),
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )
