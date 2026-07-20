#!/usr/bin/env python3
"""Verify that payment_tx_hash column was added to purchases table"""

from app.database import SessionLocal
from sqlalchemy import inspect

try:
    db = SessionLocal()
    inspector = inspect(db.get_bind())
    
    # Get columns for purchases table
    columns = inspector.get_columns('purchases')
    column_names = [col['name'] for col in columns]
    
    print("✅ Successfully connected to database")
    print("\nColumns in 'purchases' table:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
    
    if 'payment_tx_hash' in column_names:
        print("\n✅ SUCCESS: payment_tx_hash column exists!")
    else:
        print("\n❌ ERROR: payment_tx_hash column NOT found!")
        
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    db.close()
