"""Launch parameters for image_transport republishers."""

from launch.substitutions import LaunchConfiguration, PathJoinSubstitution


def republisher_parameters(input_topic, output_topic):
    """Use sensor-data QoS for both endpoints on their final remapped topics."""
    parameters = {'in_transport': 'raw', 'out_transport': 'compressed'}
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
