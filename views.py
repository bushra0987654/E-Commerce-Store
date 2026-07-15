"""
Views for the store app.
"""
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .forms import RegisterForm, LoginForm, CheckoutForm
from .models import Product, Cart, CartItem, Order, OrderItem


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _get_or_create_cart(user):
    """Return the user's cart, creating one if it doesn't exist yet."""
    cart, _created = Cart.objects.get_or_create(user=user)
    return cart


# ---------------------------------------------------------------------------
# Authentication views
# ---------------------------------------------------------------------------

def register_view(request):
    """Handle new user registration using Django's built-in auth system."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Automatically create an empty cart for the new user
            Cart.objects.get_or_create(user=user)
            login(request, user)  # Log the user in immediately after registering
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()

    return render(request, 'store/register.html', {'form': form})


def login_view(request):
    """Handle user login using Django's built-in authentication."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                _get_or_create_cart(user)
                messages.success(request, f"Welcome back, {user.username}!")
                next_url = request.GET.get('next')
                return redirect(next_url or 'home')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'store/login.html', {'form': form})


@login_required
def logout_view(request):
    """Log the current user out."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


# ---------------------------------------------------------------------------
# Home & product views
# ---------------------------------------------------------------------------

def home_view(request):
    """Homepage: shows featured products and supports a top search bar."""
    query = request.GET.get('q', '').strip()
    featured_products = Product.objects.filter(is_featured=True)[:8]

    if not featured_products:
        # Fall back to newest products if nothing is marked featured
        featured_products = Product.objects.all()[:8]

    search_results = None
    if query:
        search_results = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    context = {
        'featured_products': featured_products,
        'search_results': search_results,
        'query': query,
    }
    return render(request, 'store/home.html', context)


def product_list_view(request):
    """Full product listing page with search support."""
    query = request.GET.get('q', '').strip()
    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    context = {'products': products, 'query': query}
    return render(request, 'store/product_list.html', context)


def product_detail_view(request, product_id):
    """Product details page."""
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})


# ---------------------------------------------------------------------------
# Shopping cart views
# ---------------------------------------------------------------------------

@login_required
def cart_view(request):
    """Display the current user's shopping cart."""
    cart = _get_or_create_cart(request.user)
    return render(request, 'store/cart.html', {'cart': cart})


@login_required
def add_to_cart_view(request, product_id):
    """Add a product to the cart, or increase its quantity if already present."""
    product = get_object_or_404(Product, id=product_id)
    cart = _get_or_create_cart(request.user)

    if product.stock < 1:
        messages.error(request, f"Sorry, {product.name} is out of stock.")
        return redirect('product_detail', product_id=product.id)

    # Read desired quantity from the form (default 1)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1
    quantity = max(1, quantity)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
    if not created:
        cart_item.quantity += quantity

    # Don't let cart quantity exceed available stock
    if cart_item.quantity > product.stock:
        cart_item.quantity = product.stock
        messages.warning(request, f"Only {product.stock} unit(s) of {product.name} available. Quantity adjusted.")

    cart_item.save()
    messages.success(request, f"{product.name} added to cart.")
    return redirect('cart')


@login_required
def update_cart_item_view(request, item_id):
    """Update the quantity of an existing cart item."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1

        if quantity < 1:
            cart_item.delete()
            messages.info(request, "Item removed from cart.")
        else:
            if quantity > cart_item.product.stock:
                quantity = cart_item.product.stock
                messages.warning(request, "Quantity adjusted to available stock.")
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, "Cart updated.")

    return redirect('cart')


@login_required
def remove_from_cart_view(request, item_id):
    """Remove a single item line from the cart."""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect('cart')


@login_required
def empty_cart_view(request):
    """Remove all items from the current user's cart."""
    cart = _get_or_create_cart(request.user)
    cart.items.all().delete()
    messages.info(request, "Your cart has been emptied.")
    return redirect('cart')


# ---------------------------------------------------------------------------
# Checkout & order views
# ---------------------------------------------------------------------------

@login_required
def checkout_view(request):
    """Collect customer/shipping details and show an order summary."""
    cart = _get_or_create_cart(request.user)

    if not cart.items.exists():
        messages.warning(request, "Your cart is empty. Add some products before checking out.")
        return redirect('product_list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Re-validate stock right before placing the order
            for item in cart.items.select_related('product'):
                if item.quantity > item.product.stock:
                    messages.error(
                        request,
                        f"Not enough stock for {item.product.name}. Only {item.product.stock} left."
                    )
                    return redirect('cart')

            with transaction.atomic():
                # Create the order record with customer/shipping details
                order = form.save(commit=False)
                order.user = request.user
                order.total_price = cart.total_price
                order.save()

                # Snapshot each cart item into an OrderItem, and decrement stock
                for item in cart.items.select_related('product'):
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        product_name=item.product.name,
                        price=item.product.price,
                        quantity=item.quantity,
                    )
                    item.product.stock -= item.quantity
                    item.product.save()

                # Clear the cart now that the order has been placed
                cart.items.all().delete()

            messages.success(request, "Your order has been placed successfully!")
            return redirect('order_success', order_id=order.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Pre-fill email from the logged-in user if available
        initial = {'email': request.user.email} if request.user.email else {}
        form = CheckoutForm(initial=initial)

    return render(request, 'store/checkout.html', {'form': form, 'cart': cart})


@login_required
def order_success_view(request, order_id):
    """Show a confirmation page after an order has been placed."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})
