"""Launch parameters for sensor-data QoS overrides."""

from launch.substitutions import LaunchConfiguration, PathJoinSubstitution


def sensor_data_qos_parameters(input_topic, output_topic):
    """Configure both endpoints using their final remapped topic names."""
    parameters = {}
    for topic, endpoint in ((input_topic, 'subscription'), (output_topic, 'publisher')):
        resolved_topic = PathJoinSubstitution([
            LaunchConfiguration('ros_namespace', default='/'), topic,
        ])
        for policy, value in {
            'reliability': 'best_effort',
            'durability': 'volatile',
            'history': 'keep_last',
            'depth': 5,
        }.items():
            parameters[('qos_overrides.', resolved_topic, f'.{endpoint}.{policy}')] = value
    return parameters
