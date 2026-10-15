"""
Helper script to populate the SQLite database with initial sample products for testing.
Usage:
    python seed_data.py
"""

from app.database import SessionLocal, Base, engine
from app.models import Product


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if products already exist
        existing_count = db.query(Product).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} product(s). Skipping seed.")
            return

        sample_products = [
            Product(name="Mechanical Keyboard", stock_quantity=20),
            Product(name="Wireless Gaming Mouse", stock_quantity=15),
            Product(name="UltraWide Monitor 34-inch", stock_quantity=5),
            Product(name="USB-C Docking Station", stock_quantity=8),
            Product(name="Noise Cancelling Headphones", stock_quantity=12),
        ]

        db.add_all(sample_products)
        db.commit()
        print("Successfully seeded sample products:")
        for p in sample_products:
            print(f"  - [{p.id}] {p.name} (Stock: {p.stock_quantity})")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
