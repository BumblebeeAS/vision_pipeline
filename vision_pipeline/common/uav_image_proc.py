# Image proc nodes shared by the UAV GSCam camera pipeline and the UAV sim pipeline.
# These are inserted into the containers defined in their respective launch files
# to take advantage of IPC.

from launch_ros.descriptions import ComposableNode
from launch_ros.actions import Node

from vision_pipeline.common.image_transport import republisher_parameters


def get_image_proc_nodes(use_intra_process_comms=False):
    """Create resize, rectification, and visualization components per camera."""
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
                "output_qos": "DEFAULT",
                "input_queue_size": 3,
                "output_queue_size": 3,
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
                "output_qos": "DEFAULT",
                "input_queue_size": 3,
                "output_queue_size": 3,
            }],
            remappings=[
                ("image_raw", "resize/image"),
                ("camera_info", "resize/camera_info"),
                ("image_rect", "rect/image"),
                ("camera_info_rect", "rect/camera_info_internal"),
            ],
        ),
        # Low quality compression for visualization over RF comms
        ComposableNode(
            # JPEG compression needs CPU data; DDS materializes CUDA output on the host.
            extra_arguments=[{"use_intra_process_comms": False}],
            package="image_transport",
            plugin="image_transport::Republisher",
            name="vis_compression_node",
            parameters=[
                republisher_parameters("rect/image", "rect/image/compressed"),
                # image_transport uses a leading dot in non-root namespaces.
                {"out.compressed.jpeg_quality": 10, ".out.compressed.jpeg_quality": 10},
            ],
            remappings=[
                ("in", "rect/image"),
                ("out/compressed", "rect/image/compressed"),
            ],
        ),
    ]


def get_rectified_camera_info_node():
    # Isaac may retain the fisheye model with a five-element zero D array.
    # Describe the rectified image as a pinhole camera for downstream clients.
    return Node(
        package="image_processing",
        executable="rectified_camera_info_node",
        name="rectified_camera_info_node",
        output="screen",
    )
