# Vision Pipeline

Collection of launch files and utilities for vision-related nodes.

## Quickstart

Before launching any nodes on the AUV4 Orin, run the following to republish the `CompressedImage` topics from the SBC.

```bash
ros2 launch vision_pipeline orin_cam_repub.launch.py
```

This only has to be done once for multiple launches of vision-related launch files.

Launch any other file in `launch`, for example:

```bash
ros2 launch vision_pipeline image_matching.launch.py
```

You can edit the corresponding launch configuration YAML file in `config`. Note that specifying remap rules in YAML files is not supported in ROS as of 22 Jun 2025. These have to be changed in the launch files themselves.

Most launch files do not start all nodes activated by default:

- For **lifecycle nodes** (e.g., YOLO), call the _namespaced_ `manage_nodes` service to activate / deactivate.
- For **components** (e.g., depth anything), call the _namespaced_ `manage_components` service to load / unload.
- For **image matching**, call the _namespaced_ `image_matching/toggle_template` service to enable / disable.

Launch files may not have all the above node types and thus some services may not be present.

See [vision_pipeline/README.md](vision_pipeline/README.md) for more details.

## Issues

**1. LLVM Out of Memory**

**Fix:** Check that the `model_path` parameter for `slalom_depth_anything_node` in `slalom.yaml` is set to the `.onnx` model, not the `.engine` model. The `.engine` is built from the `.onnx` when the node is run for the first time, so on the first run, the model path has to be set to point to the `.onnx` model instead.

## Notes

### Image Types

Each node in `vision_pipeline` subscribes to `Image` and publishes `Image` topics. Additional republishers are added should we need to convert to `CompressedImage` topics for visualization.

#### Context for AUV4

Since the cameras are connected to the SBC and not directly to the Orin, we need to pass the camera messages through the network to the Orin. _This is a bad design choice leading to unnecessary network and CPU load as the SBC does not process images at all in the current setup. However, we are constrained by hardware._

To reduce network load, the images are compressed before being passed. However, I think we should not subscribe directly to the `CompressedImage` topics in our image processing and ML nodes because each subscriber to the `CompressedImage` topic would request for messages over the network adding to network load and each subscriber has to decode the compression adding to CPU load. Instead a single `image_transport` republisher converts the `CompressedImage` messages to `Image` messages for each camera stream which the downstream vision nodes subscribe to. **Importantly, all subscribers to the republished `Image` topics reside locally on the Orin.**

## Related Repositories

- [Depth Anything ROS2 TensorRT](https://github.com/BumblebeeAS/depth_anything_ros2_trt)
- [Image matching](https://github.com/BumblebeeAS/image_matching)
- [Image processing](https://github.com/BumblebeeAS/image_processing)
- [Pose estimator](https://github.com/BumblebeeAS/pose_estimator)
- [YOLO ROS TensorRT](https://github.com/bumblebeeas/yolo_ros_trt)
