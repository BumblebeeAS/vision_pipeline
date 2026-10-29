import os

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    OpaqueFunction,
    UnsetEnvironmentVariable,
)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

from vision_pipeline.common.uav_image_proc import (
    get_image_proc_nodes,
    get_rectified_camera_info_node,
)


def evaluate_launch(context, *args, **kwargs):
    camera_name = LaunchConfiguration("camera_name").perform(context)
    camera_id = LaunchConfiguration("camera_id").perform(context)
    camera_mode = LaunchConfiguration("camera_mode").perform(context)
    camera_frame_id = LaunchConfiguration("camera_frame_id").perform(context)

    config_dir = os.path.join(
        get_package_share_directory("vision_pipeline"), "config", "uav"
    )
    calibration_data_file = os.path.join(config_dir, "calib", f"{camera_name}.yaml")
    gscam_config = (
        f"nvarguscamerasrc sensor-id={int(camera_id)} "
        f"sensor-mode={int(camera_mode)} do-timestamp=true ! "
        "video/x-raw(memory:NVMM),width=1280,height=720,format=NV12,framerate=30/1 ! "
        "nvvidconv ! video/x-raw,format=BGRx ! "
        "videoconvert ! video/x-raw,format=RGB"
    )
    # Prepare the full processing chain before GSCam starts producing frames.
    cam_container_nodes = [
        *get_image_proc_nodes(use_intra_process_comms=True),
        ComposableNode(
            name="gscam",
            package="gscam",
            plugin="gscam::GSCam",
            parameters=[{
                "gscam_config": gscam_config,
                "camera_name": camera_name,
                "frame_id": camera_frame_id,
                "camera_info_url": f"file://{calibration_data_file}",
                "image_encoding": "rgb8",
                "sync_sink": False,
                "use_gst_timestamps": True,
                "use_sensor_data_qos": True,
            }],
            remappings=[
                ("camera/image_raw", "image"),
                ("camera/camera_info", "camera_info"),
            ],
            extra_arguments=[{"use_intra_process_comms": True}],
        ),
    ]
    lib_dir = os.path.join(get_package_prefix("isaac_ros_image_proc"), "lib")
    camera_env = {
        # Allow more time for component-loading service replies.
        "FASTDDS_DEFAULT_PROFILES_FILE": os.path.join(
            get_package_share_directory("vision_pipeline"),
            "config", "uav", "camera_fastdds.xml",
        ),
        # CUDA IPC dispatcher threads outlive component dlclose in Isaac ROS 5.0.
        # Keep their code mapped until process exit.
        "LD_PRELOAD": " ".join(filter(None, [
            os.path.join(lib_dir, "libresize_node.so"),
            os.path.join(lib_dir, "librectify_node.so"),
            os.environ.get("LD_PRELOAD", ""),
        ])),
    }
    camera_container = ComposableNodeContainer(
        name="camera_container",
        package="rclcpp_components",
        executable="component_container_mt",
        composable_node_descriptions=cam_container_nodes,
        namespace="",
        output="screen",
        additional_env=camera_env,
        arguments=["--ros-args", "--log-level", "info"],
    )

    # EGL needs DISPLAY absent, not empty, for headless CSI capture.
    return [GroupAction([
        UnsetEnvironmentVariable("DISPLAY"),
        camera_container,
        get_rectified_camera_info_node(),
    ])]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("camera_name", default_value=""),
            DeclareLaunchArgument("camera_id", default_value="-1"),
            DeclareLaunchArgument("camera_mode", default_value="4"),
            DeclareLaunchArgument("camera_frame_id", default_value=""),
            OpaqueFunction(function=evaluate_launch),
        ]
    )


if __name__ == "__main__":
    generate_launch_description()
