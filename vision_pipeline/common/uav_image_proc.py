# Image proc nodes shared by the UAV Argus camera pipeline and the UAV sim pipeline.
# These are inserted into the containers defined in their respective launch files
# to take advantage of IPC.

from launch_ros.descriptions import ComposableNode


def get_image_proc_nodes():
    """
    Get image processing composable nodes.

    This must be defined in the function and called within the launch
    context instead of being a static list.

    Returns:
        List of ComposableNode objects
    """
    return [
        # ComposableNode(
        #     name="resize_node",
        #     package="isaac_ros_image_proc",
        #     plugin="nvidia::isaac_ros::image_proc::ResizeNode",
        #     parameters=[
        #         {"input_width": 1280},
        #         {"input_height": 720},
        #         {"output_width": 640},
        #         {"output_height": 360},
        #         {"keep_aspect_ratio": True},
        #     ],
        # ),
        ComposableNode(
            name="rectify_node",
            package="isaac_ros_image_proc",
            plugin="nvidia::isaac_ros::image_proc::RectifyNode",
            parameters=[{"output_height": 360}, {"output_width": 640}],
            remappings=[
                ("image_raw", "image"),
                ("image_rect", "rect/image"),
                ("camera_info_rect", "rect/camera_info"),
            ],
        ),
        # # High quality compression for bagging
        # ComposableNode(
        #     package="custom_image_republisher",
        #     plugin="custom_image_republisher::Republisher",
        #     name="orin_compression_node",
        #     parameters=[{"in_transport": "raw", "out_transport": "compressed"}],
        #     remappings=[
        #         ("in", "rect/image"),
        #         ("out/compressed", "rect/image/compressed"),
        #     ],
        # ),
        # Low quality compression for visualization over RF comms
        ComposableNode(
            package="custom_image_republisher",
            plugin="custom_image_republisher::Republisher",
            name="vis_compression_node",
            parameters=[
                {
                    "in_transport": "raw",
                    "out_transport": "compressed",
                    ".out.jpeg_quality": 10,
                }
            ],
            remappings=[
                ("in", "rect/image"),
                ("out/compressed", "rect/image/compressed"),
            ],
        ),
    ]
