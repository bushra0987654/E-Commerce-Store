"""
Forms for the store app: user registration and checkout.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Order


class RegisterForm(UserCreationForm):
    """
    Extends Django's built-in UserCreationForm to also collect an email
    address, and applies Bootstrap classes to all fields for styling.
    """
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap styling to every field automatically
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control', 'placeholder': field.label})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Simple login form (username + password) styled with Bootstrap."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class CheckoutForm(forms.ModelForm):
    """Collects customer details required to place an order."""

    class Meta:
        model = Order
        fields = ['customer_name', 'email', 'phone_number', 'shipping_address']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'Email Address'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Phone Number'
            }),
            'shipping_address': forms.Textarea(attrs={
                'class': 'form-control', 'placeholder': 'Full Shipping Address', 'rows': 4
            }),
        }

    def clean_phone_number(self):
        """Basic validation: phone number should contain only digits, spaces, +, -."""
        phone = self.cleaned_data['phone_number']
        allowed = set('0123456789 +-()')
        if not phone or any(ch not in allowed for ch in phone):
            raise forms.ValidationError("Enter a valid phone number.")
        if len(phone.strip()) < 7:
            raise forms.ValidationError("Phone number is too short.")
        return phone
