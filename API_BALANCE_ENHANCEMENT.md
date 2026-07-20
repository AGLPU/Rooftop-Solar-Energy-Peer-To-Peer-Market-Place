# Blockchain Balance API - Updated Response

## Endpoint
```
GET /api/v1/blockchain/balance/{wallet_address}
```

## New Response Format

The API now displays **both SEC tokens (energy) and ETH (money)** in the wallet.

### Example Request
```bash
curl "https://greengridenergyexchange.onrender.com/api/v1/blockchain/balance/0xeC1750f914b771138C746CdF1CE51D382BA24Ec4"
```

### Example Response (Success)
```json
{
  "wallet_address": "0xeC1750f914b771138C746CdF1CE51D382BA24Ec4",
  "sec_tokens": {
    "balance_kwh": 150,
    "balance_sec_tokens": 150,
    "note": "1 SEC token = 1 kWh of solar energy",
    "type": "Energy Tokens"
  },
  "eth": {
    "balance_eth": 2.5,
    "balance_wei": "2500000000000000000",
    "note": "Actual ETH (money) in the wallet for purchases",
    "type": "Native Currency"
  },
  "summary": {
    "energy_available_kwh": 150,
    "funds_available_eth": 2.5,
    "can_purchase": true
  }
}
```

## Response Fields Explained

### `sec_tokens` Object
- **`balance_kwh`**: Number of kWh the wallet owns (as SEC tokens)
- **`balance_sec_tokens`**: Same as balance_kwh (1 SEC token = 1 kWh)
- **`type`**: "Energy Tokens" - identifies this as energy

### `eth` Object
- **`balance_eth`**: ETH amount in decimal format (e.g., "2.5" = 2.5 ETH)
- **`balance_wei`**: ETH amount in wei (smallest unit, 1 ETH = 10^18 wei)
- **`type`**: "Native Currency" - identifies this as native ETH

### `summary` Object
- **`energy_available_kwh`**: Total energy in wallet
- **`funds_available_eth`**: Total money in wallet
- **`can_purchase`**: Boolean - true if wallet has both energy and funds

## What This Shows

✅ **Energy Status**: How many kWh of solar energy the wallet holds
✅ **Fund Status**: How much ETH (money) the wallet has available
✅ **Purchase Capability**: Whether the wallet can purchase more listings

## Use Cases

### 1. Check Seller's Energy Balance After Listing
```bash
# Check if tokens were minted after creating a listing
curl "https://greengridenergyexchange.onrender.com/api/v1/blockchain/balance/0xSELLER_ADDRESS"

# Response shows:
# - balance_kwh: 100 (tokens minted successfully)
# - balance_eth: 0.5 (seller's balance)
```

### 2. Check Buyer's Capability to Purchase
```bash
# Check if buyer has enough ETH to purchase energy
curl "https://greengridenergyexchange.onrender.com/api/v1/blockchain/balance/0xBUYER_ADDRESS"

# Response shows:
# - balance_kwh: 50 (energy they already own)
# - balance_eth: 5.0 (they have 5 ETH to spend)
# - can_purchase: true (they can buy)
```

### 3. Verify After Purchase
```bash
# After a purchase completes:
# - Buyer's balance_kwh should increase (received SEC tokens)
# - Seller's balance_eth should increase (received payment)
```

## API Status

✅ Live on https://greengridenergyexchange.onrender.com/api/v1/blockchain/balance/

### Testing

Try these addresses:
```bash
# Check balance for seller
curl "https://greengridenergyexchange.onrender.com/api/v1/blockchain/balance/0xeC1750f914b771138C746CdF1CE51D382BA24Ec4"

# Check balance for buyer  
curl "https://greengridenergyexchange.onrender.com/api/v1/blockchain/balance/0xYOUR_WALLET_ADDRESS"
```

## Implementation Details

- **SEC Token Balance**: Retrieved from smart contract via `getEnergyBalance()`
- **ETH Balance**: Retrieved via `Web3.eth.get_balance()`
- **Network**: Sepolia Testnet (or configured network)
- **No Gas Cost**: Both are read-only operations

## Migration/Update

This is a **non-breaking change** - the new fields are added alongside existing fields:
- ✅ Old clients still work (fields are included)
- ✅ New clients get both SEC and ETH data
- ✅ No database changes required
