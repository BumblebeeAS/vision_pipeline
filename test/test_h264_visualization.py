"""Verify GPU image processing, H.264 decoding, and recovery after dropped frames."""

import os
from pathlib import Path
import signal
import subprocess
import time

import av
from foxglove_msgs.msg import CompressedVideo
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, CompressedImage, Image


def nal_types(data):
    """Read NAL unit types from an Annex B access unit."""
    return [data[i + 3] & 31 for i in range(len(data) - 3)
            if data[i:i + 3] == b'\x00\x00\x01']


def test_h264_visualization_decodes_and_recovers(tmp_path):
    assert os.environ.get('ROS_DOMAIN_ID') in ('224', '225'), 'Use an isolated test domain'
    launch_file = tmp_path / 'h264_test.launch.py'
    launch_file.write_text('''
from launch import LaunchDescription
from launch.actions import GroupAction
from launch_ros.actions import ComposableNodeContainer, PushRosNamespace
from vision_pipeline.common.uav_image_proc import (
    get_foxglove_video_node,
    get_image_proc_nodes,
)

def generate_launch_description():
    return LaunchDescription([GroupAction([
        PushRosNamespace('/h264_test'),
        ComposableNodeContainer(
            name='container', namespace='', package='rclcpp_components',
            executable='component_container_mt', output='screen',
            composable_node_descriptions=get_image_proc_nodes(True, camera_fps=15)),
        get_foxglove_video_node(),
    ])])
''')
    env = dict(os.environ)
    lib = Path('/opt/ros/lyrical/lib')
    env['LD_PRELOAD'] = ' '.join(str(lib / name) for name in (
        'libresize_node.so', 'librectify_node.so', 'libimage_format_converter_node.so'))
    with (tmp_path / 'pipeline.log').open('w') as log:
        process = subprocess.Popen(['ros2', 'launch', str(launch_file)], env=env,
                                   stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        rclpy.init()
        node = Node('h264_visualization_test')
        image_pub = node.create_publisher(Image, '/h264_test/image', qos_profile_sensor_data)
        info_pub = node.create_publisher(CameraInfo, '/h264_test/camera_info',
                                         qos_profile_sensor_data)
        encoded = []
        node.create_subscription(CompressedImage, '/h264_test/rect/image/vis/compressed',
                                 encoded.append, qos_profile_sensor_data)
        packets = []
        node.create_subscription(CompressedVideo, '/h264_test/rect/image/vis/video',
                                 packets.append, 1)
        mono = []
        node.create_subscription(Image, '/h264_test/rect/mono', mono.append,
                                 qos_profile_sensor_data)
        image = np.zeros((720, 1280, 3), dtype=np.uint8)
        image[:, :, 1] = np.arange(1280, dtype=np.uint16)[None, :] % 256
        start = time.monotonic()
        next_frame = start
        frame = 0
        try:
            while time.monotonic() - start < 35 and len(packets) < 45:
                if time.monotonic() >= next_frame:
                    stamp = node.get_clock().now().to_msg()
                    x = (frame * 12) % 1100
                    moving_image = image.copy()
                    moving_image[220:420, x:x + 100] = [255, 40, 80]
                    message = Image(height=720, width=1280, encoding='rgb8', step=3840,
                                    data=moving_image.tobytes())
                    message.header.stamp = stamp
                    message.header.frame_id = 'test_optical'
                    info = CameraInfo(header=message.header, width=1280, height=720,
                                      distortion_model='plumb_bob', d=[0.] * 5,
                                      k=[800., 0., 640., 0., 800., 360., 0., 0., 1.],
                                      r=[1., 0., 0., 0., 1., 0., 0., 0., 1.],
                                      p=[800., 0., 640., 0., 0., 800., 360., 0.,
                                         0., 0., 1., 0.])
                    info_pub.publish(info)
                    image_pub.publish(message)
                    frame += 1
                    next_frame = time.monotonic() + 1 / 15
                rclpy.spin_once(node, timeout_sec=.005)
            assert len(packets) >= 32, (tmp_path / 'pipeline.log').read_text()
            assert mono and (mono[-1].width, mono[-1].height) == (640, 360)
            assert all(m.format == 'h264' and m.frame_id == 'test_optical'
                       for m in packets)
            source = {(m.header.stamp.sec, m.header.stamp.nanosec): m for m in encoded}
            matched = [m for m in packets if (m.timestamp.sec, m.timestamp.nanosec) in source]
            assert len(matched) > 20
            for message in matched:
                original = source[(message.timestamp.sec, message.timestamp.nanosec)]
                assert message.data == original.data
                assert message.frame_id == original.header.frame_id
            keys = [i for i, m in enumerate(packets) if 5 in nal_types(bytes(m.data))]
            assert len(keys) >= 3
            assert max(b - a for a, b in zip(keys, keys[1:])) <= 8
            for i in keys:
                assert {7, 8}.issubset(nal_types(bytes(packets[i].data)))
            decoder = av.CodecContext.create('h264', 'r')
            decoded = [f for m in packets for f in decoder.decode(av.Packet(bytes(m.data)))]
            assert decoded and (decoded[-1].width, decoded[-1].height) == (640, 360)
            # Simulate reconnect/loss: start a fresh decoder at a later recovery frame.
            decoder = av.CodecContext.create('h264', 'r')
            recovered = [f for m in packets[keys[2]:]
                         for f in decoder.decode(av.Packet(bytes(m.data)))]
            assert recovered
            assert len({(m.timestamp.sec, m.timestamp.nanosec) for m in packets}) > 20
        finally:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            node.destroy_node()
            rclpy.shutdown()
