from nicegui import ui
from lib.store import (
    get_products, get_cart, add_to_cart, remove_from_cart,
    get_cart_total, clear_cart, Product, CartItem
)
from lib.amplitude import track_event

def create_product_card(product: Product, user_id: str):
    """Create a card for a product."""
    with ui.card().classes('w-64'):
        ui.label(product.name).classes('text-h6')
        ui.label(f"${product.price:.2f}").classes('text-subtitle1')
        ui.label(product.description).classes('text-body2')
        
        def handle_add_to_cart():
            track_event('add_to_cart', user_id, {'product_id': product.id})
            add_to_cart(user_id, product.id)
            ui.notify(f'Added {product.name} to cart', type='positive')
        
        ui.button('Add to Cart', on_click=handle_add_to_cart).classes('w-full')

def create_cart_item(item: CartItem, user_id: str, on_update=None):
    """Create a display for a cart item."""
    with ui.row().classes('w-full items-center justify-between'):
        ui.label(f"{item.product.name} x{item.quantity}")
        ui.label(f"${item.product.price * item.quantity:.2f}")
        
        def handle_remove():
            track_event('remove_from_cart', user_id, {'product_id': item.product.id})
            remove_from_cart(user_id, item.product.id)
            if on_update:
                on_update()
        
        ui.button('Remove', on_click=handle_remove).classes('text-negative')

def create_store_page(user_id: str):
    """Create the store page with products and cart."""
    track_event('page_view', user_id, {'page': 'store'})
    
    with ui.row().classes('w-full justify-between p-4'):
        ui.label('Store').classes('text-h4')
        with ui.row():
            ui.button('View Cart', on_click=lambda: ui.navigate.to('/cart')).classes('mr-2')
            ui.button('Profile', on_click=lambda: ui.navigate.to('/profile'))
    
    with ui.grid().classes('gap-4'):
        for product in get_products():
            create_product_card(product, user_id)

def create_cart_page(user_id: str):
    """Create the cart page."""
    track_event('page_view', user_id, {'page': 'cart'})
    
    def refresh_cart():
        cart_container.clear()
        total = get_cart_total(user_id)
        
        with cart_container:
            if not get_cart(user_id):
                ui.label('Your cart is empty').classes('text-subtitle1')
            else:
                for item in get_cart(user_id):
                    create_cart_item(item, user_id, refresh_cart)
                
                ui.separator()
                ui.label(f'Total: ${total:.2f}').classes('text-h6')
                
                def handle_checkout():
                    track_event('checkout_complete', user_id, {'total': total})
                    clear_cart(user_id)
                    ui.notify('Order placed successfully!', type='positive')
                    refresh_cart()
                
                ui.button('Checkout', on_click=handle_checkout).classes('w-full mt-4')
    
    with ui.column().classes('w-full max-w-3xl mx-auto p-4'):
        ui.label('Shopping Cart').classes('text-h4')
        cart_container = ui.column().classes('w-full')
        refresh_cart()
        
        ui.button('Back to Store', on_click=lambda: ui.navigate.to('/store')).classes('mt-4') 