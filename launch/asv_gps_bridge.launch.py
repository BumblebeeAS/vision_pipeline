"""Bridge ASV GPS into the UAV domain with discovery isolated per process."""

import json
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, UnsetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    workspace = os.environ.get('ISAAC_ROS_WS', '/workspaces/isaac_ros-dev')
    config = os.path.join(workspace, 'src', 'bring-up', 'etc')
    domains = os.path.join(config, 'vehicle_domains.json')
    asv_domain = 2
    if os.path.isfile(domains):
        with open(domains, encoding='utf-8') as stream:
            asv_domain = json.load(stream)['asv5']
    return LaunchDescription([
        DeclareLaunchArgument('asv_domain_id', default_value=str(asv_domain),
                              description='ASV source domain from the vehicle registry'),
        GroupAction([
            UnsetEnvironmentVariable('FASTRTPS_DEFAULT_PROFILES_FILE'),
            Node(
                package='bb_localization', executable='asv_gps_domain_bridge.py',
                output='screen',
                additional_env={
                    'RMW_IMPLEMENTATION': 'rmw_fastrtps_cpp',
                    'FASTDDS_DEFAULT_PROFILES_FILE': os.path.join(
                        config, 'uav', 'fastdds_local.xml'),
                },
                arguments=[
                    '--source-domain', LaunchConfiguration('asv_domain_id'),
                    '--source-dds-profile', os.path.join(
                        config, 'uav', 'asv_gps_bridge_fastdds.xml'),
                ],
            ),
        ]),
    ])
