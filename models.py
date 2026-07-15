"""
Models for the e-commerce store app.

We rely on Django's built-in User model (django.contrib.auth.models.User)
for authentication, and define Product, Cart, CartItem, Order, and OrderItem
below.

UPGRADE NOTE: Added Category model + Product.category ForeignKey only.
The FK is nullable/optional, so existing Product rows and any code that
creates Products without a category keep working unchanged. No existing
field, method, or class was removed or renamed.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver

# ---------------------------------------------------------------------------
# NEW: Category model (Product Categories feature)
# ---------------------------------------------------------------------------

class Category(models.Model):
    """A product category used for browsing/filtering the catalog."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True,
                             help_text="URL-friendly identifier, auto-generated from name if left blank")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-generate a slug from the name if one wasn't provided
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """A product available for sale in the store."""
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.PositiveIntegerField(default=0, help_text="Number of units available in stock")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_featured = models.BooleanField(default=False, help_text="Show on homepage featured section")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---- NEW FIELD (nullable/optional -> safe for existing rows) ----
    category = models.ForeignKey( 
        
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products', help_text="Product category (optional)"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    @property
    def in_stock(self):
        """Convenience property to check stock availability."""
        return self.stock > 0


class Cart(models.Model):
    """
    A shopping cart belonging to a logged-in user.
    Each user has exactly one active cart.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_price(self):
        """Sum of (price * quantity) for all items in the cart."""
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        """Total number of individual units in the cart."""
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """A single product line inside a shopping cart."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')  # One line per product per cart

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Order(models.Model):
    """A placed order, containing customer/shipping info and totals."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)

    # Customer details captured at checkout time
    customer_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    shipping_address = models.TextField()

    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"


class OrderItem(models.Model):
    """A single product line inside a placed order (snapshot at order time)."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)  # Snapshot in case product is later deleted/changed
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    @property
    def subtotal(self):
        return self.price * self.quantity            
    
# ---------------------------------------------------------------------------
# NEW: Wishlist (Feature #4)
# ---------------------------------------------------------------------------

class Wishlist(models.Model):
    """A single saved product for a user's wishlist."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Can't wishlist the same product twice
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} ♥ {self.product.name}"


# ---------------------------------------------------------------------------
# NEW: Review & Rating (Feature #5)
# ---------------------------------------------------------------------------

class Review(models.Model):
    """A user's rating and optional written review of a product."""
    RATING_CHOICES = [(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(1, 6)]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')  # One review per user per product
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} rated {self.product.name}: {self.rating}★"


# ---------------------------------------------------------------------------
# NEW: User Profile (Feature #8)
# ---------------------------------------------------------------------------

class UserProfile(models.Model):
    """Extra profile info attached 1-to-1 to Django's built-in User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a UserProfile whenever a new User is created —
    mirrors the existing Cart auto-creation pattern in views.py, so every
    user (including ones registered before this upgrade, once they save)
    ends up with a profile.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)


# ---------------------------------------------------------------------------
# NEW: Contact Us message storage (Feature #10)
# ---------------------------------------------------------------------------

class ContactMessage(models.Model):
    """Stores messages submitted via the Contact Us page."""
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} — {self.name}"