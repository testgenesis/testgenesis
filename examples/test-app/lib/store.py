from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Product:
    id: str
    name: str
    price: float
    description: str

@dataclass
class CartItem:
    product: Product
    quantity: int

# Sample products
products = {
    "p1": Product("p1", "T-Shirt", 19.99, "A comfortable cotton t-shirt"),
    "p2": Product("p2", "Jeans", 49.99, "Classic blue jeans"),
    "p3": Product("p3", "Sneakers", 79.99, "Casual sneakers"),
}

# User carts storage
carts: Dict[str, List[CartItem]] = {}

def get_products() -> List[Product]:
    """Get all available products."""
    return list(products.values())

def get_product(product_id: str) -> Product:
    """Get a product by ID."""
    if product_id not in products:
        raise ValueError("Product not found")
    return products[product_id]

def get_cart(user_id: str) -> List[CartItem]:
    """Get a user's cart."""
    return carts.get(user_id, [])

def add_to_cart(user_id: str, product_id: str, quantity: int = 1):
    """Add a product to a user's cart."""
    product = get_product(product_id)
    if user_id not in carts:
        carts[user_id] = []
    
    # Check if product already in cart
    for item in carts[user_id]:
        if item.product.id == product_id:
            item.quantity += quantity
            return
    
    carts[user_id].append(CartItem(product, quantity))

def remove_from_cart(user_id: str, product_id: str):
    """Remove a product from a user's cart."""
    if user_id not in carts:
        return
    
    carts[user_id] = [item for item in carts[user_id] if item.product.id != product_id]

def get_cart_total(user_id: str) -> float:
    """Calculate the total price of items in a user's cart."""
    return sum(item.product.price * item.quantity for item in get_cart(user_id))

def clear_cart(user_id: str):
    """Clear a user's cart."""
    carts[user_id] = [] 