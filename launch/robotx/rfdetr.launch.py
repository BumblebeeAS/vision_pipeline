import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"), "config", "uav", "rfdetr.yaml"
    )
    models = os.path.join(get_package_share_directory("ml_models"), "robotx26")

    return LaunchDescription([
        DeclareLaunchArgument(
            "camera_name", default_value="wide_a",
            description="UAV camera namespace: wide_a or narrow_a",
        ),
        DeclareLaunchArgument(
            "model_path", default_value=os.path.join(
                models, "uav_segment", "rfdetr_seg_nano_20261114_0", "weights_fp16.trt"
            ),
        ),
        DeclareLaunchArgument(
            "color_model_path", default_value=os.path.join(
                models, "buoy_color", "mobilenet_v3_small_20261114_1", "classifier_pipeline_fp32.trt"
            ),
        ),
        PushRosNamespace(["/uav/", LaunchConfiguration("camera_name")]),
        Node(
            package="yolo_ros_trt",
            executable="rfdetr_node",
            name="rfdetr_node",
            parameters=[config, {"model_path": LaunchConfiguration("model_path")}],
            output="screen",
        ),
        Node(
            package="yolo_ros_trt",
            executable="classifier_node",
            name="classifier_node",
            parameters=[config, {"model_path": LaunchConfiguration("color_model_path")}],
            output="screen",
        ),
        Node(
            package="pose_estimator",
            executable="buoy_pose_estimator_node",
            name="buoy_pose_estimator_node",
            parameters=[config],
            output="screen",
        ),
    ])
