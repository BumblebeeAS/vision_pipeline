"""Launch parameters for image_transport republishers."""

from launch.substitutions import LaunchConfiguration, PathJoinSubstitution


def republisher_parameters(input_topic, output_topic):
    """Preserve sensor-data QoS on the final remapped input and output topics.

    Relative topics follow PushRosNamespace, including camera_name substitutions.
    Pass the actual transport topic (e.g. image/compressed) for the output.
    Nodes using these parameters must inherit the current launch namespace.
    """
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
