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

# Primary state each transition ends in, used to skip nodes already there.
# Transition and state IDs overlap numerically (e.g. TRANSITION_CONFIGURE == 1 ==
# PRIMARY_STATE_UNCONFIGURED), so they must not be compared directly.
transition_goal_states = {
    1: 2,  # CONFIGURE -> INACTIVE
    2: 1,  # CLEANUP -> UNCONFIGURED
    3: 3,  # ACTIVATE -> ACTIVE
    4: 2,  # DEACTIVATE -> INACTIVE
    5: 4,  # UNCONFIGURED_SHUTDOWN -> FINALIZED
    6: 4,  # INACTIVE_SHUTDOWN -> FINALIZED
    7: 4,  # ACTIVE_SHUTDOWN -> FINALIZED
}
