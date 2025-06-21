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
