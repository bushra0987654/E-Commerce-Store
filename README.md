# SimpleShop — Django E-commerce Store

A complete, runnable e-commerce store built with Django (backend), SQLite (database),
and HTML5/CSS3/JavaScript + Bootstrap 5 (frontend).

## Features
- User registration, login, logout (Django built-in auth, password validation)
- Responsive homepage with navbar, search bar, and featured products
- Product listing and detail pages (image, name, description, price, stock)
- Shopping cart: add / remove / update quantity / empty / auto total
- Checkout: customer name, email, phone, shipping address, order summary
- Orders saved to SQLite with customer details, items, total price, date
- Order success confirmation page
- Full Django Admin panel to manage Products, Orders, and Users

## Project Structure
```
ecommerce_store/
├── manage.py
├── requirements.txt
├── ecommerce_store/          # Project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── store/                    # Main app
│   ├── models.py             # Product, Cart, CartItem, Order, OrderItem
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── context_processors.py
│   ├── migrations/
│   ├── templates/store/      # All HTML templates
│   └── static/store/         # style.css, script.js
└── media/                    # Uploaded product images
```

## Installation & Run

```bash
# 1. Create & activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py makemigrations
python manage.py migrate

# 4. Create an admin user
python manage.py createsuperuser

# 5. Run the development server
python manage.py runserver
```

Visit:
- Store: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/

## Adding Products
Log into `/admin/`, go to **Products**, click **Add Product**, fill in name,
description, price, stock, upload an image, and optionally check "is_featured"
to show it on the homepage.

## Notes
- `DEBUG = True` and `SECRET_KEY` in `settings.py` are for development only —
  change both before deploying to production.
- Media files (product images) are served by Django's dev server only when
  `DEBUG = True`. Use a real web server (nginx, etc.) in production.
