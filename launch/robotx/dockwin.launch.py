import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode, Node, PushRosNamespace


def generate_launch_description():
	dock_config = os.path.join(
		get_package_share_directory("vision_pipeline"),
		"config",
		"asv5",
		"dock.yaml",
	)
	dockwin_config = os.path.join(
		get_package_share_directory("vision_pipeline"),
		"config",
		"asv5",
		"dockwin.yaml",
	)

	enable_decoder_arg = DeclareLaunchArgument(
		"enable_decoder",
		default_value="false",
		description="Whether to run the dockwin sequence decoder node",
	)

	# Dock approach vision (previously dock.launch.py). The lifecycle manager
	# exposes /asv5/dock/manage_nodes, which the dock behaviour tree starts; the
	# LED YOLO publishes /asv5/dock_led/yolo/detections for it to consume.
	dock_vision_nodes = [
		PushRosNamespace("/asv5/dock"),
		LifecycleNode(
			package="yolo_ros_trt",
			executable="yolo_node",
			name="dock_beacon_yolo_node",
			namespace="",
			parameters=[dock_config],
		),
		Node(
			package="vision_pipeline",
			executable="lifecycle_manager_node",
			name="lifecycle_manager_node",
			output="screen",
			parameters=[dock_config],
		),
	]

	dockwin_nodes = [
		PushRosNamespace("/asv5/dockwin"),
		Node(
			package="yolo_ros_trt",
			executable="yolo_node",
			name="dockwin_yolo_node",
			parameters=[dockwin_config],
		),
		Node(
			package="pose_estimator",
			executable="dockwin_pose_estimator_node",
			name="dockwin_pose_estimator_node",
			parameters=[dockwin_config],
		),
		Node(
			package="dockwin_sequence_decoder",
			executable="dockwin_sequence_decoder_node",
			name="dockwin_sequence_decoder_node",
			parameters=[dockwin_config],
			condition=IfCondition(LaunchConfiguration("enable_decoder")),
		),
		Node(
			package="vision_pipeline",
			executable="lifecycle_manager_node",
			name="lifecycle_manager_node",
			output="screen",
			parameters=[dockwin_config],
		),
	]

	# Dock pose from the lidar BEV, published to /asv5/dock/pose which the dock
	# tree clusters. ``use_sim`` selects the RX26 sim template/dock dimensions.
	dock_lidar_pose_estimator = Node(
		package="pose_estimator",
		executable="dock_lidar_pose_estimator_node",
		name="dock_lidar_pose_estimator_node",
		namespace="/asv5",
		output="screen",
		parameters=[{"use_sim": True}],
	)

	return LaunchDescription(
		[enable_decoder_arg]
		+ dock_vision_nodes
		+ dockwin_nodes
		+ [dock_lidar_pose_estimator]
	)


if __name__ == "__main__":
	generate_launch_description()
