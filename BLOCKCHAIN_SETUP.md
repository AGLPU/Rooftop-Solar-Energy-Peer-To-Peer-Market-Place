# 🔗 Blockchain Integration Guide

## Overview

This Solar Energy Marketplace integrates with Ethereum blockchain to tokenize energy credits as ERC-20 tokens.

**Key Features:**
- ✅ Energy is represented as **ERC-20 tokens** (1 token = 1 kWh)
- ✅ Sellers mint tokens when they produce energy
- ✅ Buyers purchase and receive tokens
- ✅ Transparent, immutable transaction records
- ✅ **Optional** - System works with database-only mode too

---

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
│  (Python/Web3)  │
└────────┬────────┘
         │
         │ Web3.py
         │
┌────────▼────────┐
│  Ethereum Node  │
│  (Local/Testnet)│
└────────┬────────┘
         │
         │
┌────────▼────────┐
│ EnergyToken.sol │
│  (Smart Contract)│
└─────────────────┘
```

---

## Prerequisites

### 1. Install Node.js and npm
```bash
node --version  # Should be v18+
npm --version
```

### 2. Install Dependencies

**Contracts (Node.js):**
```bash
cd contracts
npm install
```

**Backend (Python):**
```bash
pip install web3==6.15.1
```

---

## Setup Options

### 🟢 Option 1: Local Development (Hardhat Network)

**Easiest for testing - No real money needed!**

#### Step 1: Start Local Blockchain
```bash
cd contracts
npx hardhat node
```

This starts a local Ethereum node at `http://127.0.0.1:8545` with test accounts pre-funded with ETH.

#### Step 2: Deploy Contract
Open a **new terminal**:
```bash
cd contracts
npm run deploy:local
```

Copy the contract address from output.

#### Step 3: Update `.env`
```env
BLOCKCHAIN_ENABLED=True
BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545
BLOCKCHAIN_NETWORK=localhost
BLOCKCHAIN_CONTRACT_ADDRESS=0x... (from deployment)
BLOCKCHAIN_PRIVATE_KEY=ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

**Note:** The private key above is from Hardhat's default test accounts (Account #0). **Never use this in production!**

---

### 🟡 Option 2: Ethereum Sepolia Testnet

**For testing with real test network**

#### Step 1: Get Testnet ETH
1. Create a wallet on [MetaMask](https://metamask.io/)
2. Switch to Sepolia network
3. Get free test ETH from faucet:
   - https://sepoliafaucet.com/
   - https://sepolia-faucet.pk910.de/

#### Step 2: Get RPC URL
Use a free RPC provider:
- [Alchemy](https://www.alchemy.com/) - Sign up and create Sepolia app
- [Infura](https://infura.io/) - Get free API key
- Public RPC: `https://rpc.sepolia.org`

#### Step 3: Deploy Contract
```bash
cd contracts
export SEPOLIA_RPC_URL="https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY"
export DEPLOYER_PRIVATE_KEY="your_private_key_without_0x"
npm run deploy:sepolia
```

#### Step 4: Update `.env`
```env
BLOCKCHAIN_ENABLED=True
BLOCKCHAIN_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY
BLOCKCHAIN_NETWORK=sepolia
BLOCKCHAIN_CONTRACT_ADDRESS=0x... (from deployment)
BLOCKCHAIN_PRIVATE_KEY=your_private_key_here
```

---

### 🟣 Option 3: Polygon Mumbai Testnet

**Cheaper gas fees than Ethereum!**

#### Step 1: Get Test MATIC
1. Switch MetaMask to Mumbai network
2. Get free test MATIC from:
   - https://faucet.polygon.technology/

#### Step 2: Deploy
```bash
cd contracts
export MUMBAI_RPC_URL="https://rpc-mumbai.maticvigil.com"
export DEPLOYER_PRIVATE_KEY="your_private_key"
npm run deploy:mumbai
```

#### Step 3: Update `.env`
```env
BLOCKCHAIN_ENABLED=True
BLOCKCHAIN_RPC_URL=https://rpc-mumbai.maticvigil.com
BLOCKCHAIN_NETWORK=mumbai
BLOCKCHAIN_CONTRACT_ADDRESS=0x...
BLOCKCHAIN_PRIVATE_KEY=your_private_key
```

---

### 🔴 Option 4: Database-Only Mode (No Blockchain)

**For development without blockchain complexity**

Just set in `.env`:
```env
BLOCKCHAIN_ENABLED=False
```

The system will work perfectly fine without blockchain - all transactions are tracked in the database only.

---

## Testing the Integration

### 1. Check Blockchain Status
```bash
curl http://127.0.0.1:8000/api/v1/blockchain/status
```

**Expected Response:**
```json
{
  "connected": true,
  "chain_id": 31337,
  "block_number": 42,
  "contract_address": "0x5FbDB2315678afecb367f032d93F642f64180aa3",
  "token_name": "Solar Energy Credit",
  "token_symbol": "SEC"
}
```

### 2. Check Token Balance
```bash
curl http://127.0.0.1:8000/api/v1/blockchain/balance/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1
```

### 3. Create Listing (Auto-mints tokens)
When a seller creates a listing, tokens are automatically minted to their wallet address.

---

## Smart Contract Details

### EnergyToken.sol

**Contract Functions:**
- `mintEnergy(address seller, uint256 kWh, string metadata)` - Mint tokens for energy production
- `recordPurchase(address seller, address buyer, uint256 kWh, uint256 price)` - Record energy purchase
- `consumeEnergy(uint256 kWh)` - Burn tokens when energy is consumed
- `getEnergyBalance(address)` - Get balance in kWh
- `getEnergyProduced(address)` - Total energy produced by seller
- `getEnergyConsumed(address)` - Total energy consumed by buyer

**Token Details:**
- Name: **Solar Energy Credit**
- Symbol: **SEC**
- Decimals: **18** (standard ERC-20)
- 1 token = 1 kWh of solar energy

---

## How It Works

### Listing Flow
1. Seller creates listing via API
2. Backend calls `mintEnergy()` on smart contract
3. Tokens are minted to seller's wallet
4. Transaction hash stored in database
5. Listing is active

### Purchase Flow
1. Buyer purchases energy via API
2. Backend calls `recordPurchase()` on smart contract
3. Tokens transferred from seller to buyer
4. Transaction hash stored in database
5. Purchase is complete

---

## Security Notes

⚠️ **IMPORTANT:**

1. **Never commit private keys to git**
2. **Never use default Hardhat keys in production**
3. **Use environment variables for secrets**
4. **Test on testnets before mainnet**
5. **Audit smart contracts before deploying to mainnet**

---

## Troubleshooting

### "Blockchain service unavailable"
- Check if `BLOCKCHAIN_ENABLED=True` in `.env`
- Verify RPC URL is correct and accessible
- Ensure blockchain node is running (for local development)

### "Contract not found"
- Run `npm run compile` in contracts directory
- Verify contract address in `.env`
- Check if contract is deployed on the network

### "Insufficient funds"
- Ensure deployer account has enough ETH/MATIC
- Get testnet tokens from faucets

### "Transaction failed"
- Check gas price and gas limit
- Verify account has permission (only owner can mint)
- Check blockchain explorer for detailed error

---

## Blockchain Explorers

View your transactions:

- **Sepolia:** https://sepolia.etherscan.io/
- **Mumbai:** https://mumbai.polygonscan.com/
- **Local:** http://127.0.0.1:8545 (no explorer for local)

---

## Next Steps

1. ✅ Choose your setup option (Local/Sepolia/Mumbai)
2. ✅ Deploy the smart contract
3. ✅ Update `.env` with blockchain settings
4. ✅ Restart FastAPI server
5. ✅ Test blockchain endpoints
6. ✅ Create listings and purchases with blockchain integration

---

## Resources

- **Hardhat Documentation:** https://hardhat.org/docs
- **Web3.py Documentation:** https://web3py.readthedocs.io/
- **OpenZeppelin Contracts:** https://docs.openzeppelin.com/contracts/
- **Ethereum Development:** https://ethereum.org/en/developers/

---

**Happy Building! 🚀⚡**

