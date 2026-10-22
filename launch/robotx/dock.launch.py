"""ASV5 dock vision pipeline: BEV dock pose + dock window detection.

Each stage has its own lifecycle manager so it can be toggled independently
(lifecycle_msgs/srv/ChangeState, transition 3 = activate, 4 = deactivate):

- /asv5/dock_bev/manage_nodes: dock pose from the lidar BEV (template matching),
  published to /asv5/dock_bev/pose, and the dock panel plane from the OAK-D
  window YOLO + stereo depth, published to /asv5/dock/depth_planar/pose. The BEV itself comes from lidar_segmentation2.
- /asv5/dockwin/manage_nodes: dock window YOLO on the OAK-D, feeding the
  dockwin pose estimator and (optionally) the light sequence decoder.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode, Node, PushRosNamespace

# colcon installs Python nodes with a /usr/bin/python3 shebang, which lacks supervision/cv2
VENV_PYTHON = "/opt/venv/bin/python3"


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "asv5",
        "dock.yaml",
    )

    enable_decoder_arg = DeclareLaunchArgument(
        "enable_decoder",
        default_value="false",
        description="Whether to run the dockwin sequence decoder node",
    )

    bev_nodes = GroupAction(
        [
            PushRosNamespace("/asv5/dock_bev"),
            LifecycleNode(
                package="pose_estimator",
                executable="dock_lidar_pose_estimator_node",
                name="dock_lidar_pose_estimator_node",
                namespace="",
                output="screen",
                parameters=[config],
            ),
            # BEV dock YOLO. Not managed by /asv5/dock_bev/manage_nodes (the
            # estimator does not use its detections); toggle it directly with
            # ros2 lifecycle set /asv5/dock_bev/dock_bev_yolo_node activate.
            LifecycleNode(
                package="yolo_ros_trt",
                executable="yolo_node",
                prefix=VENV_PYTHON,
                name="dock_bev_yolo_node",
                namespace="",
                output="screen",
                parameters=[config],
            ),
            # Dock beacon (LED pattern) YOLO on OAK-D RGB camera, managed by
            # /asv5/dock_bev/manage_nodes for dock bay selection.
            LifecycleNode(
                package="yolo_ros_trt",
                executable="yolo_node",
                prefix=VENV_PYTHON,
                name="dock_beacon_yolo_node",
                namespace="",
                output="screen",
                parameters=[config],
            ),
            
            
             LifecycleNode(
                package="yolo_ros_trt",
                executable="yolo_node",
                prefix=VENV_PYTHON,
                name="dock_planar_window_yolo_node",
                namespace="",
                output="screen",
                parameters=[config],
            ),
            Node(
                package="pose_estimator",
                executable="dock_planar_pose_estimator_node",
                prefix=VENV_PYTHON,
                name="dock_planar_pose_estimator_node",
                output="screen",
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
    )

    dockwin_nodes = GroupAction(
        [
            PushRosNamespace("/asv5/dockwin"),
            LifecycleNode(
                package="yolo_ros_trt",
                executable="yolo_node",
                prefix=VENV_PYTHON,
                name="dockwin_yolo_node",
                namespace="",
                output="screen",
                parameters=[config],
            ),
            Node(
                package="pose_estimator",
                executable="dockwin_pose_estimator_node",
                prefix=VENV_PYTHON,
                name="dockwin_pose_estimator_node",
                parameters=[config],
            ),
            Node(
                package="rx_light_sequence_decoder",
                executable="dockwin_sequence_decoder_node",
                name="dockwin_sequence_decoder_node",
                parameters=[config],
                condition=IfCondition(LaunchConfiguration("enable_decoder")),
            ),
            Node(
                package="vision_pipeline",
                executable="lifecycle_manager_node",
                name="lifecycle_manager_node",
                output="screen",
                parameters=[config],
            ),
        ]
    )

    return LaunchDescription([enable_decoder_arg, bev_nodes, dockwin_nodes])
