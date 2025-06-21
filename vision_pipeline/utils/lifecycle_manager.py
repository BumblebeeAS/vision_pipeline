from typing import Sequence

from lifecycle_msgs.msg import State, TransitionDescription
from lifecycle_msgs.srv import ChangeState, GetAvailableTransitions, GetState
from rclpy.client import Client

# NOTE: TRANSITION_DESTROY is not available
# This is required since the ChangeState service request allows arbitrary labels
lifecycle_transitions = {
    0: "TRANSITION_CREATE",
    1: "TRANSITION_CONFIGURE",
    2: "TRANSITION_CLEANUP",
    3: "TRANSITION_ACTIVATE",
    4: "TRANSITION_DEACTIVATE",
    5: "TRANSITION_UNCONFIGURED_SHUTDOWN",
    6: "TRANSITION_INACTIVE_SHUTDOWN",
    7: "TRANSITION_ACTIVE_SHUTDOWN",
    8: "TRANSITION_DESTROY",
}


async def call_get_state(client: Client) -> State:
    """Call the GetState service to get the current state of a node.

    Args:
        client (Client): Client to the GetState service.

    Returns:
        State: Current state of the node.
    """
    req = GetState.Request()
    future = client.call_async(req)
    result: GetState.Response = await future
    return result.current_state


async def call_get_transitions(client: Client) -> Sequence[TransitionDescription]:
    """Call the GetAvailableTransitions service and return the available transitions.

    Args:
        client (Client): Client to the GetAvailableTransitions service.

    Returns:
        Sequence[TransitionDescription]: List of available transitions for the node.
    """
    req = GetAvailableTransitions.Request()
    future = client.call_async(req)
    result: GetAvailableTransitions.Response = await future
    return result.available_transitions


async def call_change_state(client: Client, transition_id: int) -> bool:
    """Call the ChangeState service to change the state of a node.

    Args:
        client (Client): Client to the ChangeState service.
        transition_id (int): ID of the transition to change to.

    Returns:
        bool: True if the state was changed successfully, False otherwise.
    """
    req = ChangeState.Request()
    req.transition.id = transition_id
    future = client.call_async(req)
    result: ChangeState.Response = await future
    return result.success
