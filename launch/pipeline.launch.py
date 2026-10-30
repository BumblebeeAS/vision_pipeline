import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode, Node, PushRosNamespace


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("vision_pipeline"),
        "config",
        "auv5",
        "pipeline.yaml",
    )

    launch_objects = [PushRosNamespace("/auv5/pipeline")]

    pipeline_nodes = [
        Node(
            package="yolo_ros_trt",
            executable="yolo_node",
            name="sonar_yolo_node",
            parameters=[config],
        ),
        Node(
            package="vision_pipeline",
            executable="lifecycle_manager_node",
            name="sonar_lifecycle_manager_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="sonar_pipe_pose_estimator_node",
            name="sonar_pipe_pose_estimator_node",
            parameters=[config],
        ),
        Node(
            package="pose_estimator",
            executable="sonar_pipe_trace_node",
            name="sonar_pipe_trace_node",
            parameters=[config],
        ),
    ]

    # Bottom-camera pipe following. The camera model gets its own lifecycle
    # manager so the mission can run sonar (sweep/centre) and camera (follow)
    # models one at a time; its manage_nodes service is remapped to
    # /auv5/pipeline/cam/manage_nodes so it does not clash with the sonar
    # manager's /auv5/pipeline/manage_nodes.
    camera_nodes = [
        LifecycleNode(
            package="yolo_ros_trt",
            executable="yolo_node",
            name="pipe_yolo_node",
            parameters=[config],
            namespace="",
        ),
        Node(
            package="vision_pipeline",
            executable="lifecycle_manager_node",
            name="pipe_lifecycle_manager_node",
            parameters=[config],
            remappings=[("manage_nodes", "cam/manage_nodes")],
        ),
        Node(
            package="pipeline_vision_tracker",
            executable="pipeline_projection_node",
            name="pipeline_projection_node",
            parameters=[config],
        ),
        # Action server /auv5/pipeline/follow (node-relative name "follow").
        Node(
            package="pipeline_vision_tracker",
            executable="pipeline_follow_node",
            name="pipeline_follow_node",
            parameters=[config],
            output="screen",
        ),
    ]

    # Bottom-camera red light box, run only on the follow leg after the
    # end-of-pipe turn. Own lifecycle manager, remapped to
    # /auv5/pipeline/light_box/manage_nodes, so the pipe model can run alone.
    # tracking_node (ByteTrack) fills Detection.id so the mission can count
    # distinct green light boxes.
    light_box_nodes = [
        LifecycleNode(
            package="yolo_ros_trt",
            executable="tracking_node",
            name="light_box_yolo_node",
            parameters=[config],
            namespace="",
        ),
        Node(
            package="vision_pipeline",
            executable="lifecycle_manager_node",
            name="light_box_lifecycle_manager_node",
            parameters=[config],
            remappings=[("manage_nodes", "light_box/manage_nodes")],
        ),
        Node(
            package="pose_estimator",
            executable="light_box_pose_estimator_node",
            name="light_box_pose_estimator_node",
            parameters=[config],
        ),
        # Multi-view light box position (world-fixed, odom frame) from mask
        # centroid rays gathered while the vehicle moves; publishes
        # /auv5/pipeline/light_box/triangulated/pose (PoseArray). Only sees
        # rays while a light box model is active. ~/reset clears its tracks.
        # Node(
        #     package="pose_estimator",
        #     executable="light_box_triangulation_pose_estimator_node",
        #     name="light_box_triangulation_pose_estimator_node",
        #     parameters=[config],
        # ),
        # Idle until the mission calls ~/start_decoding after the dock.
        # Node(
        #     package="rx_light_sequence_decoder",
        #     executable="lightbox_sequence_decoder_node",
        #     name="lightbox_sequence_decoder_node",
        #     parameters=[config],
        # ),
        # Classical (no-YOLO) alternative to light_box_yolo_node: publishes the
        # same red/green/blue_faceplate detections on the same topic. Toggled
        # by its own manager at /auv5/pipeline/light_box_classical/manage_nodes;
        # activate only one of the two.
        # LifecycleNode(
        #     package="pose_estimator",
        #     executable="light_box_classical_node",
        #     name="light_box_classical_node",
        #     parameters=[config],
        #     namespace="",
        # ),
        # Node(
        #     package="vision_pipeline",
        #     executable="lifecycle_manager_node",
        #     name="light_box_classical_lifecycle_manager_node",
        #     parameters=[config],
        #     remappings=[("manage_nodes", "light_box_classical/manage_nodes")],
        # ),
    ]

    vis_nodes = []

    return LaunchDescription(
        launch_objects + pipeline_nodes + camera_nodes + light_box_nodes + vis_nodes
    )
