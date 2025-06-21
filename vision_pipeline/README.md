# Vision Pipeline Nodes

## Component Manager

Calling the service of type `std_srvs/srv/SetBool` with value `true` loads all nodes into the `component_container`. This is equivalent to calling `<container_name>/_container/list_nodes` and then calling `<container_name>/_container/load_node` for each node supplied in `node_names` **not already loaded**:

### CLI Commands

For debugging, the corresponding CLI commands are listed here (with example parameters).

#### Load node

```bash
ros2 service call /ComponentManager/_container/load_node composition_interfaces/srv/LoadNode "package_name: 'depth_anything_ros2_trt'
plugin_name: 'depth_anything::DepthAnythingNode'
node_name: 'depth_anything_node'
node_namespace: ''
log_level: 0
remap_rules: []
parameters: [ { name: 'model_path', value: { type: 4, string_value: '/workspaces/isaac_ros-dev/src/ml_models/depth_anything/depth_anything_v2_vitb_770.engine' } } ]
extra_arguments: []"
```

#### List nodes

```bash
ros2 service call /ComponentManager/_container/list_nodes composition_interfaces/srv/ListNodes {}
```

#### Unload node

```bash
ros2 service call /ComponentManager/_container/unload_node composition_interfaces/srv/UnloadNode "unique_id: 0"
```
