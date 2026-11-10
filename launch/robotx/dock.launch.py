"""ASV5 dock vision pipeline: BEV dock pose + dock window detection.

Each stage has its own lifecycle manager so it can be toggled independently
(lifecycle_msgs/srv/ChangeState, transition 3 = activate, 4 = deactivate):

- /asv5/dock_bev/manage_nodes: dock pose from the lidar BEV (BEV YOLO ROI +
  template matching), published to /asv5/dock_bev/pose. The BEV itself comes
  from lidar_segmentation2.
- /asv5/dock_bev/manage_planar_nodes: OAK-D dock window plane YOLO. The planar
  pose estimator is a plain node and publishes /asv5/dock/depth_planar/pose
  only while that YOLO is active.
- /asv5/dockwin/manage_nodes: dock window YOLO on the OAK-D, feeding the
  dockwin pose estimator and (optionally) the light sequence decoder.

/asv5/dock_led_count (bb_robotx_msgs/srv/DockLedCount) counts dock LED
patterns (HSV or beacon YOLO) for the dock tree.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode, Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterValue

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

    output_sequence_raw_topic_arg = DeclareLaunchArgument(
        "output_sequence_raw_topic",
        default_value="dockwin/light_sequence_raw",
        description="Topic for raw uint8 light sequence output",
    )

    beacon_image_topic_arg = DeclareLaunchArgument(
        "beacon_image_topic",
        default_value="/asv5/oakd/rgb_enhanced/image_raw",
        description="Image topic for the dock beacon YOLO (needs the OAK-D "
        "image enhancer running)",
    )

    activate_dock_pose_arg = DeclareLaunchArgument(
        "activate_dock_pose",
        default_value="false",
        description="Activate the dock lidar pose estimator and the BEV and "
        "planar window YOLOs on start instead of via manage_nodes "
        "(asv_main deactivates them again before the first tick)",
    )
    use_bev_yolo_arg = DeclareLaunchArgument(
        "use_bev_yolo",
        default_value="false",
        description="Launch the BEV dock YOLO and manage it with the BEV pose "
        "pipeline (the estimator only reads it if dock.yaml "
        "input_detections_topic is set). Must match asv_main USE_BEV_YOLO.",
    )
    use_bev_yolo = LaunchConfiguration("use_bev_yolo")
    bev_managed_nodes = ["dock_lidar_pose_estimator_node"]

    # Overrides dock.yaml activate_on_start for the dock pose pipeline. The
    # lifecycle manager skips nodes already active.
    activate_dock_pose = {
        "activate_on_start": ParameterValue(
            LaunchConfiguration("activate_dock_pose"), value_type=bool
        )
    }

    bev_nodes = GroupAction(
        [
            PushRosNamespace("/asv5/dock_bev"),
            LifecycleNode(
                package="pose_estimator",
                executable="dock_lidar_pose_estimator_node",
                name="dock_lidar_pose_estimator_node",
                namespace="",
                output="screen",
                parameters=[config, activate_dock_pose],
            ),
            # BEV dock YOLO, activated with the dock BEV pose pipeline by
            # /asv5/dock_bev/manage_nodes. Only with use_bev_yolo.
            LifecycleNode(
                package="yolo_ros_trt",
                executable="yolo_node",
                prefix=VENV_PYTHON,
                name="dock_bev_yolo_node",
                namespace="",
                output="screen",
                parameters=[config, activate_dock_pose],
                condition=IfCondition(use_bev_yolo),
            ),
            # Dock beacon (LED pattern) YOLO on the enhanced OAK-D RGB image
            # (bb_oak_driver image_enhancer, oak.launch.py enhance:=true). In no
            # lifecycle group: only the YOLO LED count method needs it.
            LifecycleNode(
                package="yolo_ros_trt",
                executable="yolo_node",
                prefix=VENV_PYTHON,
                name="dock_beacon_yolo_node",
                namespace="",
                output="screen",
                parameters=[
                    config,
                    {"input_image_topic": LaunchConfiguration("beacon_image_topic")},
                ],
            ),
            LifecycleNode(
                package="yolo_ros_trt",
                executable="yolo_node",
                prefix=VENV_PYTHON,
                name="dock_planar_window_yolo_node",
                namespace="",
                output="screen",
                parameters=[config, activate_dock_pose],
            ),
            # Plain node; publishes once the planar window YOLO is active.
            Node(
                package="pose_estimator",
                executable="dock_planar_pose_estimator_node",
                prefix=VENV_PYTHON,
                name="dock_planar_pose_estimator_node",
                output="screen",
                parameters=[config],
            ),

            # node_names comes from use_bev_yolo, not dock.yaml.
            Node(
                package="vision_pipeline",
                executable="lifecycle_manager_node",
                name="lifecycle_manager_node",
                output="screen",
                parameters=[
                    config,
                    {"node_names": bev_managed_nodes + ["dock_bev_yolo_node"]},
                ],
                condition=IfCondition(use_bev_yolo),
            ),
            Node(
                package="vision_pipeline",
                executable="lifecycle_manager_node",
                name="lifecycle_manager_node",
                output="screen",
                parameters=[config, {"node_names": bev_managed_nodes}],
                condition=UnlessCondition(use_bev_yolo),
            ),
            # Planar window YOLO is activated separately, after the
            # observation pose (the window plane is not visible before).
            Node(
                package="vision_pipeline",
                executable="lifecycle_manager_node",
                name="planar_lifecycle_manager_node",
                output="screen",
                parameters=[config],
                remappings=[("manage_nodes", "manage_planar_nodes")],
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
                parameters=[
                    config,
                    {
                        "output_sequence_raw_topic": LaunchConfiguration(
                            "output_sequence_raw_topic"
                        )
                    },
                ],
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

    # Not a lifecycle node: it only subscribes during a DockLedCount call.
    # The HSV method reads the same enhanced image as the beacon YOLO.
    dock_led_count = Node(
        package="dock_led_counter",
        executable="dock_led_count_node",
        prefix=VENV_PYTHON,
        name="dock_led_count_node",
        namespace="/asv5",
        output="screen",
        parameters=[{"hsv_topic": LaunchConfiguration("beacon_image_topic")}],
    )

    return LaunchDescription([
        enable_decoder_arg,
        output_sequence_raw_topic_arg,
        beacon_image_topic_arg,
        activate_dock_pose_arg,
        use_bev_yolo_arg,
        bev_nodes,
        dockwin_nodes,
        dock_led_count,
    ])
