"""Strategies for generating flow test data."""

from hypothesis import strategies as st


@st.composite
def flow_data(draw):
    """Generate random flow data for testing.
    
    Returns a dictionary with:
    - frequency: integer between 0 and 100
    - actions: list of action dictionaries
    """
    frequency = draw(st.integers(min_value=0, max_value=10))
    num_actions = draw(st.integers(min_value=0, max_value=3))

    action_types = [
        "[Amplitude] Page Viewed",
        "error",
        "click"
    ]

    pages = [
        "/login",
        "/checkout",
        "/profile",
        "/settings",
        "/unknown"
    ]

    actions = []
    for _ in range(num_actions):
        action_type = draw(st.sampled_from(action_types))
        if action_type == "[Amplitude] Page Viewed":
            actions.append({
                "type": action_type,
                "data": {"[Amplitude] Page URL": draw(st.sampled_from(pages))}
            })
        else:
            actions.append({
                "type": action_type,
                "target": f"{action_type}_{draw(st.integers(min_value=1, max_value=3))}"
            })

    return {
        "frequency": frequency,
        "actions": actions
    }


@st.composite
def config_data(draw):
    """Generate random configuration data for testing.
    
    Returns a dictionary with:
    - weights: dictionary with error_weight and business_weight
    - business_criticality: dictionary with criticality scores for different pages
    """
    error_weight = draw(st.floats(min_value=0.0, max_value=5.0))
    business_weight = draw(st.floats(min_value=0.0, max_value=5.0))

    pages = ["login", "checkout", "profile", "settings"]
    criticality = {
        "default": draw(st.floats(min_value=0.0, max_value=3.0)),
        **{page: draw(st.floats(min_value=0.0, max_value=3.0)) for page in pages}
    }

    return {
        "weights": {
            "error_weight": error_weight,
            "business_weight": business_weight
        },
        "business_criticality": criticality
    }
