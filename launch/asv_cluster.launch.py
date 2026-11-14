"""Collect an ASV cluster on demand and retain its GPS position and offset."""

import os
import json
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, UnsetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(get_package_share_directory('vision_pipeline'), 'config', 'uav', 'asv_cluster.yaml')
    bringup_config = os.path.join(os.environ.get('ISAAC_ROS_WS', '/workspaces/isaac_ros-dev'),
                                 'src', 'bring-up', 'etc')
    domain_file = os.path.join(bringup_config, 'vehicle_domains.json')
    asv_domain = 2
    if os.path.isfile(domain_file):
        with open(domain_file, encoding='utf-8') as stream:
            asv_domain = json.load(stream)['asv5']
    dds_env = {
        'RMW_IMPLEMENTATION': 'rmw_fastrtps_cpp',
        'FASTDDS_DEFAULT_PROFILES_FILE': '/etc/ros/dds/fastdds_local.xml',
    }
    bridge_profile = '/etc/ros/dds/asv_input_fastdds.xml'
    return LaunchDescription([
        DeclareLaunchArgument('asv_domain_id', default_value=str(asv_domain),
                              description='ASV source domain from the bring-up vehicle registry'),
        DeclareLaunchArgument('bridge_asv_gps', default_value='true',
                              description='Bridge only ASV GPS from its vehicle domain into the UAV domain'),
        GroupAction([
            # The legacy variable overrides per-node profiles and can load a
            # symlinked profile twice. Scope its removal to these bridge nodes.
            UnsetEnvironmentVariable('FASTRTPS_DEFAULT_PROFILES_FILE'),
            Node(package='bb_localization', executable='asv_gps_domain_bridge.py',
                 output='screen', additional_env=dds_env,
                 arguments=['--source-domain', LaunchConfiguration('asv_domain_id'),
                            '--source-dds-profile', bridge_profile],
                 condition=IfCondition(LaunchConfiguration('bridge_asv_gps'))),
            Node(package='bb_localization', executable='gps_offset.py',
                 name='asv_gps_offset', namespace='/uav/asv', parameters=[config], output='screen',
                 additional_env=dds_env),
        ]),
    ])
