# Flask Inventory Management (SQLite + Bootstrap)

Small inventory app for Products, Locations and Product Movements (transfer in/out).

## Features
- CRUD for Products and Locations
- Record Product Movements (from_location optional, to_location optional)
- Balance report: shows product balance per location (Product, Warehouse, Qty)
- Uses SQLite and Bootstrap for UI

## Requirements
- Python 3.8+
- pip

## Setup (quick)
1. Clone repository or copy files.
2. Create virtualenv (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
   pip install Flask SQLAlchemy
