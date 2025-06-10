# Vision Pipeline

Collection of launch files for vision-related nodes.

## Quickstart

Before launching any nodes on the AUV4 Orin, run the following to republish the `CompressedImage` topics from the SBC.

```bash
ros2 launch vision_pipeline orin_cam_repub.launch.py
```

This only has to be done once for multiple launches of image matching or YOLO.

### Image Matching

```bash
ros2 launch vision_pipeline image_matching.launch.py
```

### YOLO

```bash
ros2 launch vision_pipeline gate_yolo.launch.py
```

### Slalom

```bash
ros2 launch vision_pipeline slalom.launch.py
```
#### Issues
**1. LLVM Out of Memory**
**Fix:** Check that the `model_path` parameter for `slalom_depth_anything_node` in `slalom.yaml` is set to the `.onnx` model, not the `.engine` model. The `.engine` is built from the `.onnx` when the node is run for the first time, so on the first run, the model path has to be set to point to the `.onnx` model instead.

## Notes

Each node in `vision_pipeline` subscribes to `Image` and publishes `Image` topics. Additional republishers are added should we need to convert to `CompressedImage` topics for visualization.

### Context for AUV4

Since the cameras are connected to the SBC and not directly to the Orin, we need to pass the camera messages through the network to the Orin. _This is a bad design choice leading to unnecessary network and CPU load as the SBC does not process images at all in the current setup. However, we are constrained by hardware._

To reduce network load, the images are compressed before being passed. However, I think we should not subscribe directly to the `CompressedImage` topics in our image processing and ML nodes because each subscriber to the `CompressedImage` topic would request for messages over the network adding to network load and each subscriber has to decode the compression adding to CPU load. Instead a single `image_transport` republisher converts the `CompressedImage` messages to `Image` messages for each camera stream which the downstream vision nodes subscribe to. **Importantly, all subscribers to the republished `Image` topics reside locally on the Orin.**

## Related Repositories

- [Image matching](https://github.com/BumblebeeAS/image_matching)
- [Image processing](https://github.com/BumblebeeAS/image_processing)
- [Pose estimator](https://github.com/BumblebeeAS/pose_estimator)
- [YOLO ROS TensorRT](https://github.com/bumblebeeas/yolo_ros_trt)
