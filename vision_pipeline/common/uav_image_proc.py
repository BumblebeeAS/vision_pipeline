# Image proc nodes shared by the UAV GSCam camera pipeline and the UAV sim pipeline.
# These are inserted into the containers defined in their respective launch files
# to take advantage of IPC.

import os

from ament_index_python.packages import get_package_share_directory
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.descriptions import ComposableNode

from vision_pipeline.common.qos import sensor_data_qos_parameters


def get_image_proc_nodes(use_intra_process_comms=False, camera_fps=15):
    """Create resize, rectification, and visualization components per camera."""
    encoder_config = os.path.join(
        get_package_share_directory("vision_pipeline"), "config", "uav", "vis_h264.yaml"
    )
    keyframe_interval = max(1, round(camera_fps / 2))
    return [
        # Scale the image and calibration together before rectification.
        ComposableNode(
            extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            name="resize_node",
            package="isaac_ros_image_proc",
            plugin="nvidia::isaac_ros::image_proc::ResizeNode",
            parameters=[{
                "output_width": 640,
                "output_height": 360,
                "keep_aspect_ratio": True,
                "input_qos": "SENSOR_DATA",
                "output_qos": "SENSOR_DATA",
            }],
        ),
        ComposableNode(
            extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            name="rectify_node",
            package="isaac_ros_image_proc",
            plugin="nvidia::isaac_ros::image_proc::RectifyNode",
            parameters=[{
                "output_height": 360,
                "output_width": 640,
                "input_qos": "SENSOR_DATA",
                # Isaac's encoder requests reliable input. Best-effort perception
                # subscribers remain compatible with this reliable publisher.
                "output_qos": "DEFAULT",
            }],
            remappings=[
                ("image_raw", "resize/image"),
                ("camera_info", "resize/camera_info"),
                ("image_rect", "rect/image"),
                ("camera_info_rect", "rect/camera_info_internal"),
            ],
        ),
        ComposableNode(
            extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            name="mono_node", package="isaac_ros_image_proc",
            plugin="nvidia::isaac_ros::image_proc::ImageFormatConverterNode",
            parameters=[{
                "encoding_desired": "mono8", "image_width": 640, "image_height": 360,
                "input_qos": "SENSOR_DATA", "output_qos": "SENSOR_DATA",
            }],
            remappings=[("image_raw", "rect/image"), ("image", "rect/mono")],
        ),
        # Hardware H.264 for RF visualization, with a fresh IDR about every 0.5 s.
        ComposableNode(
            extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            package="isaac_ros_h264_encoder",
            plugin="nvidia::isaac_ros::h264_encoder::EncoderNode",
            name="vis_compression_node",
            parameters=[
                encoder_config,
                {
                    "framerate": camera_fps,
                    "iframe_interval": keyframe_interval,
                    "idr_interval": keyframe_interval,
                },
            ],
            remappings=[
                ("image_raw", "rect/image"),
                ("image_compressed", "rect/image/vis/compressed"),
            ],
        ),
    ]


def get_foxglove_video_node():
    """Expose the hardware encoder's bytes as native Foxglove video."""
    namespace = LaunchConfiguration("ros_namespace", default="/")
    return Node(
        package="topic_tools",
        executable="transform",
        name="h264_to_foxglove_node",
        arguments=[
            PathJoinSubstitution([namespace, "rect/image/vis/compressed"]),
            PathJoinSubstitution([namespace, "rect/image/vis/video"]),
            "foxglove_msgs/msg/CompressedVideo",
            "foxglove_msgs.msg.CompressedVideo("
            "timestamp=m.header.stamp, frame_id=m.header.frame_id, "
            "data=m.data, format=m.format)",
            "--import", "foxglove_msgs",
            "--wait-for-start",
            "--qos-reliability", "reliable",
            "--qos-depth", "1",
        ],
        output="screen",
    )


def get_rectified_camera_info_node():
    # Isaac may retain the fisheye model with a five-element zero D array.
    # Describe the rectified image as a pinhole camera for downstream clients.
    return Node(
        package="image_processing",
        executable="rectified_camera_info_node",
        name="rectified_camera_info_node",
        parameters=[sensor_data_qos_parameters(
            "rect/camera_info_internal", "rect/camera_info"
        )],
        output="screen",
    )
