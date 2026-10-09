import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import PushRosNamespace
from launch_ros.substitutions import FindPackageShare

config_file = os.path.join(
    get_package_share_directory("vision_pipeline"),
    "config",
    "uav",
    "cameras.yaml",
)
with open(config_file, "r") as f:
    config = yaml.safe_load(f)
    camera_names = config["camera_names"]
    camera_mode = config["camera_mode"]


def generate_launch_description():
    pipeline_groups = []

    for camera_id, camera_name in enumerate(camera_names):
        pipeline_groups.append(
            GroupAction(
                actions=[
                    PushRosNamespace(camera_name),
                    IncludeLaunchDescription(
                        PythonLaunchDescriptionSource(
                            [
                                FindPackageShare("vision_pipeline"),
                                "/launch/uav_cam_pipeline.launch.py",
                            ]
                        ),
                        launch_arguments={
                            "camera_name": camera_name,
                            "camera_id": str(camera_id),
                            "camera_mode": str(camera_mode),
                            "camera_frame_id": f"uav/{camera_name}_optical",
                        }.items(),
                    ),
                ]
            )
        )

    return LaunchDescription([PushRosNamespace("uav")] + pipeline_groups)


if __name__ == "__main__":
    generate_launch_description()
