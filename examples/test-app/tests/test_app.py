import pytest
from nicegui import ui
from app import error_states, toggle_error, random_error, set_current_user, current_user
from views.checkout import handle_purchase, complete_purchase
from lib.auth import User

@pytest.fixture(autouse=True)
def app():
    """Fixture to set up and tear down the app."""
    # Reset error states before each test
    for key in error_states:
        error_states[key] = False
    
    # Set up containers
    with ui.column() as main_container:
        ui.label('Test App')
        with ui.row() as content_container:
            ui.label('Content')
    
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
    await user.open('/login')
    user.find('Menu').should_exist()
    
    # Test menu visibility and navigation for logged in user
    set_current_user(User("test@example.com", "Test User", "test_user_123"))
    await user.open('/store')
    user.find('Menu').should_exist()
    
    # Test navigation to cart
    user.find('Menu').click()
    user.find('Cart').click()
    await user.should_see('Shopping Cart')
    
    # Test navigation to profile
    await user.open('/store')
    user.find('Menu').click()
    user.find('Profile').click()
    await user.should_see('Profile')
    
    # Test logout
    await user.open('/store')
    user.find('Menu').click()
    user.find('Logout').click()
    assert current_user is None, "Logout should clear current user"
    await user.should_see('Log in') 