"""Launch parameters for image_transport republishers."""

from vision_pipeline.common.qos import sensor_data_qos_parameters


def republisher_parameters(input_topic, output_topic):
    """Use sensor-data QoS for both endpoints on their final remapped topics."""
    return {
        'in_transport': 'raw',
        'out_transport': 'compressed',
        **sensor_data_qos_parameters(input_topic, output_topic),
    }
