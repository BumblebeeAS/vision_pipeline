# Vision Pipeline Nodes

## Component Manager

Calling the _namespaced_ `manage_components` service of type `std_srvs/srv/SetBool` with value `true` loads all nodes into the `component_container`. This is equivalent to calling `<container_name>/_container/list_nodes` and then calling `<container_name>/_container/load_node` for each node supplied in `node_names` **not already loaded**. Calling with `false` lists all nodes and calls `<container_name>/_container/unload_node` for each node supplied in `node_names` in the container.

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

## Lifecycle Manager

The [Nav2 Lifecycle Manager](https://docs.nav2.org/configuration/packages/configuring-lifecycle.html) is meant to support `LifecycleNode` in `nav2_util`. While it is possible to make it work by setting `bond_timeout` to `0.0`, it kills node process(es) when trying to transition to invalid states. We create our own Lifecycle Manager to support normal ROS 2 Lifecycle Nodes and handle invalid states.

Calling the _namespaced_ `manage_nodes` service of type `lifecycle_msgs/srv/ChangeState` ([link](https://docs.ros.org/en/humble/p/lifecycle_msgs/srv/ChangeState.html)) applies the specified transition to all the nodes in `node_names` **in order**. (The list of transition IDs can be found [here](https://docs.ros.org/en/humble/p/lifecycle_msgs/msg/Transition.html).) If any node fails to transition, the manager returns a failure and does **not** transition subsequent nodes.

To avoid calling an invalid transition (which may kill the running node), we first call `<node_name>/get_state` of type `lifecycle_msgs/srv/GetState` to skip the node if it is already in the requested goal state. Otherwise, we call `<node_name>/get_available_transitions` (`lifecycle_msgs/srv/GetAvailableTransitions`) and return failure if the requested transition is not available. Otherwise, we call `<node_name>/change_state` (`lifecycle_msgs/srv/ChangeState`).
