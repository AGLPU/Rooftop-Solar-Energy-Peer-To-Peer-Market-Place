# 🌟 Blockchain Integration - Quick Reference

## What We Built

A complete Ethereum blockchain integration for the Solar Energy Marketplace that tokenizes solar energy as ERC-20 tokens.

---

## 📂 Files Created

### Smart Contracts (`/contracts`)
```
contracts/
├── EnergyToken.sol              # Main smart contract (ERC-20 token)
├── hardhat.config.js            # Hardhat configuration
├── package.json                 # Node.js dependencies
└── scripts/
    └── deploy.js                # Deployment script
```

### Backend Services (`/app`)
```
app/services/
└── blockchain_service.py        # Web3 integration service

app/routers/
└── blockchain.py                # Blockchain API endpoints
```

### Configuration
```
.env.example                     # Blockchain settings template
BLOCKCHAIN_SETUP.md              # Complete setup guide
setup_blockchain.bat             # Windows setup wizard
```

---

## 🚀 Quick Start (3 Steps)

### Step 1: Choose Your Mode

**Option A: With Blockchain (Full Features)**
```bash
# Install dependencies
cd contracts
npm install

# Start local blockchain (keep running)
npx hardhat node

# Deploy contract (new terminal)
npm run deploy:local

# Install Python web3
pip install web3
```

**Option B: Without Blockchain (Simpler)**
```env
# In .env file
BLOCKCHAIN_ENABLED=False
```

---

### Step 2: Configure `.env`

**With Blockchain:**
```env
BLOCKCHAIN_ENABLED=True
BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545
BLOCKCHAIN_NETWORK=localhost
BLOCKCHAIN_CONTRACT_ADDRESS=0x... (from deployment output)
BLOCKCHAIN_PRIVATE_KEY=ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

**Without Blockchain:**
```env
BLOCKCHAIN_ENABLED=False
```

---

### Step 3: Test the Integration

Start your FastAPI server:
```bash
uvicorn app.main:app --reload
```

**Test Blockchain Status:**
```bash
curl http://127.0.0.1:8000/api/v1/blockchain/status
```

**Check Token Balance:**
```bash
curl http://127.0.0.1:8000/api/v1/blockchain/balance/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1
```

---

## 🎯 How It Works

### Energy Listing Flow
```
1. Seller creates listing → API receives request
2. Backend mints energy tokens → Smart contract call
3. Tokens credited to seller's wallet → Blockchain transaction
4. Transaction hash saved to database → Record keeping
5. Listing is active ✅
```

### Energy Purchase Flow
```
1. Buyer purchases energy → API receives request
2. Backend records purchase → Smart contract call
3. Tokens transferred seller→buyer → Blockchain transaction
4. Transaction hash saved → Record keeping
5. Purchase complete ✅
```

---

## 📊 Smart Contract Functions

### For Platform (Owner Only)
```solidity
mintEnergy(seller, kWh, metadata)      // Mint tokens when energy is produced
recordPurchase(seller, buyer, kWh, price)  // Record purchase transaction
```

### For Users (Anyone)
```solidity
consumeEnergy(kWh)                     // Burn tokens after consumption
getEnergyBalance(address)              // Check token balance
getEnergyProduced(address)             // Check total production
getEnergyConsumed(address)             // Check total consumption
```

---

## 🔌 API Endpoints

### GET `/api/v1/blockchain/status`
Check if blockchain is connected and get network info.

**Response:**
```json
{
  "connected": true,
  "chain_id": 31337,
  "block_number": 42,
  "contract_address": "0x5FbDB...",
  "token_name": "Solar Energy Credit",
  "token_symbol": "SEC"
}
```

### GET `/api/v1/blockchain/balance/{address}`
Get energy token balance for a wallet.

**Response:**
```json
{
  "address": "0x742d35...",
  "balance_kwh": 1000,
  "available": true
}
```

---

## 🛠️ Testing Scenarios

### Test Wallet Addresses (Hardhat Default Accounts)
```
Account #0: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
Private Key: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

Account #1: 0x70997970C51812dc3A010C7d01b50e0d17dc79C8
Private Key: 0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d

Account #2: 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC
Private Key: 0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a
```

⚠️ **Never use these keys in production!** These are public test keys.

---

## 📱 Integration with Frontend

When building a frontend (React/Vue/Angular), use:

1. **MetaMask** for wallet connection
2. **ethers.js** or **web3.js** for contract interaction
3. **Contract ABI** from `contracts/artifacts/contracts/EnergyToken.sol/EnergyToken.json`

Example:
```javascript
const contractAddress = "0x...";
const abi = [...]; // From EnergyToken.json
const contract = new ethers.Contract(contractAddress, abi, signer);
const balance = await contract.getEnergyBalance(userAddress);
```

---

## 🔍 Debugging

### Check if Hardhat Node is Running
```bash
curl -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

### View Contract in Console
```bash
npx hardhat console --network localhost
```

### Check Transaction
```javascript
// In hardhat console
const tx = await ethers.provider.getTransaction("0x...");
console.log(tx);
```

---

## 💡 Tips

1. **Start Simple**: Begin with database-only mode, add blockchain later
2. **Use Local Network**: Test everything locally before deploying to testnet
3. **Save Gas**: Batch operations when possible
4. **Monitor Transactions**: Always check transaction status before confirming to user
5. **Handle Failures**: Blockchain calls can fail - always have fallback logic

---

## 📚 Next Steps

1. ✅ Test blockchain integration locally
2. ✅ Deploy to testnet (Sepolia/Mumbai)
3. ✅ Build frontend wallet integration
4. ✅ Add more smart contract features (escrow, ratings, etc.)
5. ✅ Audit contract before mainnet deployment

---

## 🆘 Need Help?

- **Setup Issues**: Check `BLOCKCHAIN_SETUP.md`
- **Smart Contract**: See `contracts/EnergyToken.sol` comments
- **API Integration**: See `app/services/blockchain_service.py`
- **Hardhat Docs**: https://hardhat.org/docs

---

**Built with ❤️ for Solar Energy Marketplace**

