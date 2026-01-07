# Concreate — E-commerce demo (Flask)

A minimalist brutalist-inspired e-commerce demo built as a bootcamp final project.
Includes product catalog, cart, checkout flow, and a basic admin dashboard.

## Live demo
- App: <add-render-url>
- Admin: <optional>
- Seeded demo data: included

## Stack
- Python 3.11
- Flask (app factory pattern)
- Flask-SQLAlchemy + Alembic migrations
- Flask-Login
- Bootstrap 5
- SQLite (dev) / Postgres (prod)

## Features
- Authentication (login/register)
- Product catalog + product pages
- Cart system
- Orders & order items
- Admin area (basic): manage orders, statuses
- Product seeding from Excel (demo script)

## Local setup
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
