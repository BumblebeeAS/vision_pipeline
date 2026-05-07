from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

from launch import LaunchDescription


def generate_launch_description():
    repub_nodes = []

    for cam_name in ["front_cam", "bot_cam"]:
        cam_container_nodes = [
            # TODO: seems like dont need this compression for viz
            # Lossy compression for visualization
            # (SBC -> Orin is at default 95% quality)
            # ComposableNode(
            #     package="custom_image_republisher",
            #     plugin="custom_image_republisher::Republisher",
            #     name="orin_compression_node",
            #     parameters=[
            #         {
            #             "in_transport": "raw",
            #             "out_transport": "compressed",
            #             ".out.jpeg_quality": 60,
            #         }
            #     ],
            #     namespace=f"auv4/{cam_name}/",
            #     remappings=[
            #         ("in", "color/image"),
            #         ("out/compressed", "color/vis/image/compressed"),
            #     ],
            # ),
        ]

        if cam_name == "front_cam":
            cam_container_nodes.extend(
                [
                    ComposableNode(
                        package="custom_image_republisher",
                        plugin="custom_image_republisher::Rectifier",
                        name="front_cam_rectify_node",
                        namespace=f"auv4/{cam_name}/",
                        remappings=[
                            ("image", "color/image"),
                            ("camera_info", "color/camera_info"),
                            ("image_rect", "color/rect/image"),
                            ("image_rect/compressed", "color/rect/image/compressed"),
                        ],
                    ),
                    # Lossy compression for visualization
                    # (SBC -> Orin is at default 95% quality)
                    # ComposableNode(
                    #     package="custom_image_republisher",
                    #     plugin="custom_image_republisher::Republisher",
                    #     name="front_cam_rectify_compression_node",
                    #     parameters=[
                    #         {
                    #             "in_transport": "raw",
                    #             "out_transport": "compressed",
                    #             ".out.jpeg_quality": 60,
                    #         }
                    #     ],
                    #     namespace=f"auv4/{cam_name}/",
                    #     remappings=[
                    #         ("in", "color/rect/image"),
                    #         ("out/compressed", "color/rect/vis/image/compressed"),
                    #     ],
                    # ),
                ]
            )

        container = ComposableNodeContainer(
            name="orin_repub_container",
            namespace=f"auv4/{cam_name}/",
            package="rclcpp_components",
            executable="component_container",
            composable_node_descriptions=cam_container_nodes,
            output="screen",
        )
        repub_nodes.append(container)

    return LaunchDescription(repub_nodes)
