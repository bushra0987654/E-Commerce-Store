"""
Custom context processors for the store app.
"""
from .models import Cart


def cart_item_count(request):
    """
    Makes `cart_item_count` available in every template so the navbar
    can show a live badge of how many items are in the user's cart.
    """
    count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            count = cart.total_items
    return {'cart_item_count': count}
