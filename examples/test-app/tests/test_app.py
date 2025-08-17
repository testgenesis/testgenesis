import pytest
from app import current_user, error_states, random_error, set_current_user, toggle_error
from lib.auth import User
from nicegui import ui
from views.checkout import complete_purchase, handle_purchase


@pytest.fixture(autouse=True)
def app():
    """Fixture to set up and tear down the app."""
    # Reset error states before each test
    for key in error_states:
        error_states[key] = False

    # Set up containers
    with ui.column() as main_container:
        ui.label("Test App")
        with ui.row() as content_container:
            ui.label("Content")

    yield

    # Clean up after each test
    main_container.clear()
    content_container.clear()


def test_toggle_error():
    """Test toggling error states."""
    # Test login error
    result = toggle_error("login")
    assert result["success"] is True
    assert result["flow"] == "login"
    assert error_states["login"] is True

    # Test profile error
    result = toggle_error("profile")
    assert result["success"] is True
    assert result["flow"] == "profile"
    assert error_states["profile"] is True

    # Test invalid flow
    result = toggle_error("invalid_flow")
    assert "error" in result
    assert result["error"] == "Invalid flow"


def test_random_error():
    """Test random error triggering."""
    result = random_error()
    assert result["success"] is True
    assert result["flow"] in ["login", "profile", "checkout"]
    assert error_states[result["flow"]] is True


def test_handle_purchase_validation():
    """Test purchase form validation."""
    # Test empty fields
    handle_purchase("", "", "")
    # Note: We can't directly test UI notifications, but the function should complete without errors

    # Test partial fields
    handle_purchase("1234", "", "")
    handle_purchase("", "12/25", "")
    handle_purchase("", "", "123")

    # Test valid fields
    handle_purchase("1234567890123456", "12/25", "123")


def test_complete_purchase():
    """Test purchase completion."""
    complete_purchase()
    # Note: We can't directly test UI navigation or notifications, but the function should complete without errors


def test_error_states_initialization():
    """Test that error states are properly initialized."""
    # Reset error states to ensure they're False
    for key in error_states:
        error_states[key] = False

    # Test initial state
    assert error_states["login"] is False
    assert error_states["profile"] is False
    assert error_states["checkout"] is False


def test_error_state_toggle_sequence():
    """Test a sequence of error state toggles."""
    # Reset error states
    for key in error_states:
        error_states[key] = False

    # Toggle login error
    result = toggle_error("login")
    assert result["success"] is True
    assert error_states["login"] is True

    # Toggle it back
    result = toggle_error("login")
    assert result["success"] is True
    assert error_states["login"] is False

    # Toggle profile error
    result = toggle_error("profile")
    assert result["success"] is True
    assert error_states["profile"] is True

    # Toggle checkout error
    result = toggle_error("checkout")
    assert result["success"] is True
    assert error_states["checkout"] is True


@pytest.mark.ui
async def test_navigation_menu(app, user):
    """Test navigation menu functionality."""
    # Test menu visibility and navigation for non-logged in user
    await user.open("/login")
    user.find("Menu").should_exist()

    # Test menu visibility and navigation for logged in user
    set_current_user(User("test@example.com", "Test User", "test_user_123"))
    await user.open("/store")
    user.find("Menu").should_exist()

    # Test navigation to cart
    user.find("Menu").click()
    user.find("Cart").click()
    await user.should_see("Shopping Cart")

    # Test navigation to profile
    await user.open("/store")
    user.find("Menu").click()
    user.find("Profile").click()
    await user.should_see("Profile")

    # Test logout
    await user.open("/store")
    user.find("Menu").click()
    user.find("Logout").click()
    assert current_user is None, "Logout should clear current user"
    await user.should_see("Log in")


def test_amplitude_scoring():
    """Test amplitude scoring functionality."""
    from testgenesis_cli.analytics.amplitude import score_flows

    # Test data
    test_flows = {
        "login.flow": {
            "name": "login.flow",
            "frequency": 1000,
            "actions": [
                {
                    "type": "[Amplitude] Page Viewed",
                    "target": "",
                    "data": {
                        "[Amplitude] Page URL": "http://127.0.0.1:8081/login",
                        "[Amplitude] Page Path": "/login",
                    },
                },
                {
                    "type": "error",
                    "target": "",
                    "data": {
                        "error_type": "login_error",
                        "error_code": "invalid_credentials",
                        "message": "Invalid username or password",
                    },
                },
            ],
        },
        "checkout.flow": {
            "name": "checkout.flow",
            "frequency": 500,
            "actions": [
                {
                    "type": "[Amplitude] Page Viewed",
                    "target": "",
                    "data": {
                        "[Amplitude] Page URL": "http://127.0.0.1:8081/checkout",
                        "[Amplitude] Page Path": "/checkout",
                    },
                },
                {
                    "type": "error",
                    "target": "",
                    "data": {
                        "error_type": "validation_error",
                        "error_code": "invalid_card",
                        "message": "Invalid card number",
                    },
                },
            ],
        },
    }

    # Test scoring with explicit config file
    results = score_flows(test_flows, config_path="testgenesis.config")

    # Debug: Print results
    print("\nDebug: Scoring Results:")
    for result in results:
        print(f"\nFlow: {result['flow_file']}")
        print(f"Score: {result['score']}")
        print(f"Frequency: {result['frequency']}")
        print(f"Expected Errors: {result['expected_error_count']}")
        print(f"Unexpected Errors: {result['unexpected_error_count']}")
        print(f"Business Impact: {result.get('business_impact', 'NOT FOUND')}")
        print(f"All Keys: {list(result.keys())}")

    # Verify results structure
    assert isinstance(results, list)
    assert len(results) == 2

    # Verify login flow scoring
    login_result = next(r for r in results if r["flow_file"] == "login.flow")
    assert login_result["score"] > 0
    assert login_result["frequency"] == 1000
    assert login_result["expected_error_count"] == 0
    assert login_result["unexpected_error_count"] == 1
    assert login_result["business_impact"] == 5  # From testgenesis.config

    # Verify checkout flow scoring
    checkout_result = next(r for r in results if r["flow_file"] == "checkout.flow")
    assert checkout_result["score"] > 0
    assert checkout_result["frequency"] == 500
    assert checkout_result["expected_error_count"] == 0
    assert checkout_result["unexpected_error_count"] == 1
    assert checkout_result["business_impact"] == 2  # Default from testgenesis.config

    # Verify business impact calculation
    assert login_result["business_impact"] > checkout_result["business_impact"], (
        "Login should have higher business impact than checkout"
    )
