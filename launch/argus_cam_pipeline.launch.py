import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def evaluate_launch(context, *args, **kwargs):
    camera_name = LaunchConfiguration("camera_name").perform(context)
    camera_id = LaunchConfiguration("camera_id").perform(context)
    camera_mode = LaunchConfiguration("camera_mode").perform(context)
    camera_frame_id = LaunchConfiguration("camera_frame_id").perform(context)
    camera_link_frame_name = LaunchConfiguration("camera_link_frame_name").perform(
        context
    )

    namespace = f"drone/{camera_name}"
    calibration_data_file = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "drone",
        "calib",
        f"{camera_name}.yaml",
    )

    cam_container_nodes = [
        ComposableNode(
            name="argus_mono",
            package="isaac_ros_argus_camera",
            plugin="nvidia::isaac_ros::argus::ArgusMonoNode",
            parameters=[
                {"camera_id": int(camera_id)},
                {"mode": int(camera_mode)},
                {"optical_frame_name": camera_frame_id},
                {"camera_link_frame_name": camera_link_frame_name},
                {"camera_info_url": f"file://{calibration_data_file}"},
            ],
            remappings=[("left/image_raw", "image")],
            namespace=namespace,
        ),
        # ComposableNode(
        #     name="rectify_node",
        #     package="isaac_ros_image_proc",
        #     plugin="nvidia::isaac_ros::image_proc::RectifyNode",
        #     parameters=[{"output_height": 480}, {"output_width": 640}],
        #     namespace=namespace,
        #     remappings=[("image_rect", "rect/image")],
        # ),
        ComposableNode(
            package="custom_image_republisher",
            plugin="custom_image_republisher::Republisher",
            name="orin_compression_node",
            parameters=[{"in_transport": "raw", "out_transport": "compressed"}],
            namespace=namespace,
            remappings=[
                ("in", "image"),
                ("out/compressed", "image/compressed"),
            ],
        ),
    ]

    camera_container = ComposableNodeContainer(
        name="camera_container",
        package="rclcpp_components",
        executable="component_container_mt",
        composable_node_descriptions=cam_container_nodes,
        namespace=camera_name,
        output="screen",
        arguments=["--ros-args", "--log-level", "info"],
    )

    return [camera_container]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("camera_name", default_value=""),
            DeclareLaunchArgument("camera_id", default_value="-1"),
            DeclareLaunchArgument("camera_mode", default_value="4"),
            DeclareLaunchArgument("camera_frame_id", default_value=""),
            DeclareLaunchArgument("camera_link_frame_name", default_value=""),
            OpaqueFunction(function=evaluate_launch),
        ]
    )


if __name__ == "__main__":
    generate_launch_description()
