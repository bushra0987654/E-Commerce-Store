"""
Django admin configuration for the store app.
Provides a fully featured admin panel to manage Products, Orders, Carts, and Users.
"""
from django.contrib import admin
from .models import Product, Cart, CartItem, Order, OrderItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'is_featured', 'in_stock', 'created_at')
    list_filter = ('is_featured', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('price', 'stock', 'is_featured')
    ordering = ('-created_at',)


class CartItemInline(admin.TabularInline):
    """Show cart items inline within the Cart admin page."""
    model = CartItem
    extra = 0
    readonly_fields = ('added_at',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items', 'total_price', 'updated_at')
    inlines = [CartItemInline]
    search_fields = ('user__username',)


class OrderItemInline(admin.TabularInline):
    """Show ordered products inline within the Order admin page."""
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'subtotal')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'email', 'total_price', 'status', 'order_date')
    list_filter = ('status', 'order_date')
    search_fields = ('customer_name', 'email', 'phone_number')
    list_editable = ('status',)
    readonly_fields = ('order_date', 'total_price')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'price', 'quantity', 'subtotal')
