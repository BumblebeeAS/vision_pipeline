"""On-demand ASV capture: fresh collection, frozen output, retries and cancellation."""

from copy import deepcopy
import time
from unittest.mock import Mock

import pytest
import rclpy
from action_msgs.msg import GoalStatus
from bb_perception_msgs.action import ClusterPosesAction
from geographic_msgs.msg import GeoPointStamped
from geometry_msgs.msg import PoseStamped, TransformStamped, Vector3Stamped
from nav_msgs.msg import Odometry
from pygeodesy.ltp import LocalCartesian
from px4_msgs.msg import VehicleGlobalPosition
from rclpy.action import ActionClient
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from sensor_msgs.msg import NavSatFix
from tf2_ros import StaticTransformBroadcaster

from bb_localization.gps_offset import GpsOffset


def test_on_demand_capture_lifecycle():
    rclpy.init(args=['--ros-args', '-r', '__ns:=/uav/asv'])
    node = GpsOffset()
    source = Node('synthetic_asv_sources')
    executor = SingleThreadedExecutor()
    for item in (node, source):
        executor.add_node(item)
    client = ActionClient(source, ClusterPosesAction, '/uav/asv/capture_gps_offset')
    odom_pub = source.create_publisher(Odometry, '/uav/odom_ned', 10)
    pose_pubs = [source.create_publisher(PoseStamped, f'/uav/{camera}/asv/pose', 10)
                 for camera in ('wide_a', 'narrow_a')]
    ref_pub = source.create_publisher(GeoPointStamped, '/uav/home_lat_lon', 10)
    global_pub = source.create_publisher(VehicleGlobalPosition, '/fmu/out/vehicle_global_position', 10)
    gps_pub = source.create_publisher(NavSatFix, '/asv5/gps', 10)
    received, gps_received = [], []
    source.create_subscription(Vector3Stamped, '/uav/asv/gps_offset', received.append, 10)
    source.create_subscription(NavSatFix, '/uav/asv/clustered/gps', gps_received.append, 10)
    broadcaster = StaticTransformBroadcaster(source)
    transforms = []
    for camera, x in [('wide', 1.), ('narrow', -1.)]:
        tf = TransformStamped()
        tf.header.frame_id, tf.child_frame_id = 'body', camera
        tf.transform.translation.x = x
        tf.transform.rotation.w = 1.
        transforms.append(tf)
    broadcaster.sendTransform(transforms)
    state = {'counter': 0, 'gps': True, 'poses': True, 'east': 9.}
    feedback = []

    def publish():
        stamp = source.get_clock().now().to_msg()
        reference = GeoPointStamped()
        reference.position.latitude, reference.position.longitude = 1.3, 103.8
        reference.position.altitude = 10.
        ref_pub.publish(reference)
        global_pub.publish(VehicleGlobalPosition(timestamp=1, alt_valid=True, alt=20., alt_ellipsoid=26.))
        odom = Odometry()
        odom.header.frame_id, odom.header.stamp = 'odom_ned', stamp
        odom.child_frame_id = 'body'
        odom.pose.pose.position.x = 10.
        odom.pose.pose.orientation.w = 1.
        odom_pub.publish(odom)
        if state['poses']:
            for pub, camera, x in zip(pose_pubs, ['wide', 'narrow'], [2., 4.]):
                pose = PoseStamped()
                pose.header.frame_id, pose.header.stamp = camera, stamp
                pose.pose.position.x = x + (state['counter'] % 7) * .0001
                pose.pose.position.y = 2.
                pose.pose.orientation.w = 1.
                pub.publish(pose)
        if state['gps']:
            actual = LocalCartesian(1.3, 103.8, 16.).reverse(state['east'], 23., 1.)
            fix = NavSatFix(latitude=actual.lat, longitude=actual.lon, altitude=actual.height)
            fix.status.status = 0
            fix.header.stamp = stamp
            gps_pub.publish(fix)
        state['counter'] += 1

    timer = source.create_timer(.03, publish)
    node._run_clustering = Mock(wraps=node._run_clustering)

    def spin_until(predicate, timeout=8.):
        deadline = time.monotonic() + timeout
        while not predicate() and time.monotonic() < deadline:
            executor.spin_once(timeout_sec=.03)
        assert predicate()

    def start(duration=.8):
        future = client.send_goal_async(ClusterPosesAction.Goal(collection_duration=duration),
                                        feedback_callback=lambda message: feedback.append(message.feedback))
        spin_until(future.done)
        return future.result()

    def finish(handle):
        future = handle.get_result_async()
        spin_until(future.done)
        return future.result()

    def idle():
        assert node._odom_subscriber is None and not node._pose_subscribers
        assert node.actual_sub is None and not node._stream_data
        assert node._action_timer.is_canceled()

    try:
        assert client.wait_for_server(timeout_sec=3.)
        idle()
        spin_until(lambda: node.converter is not None)
        assert not received and not gps_received
        assert node._run_clustering.call_count == 0
        assert not start(float('nan')).accepted
        handle = start()
        assert handle.accepted
        assert not start().accepted  # another capture cannot overwrite active state
        result = finish(handle)
        assert result.status == GoalStatus.STATUS_SUCCEEDED
        assert len(result.result.cluster_results.results) == 1
        idle()
        assert node._run_clustering.call_count == 1
        spin_until(lambda: bool(received) and bool(gps_received))
        frozen = deepcopy(node.frozen)
        assert (frozen.vector.x, frozen.vector.y, frozen.vector.z) == pytest.approx((7., 10., 1.), abs=.01)
        assert node.snapshot[0].pose.position.x == pytest.approx(13., abs=.01)
        assert frozen.header.stamp == node.snapshot[1].header.stamp

        # New live observations cannot change a frozen capture or trigger clustering.
        state['east'] = 19.
        before = len(received)
        spin_until(lambda: len(received) > before, timeout=3.)
        assert received[-1] == frozen
        assert node._run_clustering.call_count == 1
        late = []
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        source.create_subscription(Vector3Stamped, '/uav/asv/gps_offset', late.append, qos)
        spin_until(lambda: bool(late))
        assert late[0] == frozen

        assert finish(start()).status == GoalStatus.STATUS_SUCCEEDED
        idle()
        assert node.frozen.vector.x == pytest.approx(17., abs=.01)
        frozen = deepcopy(node.frozen)
        # A fresh collection with no ASV GPS must abort and keep the old capture.
        state['gps'] = False
        assert finish(start()).status == GoalStatus.STATUS_ABORTED
        idle()
        assert node.frozen == frozen
        spin_until(lambda: any('No fresh valid ASV GPS on /asv5/gps' in item.current_status
                               for item in feedback))
        # Cancellation cleans subscriptions and does not cluster or commit.
        handle = start(5.)
        spin_until(lambda: node.actual_sub is not None)
        calls = node._run_clustering.call_count
        future = handle.cancel_goal_async()
        spin_until(future.done)
        assert future.result().goals_canceling
        assert finish(handle).status == GoalStatus.STATUS_CANCELED
        idle()
        assert node._run_clustering.call_count == calls and node.frozen == frozen
        state['gps'], state['poses'] = True, False
        assert finish(start()).status == GoalStatus.STATUS_ABORTED
        idle()
        assert node.frozen == frozen
    finally:
        timer.cancel()
        executor.shutdown()
        client.destroy()
        for item in (source, node):
            item.destroy_node()
        rclpy.shutdown()


def test_installed_launch_starts_idle_action():
    import os
    import signal
    import subprocess
    from rcl_interfaces.srv import GetParameters

    process = subprocess.Popen(
        ['ros2', 'launch', 'vision_pipeline', 'asv_cluster.launch.py', 'bridge_asv_gps:=false'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    rclpy.init()
    probe = Node('asv_launch_probe')
    client = ActionClient(probe, ClusterPosesAction, '/uav/asv/capture_gps_offset')
    try:
        assert client.wait_for_server(timeout_sec=15.)
        params = probe.create_client(GetParameters, '/uav/asv/asv_gps_offset/get_parameters')
        assert params.wait_for_service(timeout_sec=15.)
        future = params.call_async(GetParameters.Request(names=['local_frame']))
        rclpy.spin_until_future_complete(probe, future, timeout_sec=5.)
        assert future.result().values[0].string_value == 'odom_ned'
        assert process.poll() is None
        # Startup is idle: no camera subscriptions, no previous Trigger service.
        assert not probe.get_subscriptions_info_by_topic('/uav/wide_a/asv/pose')
        assert '/uav/asv/capture_gps_offset' not in dict(probe.get_service_names_and_types())
    finally:
        os.killpg(process.pid, signal.SIGINT)
        try:
            output, _ = process.communicate(timeout=10.)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            output, _ = process.communicate()
        print(output)
        client.destroy()
        probe.destroy_node()
        rclpy.shutdown()
