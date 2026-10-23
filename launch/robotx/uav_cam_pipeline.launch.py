import math
import os

import yaml

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

from vision_pipeline.common.color_shading import color_shading_filter
from vision_pipeline.common.uav_image_proc import (
    get_image_proc_nodes,
    get_rectified_camera_info_node,
)


def evaluate_launch(context, *args, **kwargs):
    camera_name = LaunchConfiguration("camera_name").perform(context)
    camera_id = LaunchConfiguration("camera_id").perform(context)
    camera_mode = LaunchConfiguration("camera_mode").perform(context)
    camera_frame_id = LaunchConfiguration("camera_frame_id").perform(context)

    calibration_data_file = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "uav",
        "calib",
        f"{camera_name}.yaml",
    )

    color_config_path = os.environ.get(
        "UAV_CAMERA_COLOR_CONFIG", "/etc/ros/uav/camera_color.yaml"
    )
    with open(color_config_path) as camera_config_file:
        camera_config = yaml.safe_load(camera_config_file)
    rgb_gains = camera_config.get("color_balance_rgb", {}).get(camera_name)
    shading = camera_config.get("color_shading", {}).get(camera_name)
    color_format = "RGBA" if rgb_gains is not None or shading is not None else "BGRx"
    color_conversion = f"nvvidconv ! video/x-raw,format={color_format} ! "
    if rgb_gains is not None:
        if len(rgb_gains) != 3 or any(
            not math.isfinite(float(gain)) or not 0.3333 <= float(gain) <= 3.0
            for gain in rgb_gains
        ):
            raise ValueError(f"Expected three RGB gains between 0.3333 and 3 for {camera_name}")
        # frei0r's multiply controls map 0..1 logarithmically to 0.3333..3.
        controls = [
            math.log(float(gain) / 0.3333) / math.log(3.0 / 0.3333)
            for gain in rgb_gains
        ]
        color_conversion += (
            "frei0r-filter-coloradj-rgb action=1 keep-luma=false "
            f"r={controls[0]:.8f} g={controls[1]:.8f} b={controls[2]:.8f} ! "
        )
    if shading is not None:
        color_conversion += color_shading_filter(shading)

    gscam_config = (
        f"nvarguscamerasrc sensor-id={int(camera_id)} "
        f"sensor-mode={int(camera_mode)} do-timestamp=true ! "
        "video/x-raw(memory:NVMM),width=1280,height=720,format=NV12,framerate=30/1 ! "
        f"{color_conversion}"
        "videoconvert ! video/x-raw,format=RGB"
    )
    cam_container_nodes = [
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
                "use_sensor_data_qos": False,
            }],
            remappings=[
                ("camera/image_raw", "image"),
                ("camera/camera_info", "camera_info"),
            ],
            extra_arguments=[{"use_intra_process_comms": True}],
        ),
    ]
    cam_container_nodes.extend(get_image_proc_nodes(use_intra_process_comms=True))
    # CUDA IPC dispatcher threads outlive component dlclose in Isaac ROS 5.0.
    # Keep their code mapped until process exit.
    lib_dir = os.path.join(get_package_prefix("isaac_ros_image_proc"), "lib")
    camera_env = {
        # Avoid service response timeouts while loading camera components.
        "RMW_FASTRTPS_PUBLICATION_MODE": "ASYNCHRONOUS",
        "LD_PRELOAD": " ".join(filter(None, [
            os.path.join(lib_dir, "libresize_node.so"),
            os.path.join(lib_dir, "librectify_node.so"),
            os.environ.get("LD_PRELOAD", ""),
        ])),
    }
    if shading is not None:
        camera_env.update({
            "GST_GL_WINDOW": "surfaceless",
            "GST_GL_PLATFORM": "egl",
            "GST_GL_API": "gles2",
        })

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
