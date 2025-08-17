"""Strategies for generating test data for flow-related tests."""

from hypothesis import strategies as st


def flow_data():
    """Generate test flow data."""
    return st.fixed_dictionaries({
        "frequency": st.integers(min_value=0),
        "actions": st.lists(
            st.fixed_dictionaries({
                "type": st.sampled_from(["[Amplitude] Page Viewed", "error", "form"]),
                "data": st.fixed_dictionaries({
                    "[Amplitude] Page URL": st.sampled_from(["/login", "/checkout", "/profile"]),
                    "message": st.just("Test error")
                })
            }),
            min_size=1
        )
    })

def config_data():
    """Generate test configuration data."""
    return st.fixed_dictionaries({
        "weights": st.fixed_dictionaries({
            "error_weight": st.floats(min_value=0.1, max_value=5.0),
            "business_weight": st.floats(min_value=0.1, max_value=5.0)
        }),
        "business_criticality": st.fixed_dictionaries({
            "default": st.integers(min_value=1, max_value=5),
            "login": st.integers(min_value=1, max_value=5),
            "checkout": st.integers(min_value=1, max_value=5),
            "profile": st.integers(min_value=1, max_value=5)
        })
    })
