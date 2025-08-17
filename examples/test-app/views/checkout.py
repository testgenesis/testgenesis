from lib.amplitude import track_event
from nicegui import ui


def create_checkout_page():
    """Create the checkout page with a payment form."""
    track_event('page_view', None, {'page': 'checkout'})

    with ui.card().classes('w-full max-w-2xl mx-auto'):
        ui.label('Checkout').classes('text-h4 mb-4')

        # Payment form
        with ui.form().classes('w-full'):
            # Card number
            card_number = ui.input(
                label='Card Number',
                placeholder='1234 5678 9012 3456'
            ).classes('w-full mb-4')

            # Expiry date
            with ui.row().classes('w-full gap-4'):
                expiry_month = ui.select(
                    label='Month',
                    options=[f'{i:02d}' for i in range(1, 13)]
                ).classes('w-1/2')

                expiry_year = ui.select(
                    label='Year',
                    options=[str(i) for i in range(2024, 2035)]
                ).classes('w-1/2')

            # CVV
            cvv = ui.input(
                label='CVV',
                placeholder='123',
                type='password'
            ).classes('w-full mb-4')

            # Total amount
            ui.label('Total Amount: $99.99').classes('text-h6 mb-4')

            # Submit button
            ui.button(
                'Complete Purchase',
                on_click=lambda: handle_purchase(
                    card_number.value,
                    f"{expiry_month.value}/{expiry_year.value}",
                    cvv.value
                )
            ).classes('w-full')

    # Back to cart button
    ui.button(
        'Back to Cart',
        on_click=lambda: ui.navigate.to('/cart')
    ).classes('mt-4')

def handle_purchase(card_number: str, expiry: str, cvv: str):
    """Handle the purchase submission."""
    if not all([card_number, expiry, cvv]):
        ui.notify('Please fill in all fields', type='warning')
        return

    # Track the purchase attempt
    track_event('purchase_attempted', None, {
        'card_number': card_number[:4] + '****',  # Only track last 4 digits
        'expiry': expiry
    })

    # Simulate payment processing
    ui.notify('Processing payment...', type='info')

    # In a real app, this would be an API call
    ui.timer(2.0, lambda: complete_purchase())

def complete_purchase():
    """Complete the purchase process."""
    track_event('purchase_completed', None, {
        'amount': 99.99,
        'currency': 'USD'
    })

    ui.notify('Purchase completed successfully!', type='success')
    ui.timer(1.0, lambda: ui.navigate.to('/store'))
