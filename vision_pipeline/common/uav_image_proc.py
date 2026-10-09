# Image proc nodes shared by the UAV GSCam camera pipeline and the UAV sim pipeline.
# These are inserted into the containers defined in their respective launch files
# to take advantage of IPC.

from launch_ros.descriptions import ComposableNode

from vision_pipeline.common.image_transport import republisher_parameters


def get_image_proc_nodes(use_intra_process_comms=False):
    """
    Get image processing composable nodes.

    This must be defined in the function and called within the launch
    context instead of being a static list.

    Returns:
        List of ComposableNode objects
    """
    return [
        # Scale the image and calibration together before rectification.
        ComposableNode(
            extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            name="resize_node",
            package="isaac_ros_image_proc",
            plugin="nvidia::isaac_ros::image_proc::ResizeNode",
            parameters=[
                {"output_width": 640},
                {"output_height": 360},
                {"keep_aspect_ratio": True},
            ],
        ),
        ComposableNode(
            extra_arguments=[{"use_intra_process_comms": use_intra_process_comms}],
            name="rectify_node",
            package="isaac_ros_image_proc",
            plugin="nvidia::isaac_ros::image_proc::RectifyNode",
            parameters=[{"output_height": 360}, {"output_width": 640}],
            remappings=[
                ("image_raw", "resize/image"),
                ("camera_info", "resize/camera_info"),
                ("image_rect", "rect/image"),
                ("camera_info_rect", "rect/camera_info"),
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
