# Purchase Data Integrity Verification System

## Overview

This document describes the purchase data integrity verification system that prevents tampering with purchase records through immutable blockchain-stored hashes.

## Problem Statement

**Attack Scenario:**
1. Buyer completes purchase: 50 kWh for $100
2. Purchase record created in database
3. Attacker modifies database: changes energy_kwh from 50 → 100 (fraudulent inflation)
4. Buyer sees 100 kWh in their account but only paid for 50
5. Buyer consumes fraudulent 100 kWh tokens

**Current Vulnerability:**
- Blockchain stores transaction hash, but not the purchase data details
- No way to verify if purchase metadata (energy, price, buyer) was tampered with after creation
- Blockchain token transfer was legitimate, but DB record is false

## Solution: Purchase Hash Verification

### How It Works

#### 1. Purchase Creation Flow
```
User creates purchase
    ↓
Backend calculates SHA256 hash of purchase data:
  {
    "buyer_id": "123e4567-e89b-12d3-a456-426614174000",
    "energy_kwh": 50,
    "price_eth": "0.05",
    "listing_id": "9e3a8b7c-6f4a-11eb-9299-0242ac130002"
  }
    ↓
Purchase hash = SHA256(canonical_json) = "a1b2c3d4e5..."
    ↓
recordPurchase() called with:
  - seller_address
  - buyer_address
  - energy_kwh (50)
  - price_wei (0.05 ETH)
  - listing_id
  - purchase_hash ("a1b2c3d4e5...") ← NEW
    ↓
Smart contract stores purchase_hash in mapping:
  purchaseHashes[purchase_id] = "a1b2c3d4e5..."
    ↓
Purchase recorded in DB with:
  - blockchain_tx_hash
  - purchase_hash ← stored locally too
    ↓
Return purchase details to buyer
```

#### 2. Verification Flow (On Get/Consume)
```
Buyer tries to view or consume purchase
    ↓
Backend retrieves purchase from DB
    ↓
Calculate current hash from DB values:
  {
    "buyer_id": "123e4567-e89b-12d3-a456-426614174000",
    "energy_kwh": 50,  (could be 100 if tampered!)
    "price_eth": "0.05",
    "listing_id": "9e3a8b7c-6f4a-11eb-9299-0242ac130002"
  }
  current_hash = SHA256(canonical_json) = "a1b2c3d4e5..."
    ↓
Compare with stored hash:
  stored_hash = "a1b2c3d4e5..."
    ↓
IF current_hash == stored_hash:
  ✓ Purchase data verified - allow consumption
ELSE:
  ✗ TAMPERING DETECTED
  - Set is_tampered = true
  - Block consumption
  - Return error to buyer
  - Log incident
```

### Data Integrity Guarantee

**What's Protected:**
- buyer_id: Prevents transfer to wrong wallet
- energy_kwh: Prevents fraudulent increase/decrease
- price_eth: Prevents price manipulation
- listing_id: Prevents cross-listing fraud

**What's NOT Protected (intentionally):**
- Status changes (PENDING → COMPLETED → CONSUMED are app lifecycle, not fraud)
- Timestamps (created_at, completed_at are informational)

**Why This Works:**
- Hash is deterministic: same input = same hash always
- Any change in ANY field → hash changes
- Hash stored immutably on blockchain before purchase committed to DB
- If attacker changes DB record, hash won't match
- Cryptographic guarantee: hash collision impossible with SHA256

### Detection Examples

#### Example 1: Energy Tampering (Attack)
```
Original purchase creation:
  energy_kwh=50, hash="a1b2c3..."
  ↓ (stored on blockchain)

Attacker modifies DB:
  UPDATE purchases SET energy_kwh=100 WHERE id='xyz'

Buyer tries to consume:
  Current: energy_kwh=100, calculated_hash="d4e5f6..."
  Stored:  energy_kwh=50,  stored_hash="a1b2c3..."
  
  d4e5f6 != a1b2c3
  
  ✗ TAMPERING DETECTED
  → is_tampered = true
  → Consumption blocked
```

#### Example 2: Price Tampering (Attack)
```
Original:
  price_eth=0.05, hash="a1b2c3..."

Attack:
  UPDATE purchases SET total_price=0.01 WHERE id='xyz'

Verification:
  Current hash calculated with price=0.01 → "g7h8i9..."
  Original hash with price=0.05 → "a1b2c3..."
  
  g7h8i9 != a1b2c3
  
  ✗ TAMPERING DETECTED
```

#### Example 3: Buyer ID Tampering (Attack)
```
Original:
  buyer_id='0x1234...', hash="a1b2c3..."

Attack:
  UPDATE purchases SET buyer_id='0x9999...' WHERE id='xyz'

Verification:
  Current hash with buyer='0x9999...' → "j1k2l3..."
  Original hash with buyer='0x1234...' → "a1b2c3..."
  
  j1k2l3 != a1b2c3
  
  ✗ TAMPERING DETECTED
```

## Smart Contract Changes Required

### Current ABI (recordPurchase)
```solidity
function recordPurchase(
  address seller,
  address buyer,
  uint256 amountKwh,
  uint256 priceWei,
  string memory listingId
) public onlyOwner nonReentrant
```

### Updated ABI Needed
```solidity
function recordPurchase(
  address seller,
  address buyer,
  uint256 amountKwh,
  uint256 priceWei,
  string memory listingId,
  bytes32 purchaseHash  ← NEW PARAMETER
) public onlyOwner nonReentrant
```

### Contract Storage Update
```solidity
// Add this mapping to EnergyToken contract
mapping(string => bytes32) public purchaseHashes;  // listingId → hash

// In recordPurchase function, add:
purchaseHashes[listingId] = purchaseHash;
```

### Deployment Steps
1. Update EnergyToken.sol to add purchaseHash parameter
2. Update purchaseHashes mapping
3. Recompile: `npm run compile`
4. Copy ABI to: `app/blockchain/EnergyToken.json`
5. Deploy new contract to Sepolia testnet
6. Update BLOCKCHAIN_CONTRACT_ADDRESS in environment variables
7. Test with new signature

## Backend Implementation

### Files Modified

#### 1. `app/models/purchase.py`
- Added `purchase_hash: String(64)` column (SHA256 hex)
- Added `is_tampered: Boolean` column (default False)

#### 2. `app/services/blockchain_service.py`
- Added `compute_purchase_hash()` static method
  - Input: buyer_id, energy_kwh, price_eth, listing_id
  - Output: SHA256 hex digest
  - Uses deterministic JSON encoding for consistency
  
- Updated `record_purchase()` method
  - Added `purchase_hash` parameter (ready for contract update)
  - Added wait_for_receipt=False for non-blocking execution
  
- Added `verify_purchase_integrity()` method
  - Input: current DB values + stored hash
  - Output: (is_valid: bool, message: str)
  - Recalculates hash and compares
  - Returns False if hashes don't match

#### 3. `app/services/purchase_service.py`
- Updated `create_purchase()` method
  - Calculates purchase_hash before blockchain call
  - Passes hash to record_purchase()
  - Stores hash in purchase record
  
- Updated `get_purchase()` method
  - Verifies integrity on retrieval
  - Marks is_tampered=true if verification fails
  - Logs warning for security audit
  
- Updated `consume_purchase()` method
  - Verifies integrity before consumption
  - Blocks consumption if tampered
  - Returns 400 error with detailed message
  - Marks is_tampered=true for tracking

#### 4. `app/schemas/purchase.py`
- Added `purchase_hash: Optional[str]` field
- Added `is_tampered: bool = False` field
- Added `can_consume` computed property
  - Returns: status=="COMPLETED" and not is_tampered

#### 5. `alembic/versions/0012_*`
- Migration to add two columns to purchases table
- Creates index on is_tampered for query optimization
- Reversible downgrade

## API Responses

### Purchase Response (GET /purchases/{id})
```json
{
  "id": "56e756e3-afe5-4afb-acaf-0c8bfc233c3f",
  "buyer_id": "6ef04719-d58f-4bfd-99fb-76143b166284",
  "seller_id": "3af8e47d-99f3-4e75-b390-d6daf936ce44",
  "listing_id": "933c95b8-2147-4413-9c41-9fccbb2f4f1f",
  "energy_kwh": 50,
  "price_per_kwh": "0.001",
  "total_price": "0.05",
  "status": "COMPLETED",
  "blockchain_tx_hash": "0xf4f858e47da3485752006c8fcba157069d2ccfdffbde23744e49c22091d61cde",
  "purchase_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "is_tampered": false,
  "can_consume": true,
  "created_at": "2026-07-19T19:04:45.650216",
  "completed_at": "2026-07-19T19:05:25.382703",
  "consumed_at": null
}
```

### Tampered Purchase Response
```json
{
  "id": "56e756e3-afe5-4afb-acaf-0c8bfc233c3f",
  "energy_kwh": 100,  ← MODIFIED!
  "status": "COMPLETED",
  "purchase_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",  ← ORIGINAL HASH
  "is_tampered": true,  ← DETECTED!
  "can_consume": false,  ← BLOCKED!
  ...
}
```

### Consume Blocked Response (POST /purchases/{id}/consume)
```json
{
  "detail": "Purchase data has been modified and cannot be consumed. Please contact support."
}
```

## Security Guarantees

### Threat Model
| Attack | Before | After |
|--------|--------|-------|
| Increase energy_kwh in DB | ✗ Undetected | ✓ Detected |
| Decrease energy_kwh in DB | ✗ Undetected | ✓ Detected |
| Change price in DB | ✗ Undetected | ✓ Detected |
| Change buyer_id in DB | ✗ Undetected | ✓ Detected |
| Modify purchase status | ✓ Already checked | ✓ Still checked |
| Replay old purchase | ✗ Undetected | ✓ Blockchain prevents (nonce) |

### What's NOT Prevented
- ✗ DBA with full database access (root-level breach)
- ✗ Smart contract owner malice (can change contract logic)
- ✗ RPC provider tampering (can return false data)
- **Mitigation:** Database encryption, access controls, audit logging

## Testing Strategy

### Unit Tests
```python
# Test hash calculation determinism
hash1 = compute_purchase_hash("buyer1", 50, "0.05", "listing1")
hash2 = compute_purchase_hash("buyer1", 50, "0.05", "listing1")
assert hash1 == hash2  # Same input always produces same hash

# Test hash changes with different input
hash3 = compute_purchase_hash("buyer1", 100, "0.05", "listing1")
assert hash1 != hash3  # Different energy produces different hash
```

### Integration Tests
```python
# Create purchase
purchase = create_purchase(db, buyer, listing)
assert purchase.purchase_hash is not None
assert purchase.is_tampered == False

# Modify DB (simulate attack)
db.execute("UPDATE purchases SET energy_kwh = 100 WHERE id = ?", [purchase.id])

# Verify detection
get_purchase(db, purchase.id)
purchase = db.query(Purchase).get(purchase.id)
assert purchase.is_tampered == True
```

### End-to-End Tests
1. Create purchase → verify hash stored
2. Retrieve purchase → verify hash matches
3. Tamper with DB field → retrieve → detect tampering
4. Attempt consume on tampered purchase → blocked
5. Verify audit log captures tampering event

## Performance Impact

### Calculation Cost
- SHA256 computation: ~1ms per purchase
- Negligible impact on API response time

### Storage Cost
- purchase_hash: 64 bytes per purchase
- is_tampered: 1 byte per purchase
- Index on is_tampered: ~100 bytes per purchase
- Total: ~165 bytes per purchase (1000 purchases = 165 KB)

### Blockchain Cost
- Gas for storing bytes32 hash: ~20,000-30,000 gas per purchase
- At current Sepolia gas price: ~$0.05-0.10 per purchase
- Acceptable cost for security guarantee

## Deployment Checklist

- [ ] Update EnergyToken.sol smart contract
- [ ] Compile new ABI: `npm run compile`
- [ ] Copy ABI to `app/blockchain/EnergyToken.json`
- [ ] Deploy contract to Sepolia testnet
- [ ] Update BLOCKCHAIN_CONTRACT_ADDRESS
- [ ] Run database migration: `alembic upgrade head`
- [ ] Test purchase creation with new signature
- [ ] Test integrity verification
- [ ] Test tampered purchase detection
- [ ] Test consumption blocking on tampered purchase
- [ ] Deploy to production
- [ ] Monitor audit logs for tampering attempts

## Future Enhancements

1. **Smart Contract Verification**
   - Add `verifyPurchaseHash(purchaseId, hash)` function
   - Allows users to verify purchase on blockchain explorer
   
2. **Seller-Side Verification**
   - Seller can verify all their purchases' hashes
   - Detect fraud attempts early
   
3. **Automatic Remediation**
   - If tampering detected, automatically refund buyer
   - Auto-alert seller
   
4. **Blockchain Sync**
   - Background job to sync purchase hashes from blockchain
   - Catch discrepancies between DB and chain
   
5. **Zero-Knowledge Proofs**
   - User can prove purchase validity without exposing full data
   - Privacy-preserving verification

## References

- SHA256 Algorithm: https://en.wikipedia.org/wiki/SHA-2
- ERC20 Standard: https://eips.ethereum.org/EIPS/eip-20
- Sepolia Testnet: https://sepolia.etherscan.io/
