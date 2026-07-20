#!/usr/bin/env python3
"""
Verification script for Purchase Integrity System
Validates that all components are properly integrated
"""

import sys
import json
from pathlib import Path
from decimal import Decimal

def verify_smart_contract():
    """Verify smart contract has required functions"""
    print("\n=== Verifying Smart Contract ===")
    
    abi_path = Path("app/blockchain/EnergyToken.json")
    if not abi_path.exists():
        print(f"❌ ABI not found: {abi_path}")
        return False
    
    with open(abi_path, 'r') as f:
        contract_json = json.load(f)
        abi = contract_json.get('abi', [])
    
    # Check for recordPurchase function
    record_purchase_funcs = [
        fn for fn in abi 
        if fn.get('name') == 'recordPurchase' and fn.get('type') == 'function'
    ]
    
    if not record_purchase_funcs:
        print("[FAIL] recordPurchase function not found in ABI")
        return False
    
    print(f"[PASS] Found {len(record_purchase_funcs)} recordPurchase function(s)")
    
    # Check for verifyPurchaseIntegrity function
    verify_funcs = [
        fn for fn in abi 
        if fn.get('name') == 'verifyPurchaseIntegrity' and fn.get('type') == 'function'
    ]
    
    if not verify_funcs:
        print("[FAIL] verifyPurchaseIntegrity function not found in ABI")
        return False
    
    print("[PASS] verifyPurchaseIntegrity function found")
    
    # Check for PurchaseRecorded event
    events = [e for e in abi if e.get('name') == 'PurchaseRecorded' and e.get('type') == 'event']
    if not events:
        print("[FAIL] PurchaseRecorded event not found in ABI")
        return False
    
    print("[PASS] PurchaseRecorded event found")
    
    return True


def verify_database_model():
    """Verify Purchase model has required fields"""
    print("\n=== Verifying Database Model ===")
    
    try:
        from app.models.purchase import Purchase
        
        # Check for purchase_hash column
        if not hasattr(Purchase, 'purchase_hash'):
            print("[FAIL] purchase_hash column not found in Purchase model")
            return False
        print("[PASS] purchase_hash column exists")
        
        # Check for is_tampered column
        if not hasattr(Purchase, 'is_tampered'):
            print("[FAIL] is_tampered column not found in Purchase model")
            return False
        print("[PASS] is_tampered column exists")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error checking Purchase model: {e}")
        return False


def verify_blockchain_service():
    """Verify blockchain service has required methods"""
    print("\n=== Verifying Blockchain Service ===")
    
    try:
        from app.services.blockchain_service import BlockchainService
        
        # Check for compute_purchase_hash method
        if not hasattr(BlockchainService, 'compute_purchase_hash'):
            print("[FAIL] compute_purchase_hash method not found")
            return False
        print("[PASS] compute_purchase_hash method exists")
        
        # Check for verify_purchase_integrity method
        if not hasattr(BlockchainService, 'verify_purchase_integrity'):
            print("[FAIL] verify_purchase_integrity method not found")
            return False
        print("[PASS] verify_purchase_integrity method exists")
        
        # Test hash computation
        test_hash = BlockchainService.compute_purchase_hash(
            buyer_id="test-buyer-123",
            energy_kwh=50,
            price_eth=Decimal("0.05"),
            listing_id="test-listing-456"
        )
        
        if not isinstance(test_hash, str) or len(test_hash) != 64:
            print(f"[FAIL] compute_purchase_hash returned invalid result: {test_hash}")
            return False
        print(f"[PASS] compute_purchase_hash works (hash: {test_hash[:16]}...)")
        
        # Test hash determinism
        test_hash2 = BlockchainService.compute_purchase_hash(
            buyer_id="test-buyer-123",
            energy_kwh=50,
            price_eth=Decimal("0.05"),
            listing_id="test-listing-456"
        )
        
        if test_hash != test_hash2:
            print("[FAIL] Hash computation is not deterministic!")
            return False
        print("[PASS] Hash computation is deterministic")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error checking blockchain service: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_purchase_schema():
    """Verify PurchaseResponse schema has required fields"""
    print("\n=== Verifying Purchase Schema ===")
    
    try:
        from app.schemas.purchase import PurchaseResponse
        
        # Check model fields
        fields = PurchaseResponse.model_fields
        
        required_fields = ['purchase_hash', 'is_tampered']
        for field in required_fields:
            if field not in fields:
                print(f"[FAIL] {field} field not found in PurchaseResponse")
                return False
            print(f"[PASS] {field} field exists")
        
        # Check for can_consume property
        if not hasattr(PurchaseResponse, 'can_consume'):
            print("[FAIL] can_consume property not found")
            return False
        print("[PASS] can_consume property exists")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error checking purchase schema: {e}")
        return False


def verify_purchase_service():
    """Verify purchase service integrates verification"""
    print("\n=== Verifying Purchase Service ===")
    
    try:
        from app.services.purchase_service import PurchaseService
        import inspect
        
        service = PurchaseService()
        
        # Check get_purchase method
        get_purchase_source = inspect.getsource(service.get_purchase)
        if 'verify_purchase_integrity' not in get_purchase_source:
            print("[FAIL] get_purchase doesn't call verify_purchase_integrity")
            return False
        print("[PASS] get_purchase verifies integrity")
        
        # Check consume_purchase method
        consume_source = inspect.getsource(service.consume_purchase)
        if 'verify_purchase_integrity' not in consume_source:
            print("[FAIL] consume_purchase doesn't call verify_purchase_integrity")
            return False
        print("[PASS] consume_purchase verifies integrity")
        
        if 'is_tampered' not in consume_source:
            print("[FAIL] consume_purchase doesn't check is_tampered")
            return False
        print("[PASS] consume_purchase checks tampered status")
        
        return True
    except Exception as e:
        print(f"[FAIL] Error checking purchase service: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_migration():
    """Verify database migration exists"""
    print("\n=== Verifying Database Migration ===")
    
    migrations_dir = Path("alembic/versions")
    migration_files = list(migrations_dir.glob("0012_*.py"))
    
    if not migration_files:
        print("[FAIL] Migration 0012_* not found")
        return False
    
    migration_file = migration_files[0]
    print(f"[PASS] Migration found: {migration_file.name}")
    
    # Check migration content
    content = migration_file.read_text()
    
    required_strings = ['purchase_hash', 'is_tampered', 'String(64)', 'Boolean']
    for req in required_strings:
        if req not in content:
            print(f"[FAIL] Migration missing '{req}'")
            return False
    print("[PASS] Migration has required columns")
    
    return True


def verify_documentation():
    """Verify documentation files exist"""
    print("\n=== Verifying Documentation ===")
    
    required_docs = [
        'PURCHASE_INTEGRITY_VERIFICATION.md',
        'PURCHASE_INTEGRITY_DEPLOYMENT.md'
    ]
    
    for doc in required_docs:
        doc_path = Path(doc)
        if not doc_path.exists():
            print(f"[FAIL] {doc} not found")
            return False
        
        size = doc_path.stat().st_size
        print(f"[PASS] {doc} exists ({size:,} bytes)")
    
    return True


def main():
    print("=" * 60)
    print("Purchase Integrity System - Verification Suite")
    print("=" * 60)
    
    checks = [
        ("Smart Contract", verify_smart_contract),
        ("Database Model", verify_database_model),
        ("Blockchain Service", verify_blockchain_service),
        ("Purchase Schema", verify_purchase_schema),
        ("Purchase Service", verify_purchase_service),
        ("Database Migration", verify_migration),
        ("Documentation", verify_documentation),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"[FAIL] {name} check failed: {e}")
            results[name] = False
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n[SUCCESS] All checks passed! System is ready for deployment.")
        return 0
    else:
        print(f"\n[ERROR] {total - passed} check(s) failed. Please fix before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
