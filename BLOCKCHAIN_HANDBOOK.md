# 🔗 Blockchain Integration Handbook

> **Goal**: Understand how Ethereum smart contracts will integrate with our RoofTop Solar Energy Marketplace

---

## 🎯 What We Need to Do

### **The Problem We're Solving**

Currently, our FastAPI backend handles:
- ✅ User registration (buyers & sellers)
- ✅ Authentication
- ✅ User management

**But we're missing**:
- ❌ How sellers list their solar energy
- ❌ How buyers purchase energy credits
- ❌ How payments are settled securely
- ❌ How to prove ownership of energy credits

**Solution**: Use Ethereum blockchain for transparent, trustless energy trading!

---

## 🌐 Why Blockchain? Why Ethereum?

### **Traditional Problems**:
| Problem | Impact |
|---------|--------|
| **Middleman fees** | 10-30% taken by energy companies |
| **No transparency** | Can't verify energy source |
| **Trust issues** | Who guarantees payment? |
| **Slow settlements** | Payments take days |

### **Blockchain Solutions**:
| Solution | Benefit |
|----------|---------|
| **Smart Contracts** | Automatic, trustless transactions |
| **ERC-20 Tokens** | Energy credits as tradeable tokens |
| **Immutable Records** | Transparent energy production/consumption |
| **Instant Settlement** | Payment when energy is delivered |

---

## 🏗️ Complete Architecture (FastAPI + Blockchain)

```
┌─────────────────────────────────────────────────────────────┐
│                         USER (Frontend)                      │
│                    (React/Vue/Mobile App)                    │
└──────────────────┬──────────────────┬───────────────────────┘
                   │                  │
                   │                  │
         ┌─────────▼────────┐   ┌────▼─────────────┐
         │  FASTAPI BACKEND │   │  METAMASK WALLET │
         │   (Our Project)  │   │  (User's Wallet) │
         └─────────┬────────┘   └────┬─────────────┘
                   │                  │
                   │                  │
         ┌─────────▼────────┐   ┌────▼─────────────┐
         │  POSTGRESQL DB   │   │ ETHEREUM NETWORK │
         │  (User Data)     │   │ (Smart Contract) │
         └──────────────────┘   └──────────────────┘
```

---

## 🔄 How They Work Together

### **Two-Layer System**:

| Layer | Technology | Stores | Purpose |
|-------|-----------|---------|---------|
| **Off-Chain** | FastAPI + PostgreSQL | User profiles, emails, preferences | Fast queries, traditional data |
| **On-Chain** | Ethereum Smart Contract | Energy tokens, transactions | Immutable, trustless, transparent |

---

## 📜 Smart Contract Overview

### **EnergyToken.sol** (ERC-20 Token)

**What it does**:
1. **Minting** — Sellers receive tokens for energy produced
2. **Trading** — Buyers purchase tokens with ETH
3. **Burning** — Tokens consumed when energy is used
4. **Tracking** — Immutable record of all transactions

**Example**:
```solidity
// Seller produces 100 kWh solar energy
energyToken.mint(sellerAddress, 100);  // Mint 100 tokens

// Buyer purchases 50 kWh
energyToken.transfer(buyerAddress, 50);  // Transfer 50 tokens

// Buyer consumes energy
energyToken.burn(50);  // Burn 50 tokens
```

---

## 🔗 Integration Flow (Complete User Journey)

### **1️⃣ Seller Lists Energy** (Off-Chain + On-Chain)

```
USER ACTION: Seller clicks "List 100 kWh for sale"
   ↓
FASTAPI: Create listing in PostgreSQL
   ↓
SMART CONTRACT: Mint 100 energy tokens to seller's wallet
   ↓
RESULT: Energy listed + tokens minted
```

**Code Flow**:
```python
# FastAPI endpoint
@router.post("/listings")
def create_listing(kWh: int, seller: User):
    # 1. Save to database
    listing = Listing(seller_id=seller.id, energy_kWh=kWh)
    db.add(listing)
    db.commit()
    
    # 2. Mint tokens on blockchain
    tx_hash = blockchain_service.mint_tokens(
        seller_wallet_address=seller.wallet_address,
        amount=kWh
    )
    
    # 3. Save transaction hash
    listing.blockchain_tx = tx_hash
    db.commit()
    
    return listing
```

---

### **2️⃣ Buyer Purchases Energy** (Off-Chain + On-Chain)

```
USER ACTION: Buyer clicks "Buy 50 kWh"
   ↓
FASTAPI: Create purchase record in PostgreSQL
   ↓
SMART CONTRACT: Transfer 50 tokens from seller to buyer
   ↓
SMART CONTRACT: Transfer ETH payment from buyer to seller
   ↓
RESULT: Buyer owns 50 energy tokens
```

**Code Flow**:
```python
# FastAPI endpoint
@router.post("/purchases")
def purchase_energy(listing_id: UUID, amount: int, buyer: User):
    # 1. Get listing
    listing = db.query(Listing).get(listing_id)
    
    # 2. Execute blockchain transaction
    tx_hash = blockchain_service.transfer_tokens(
        from_address=listing.seller.wallet_address,
        to_address=buyer.wallet_address,
        amount=amount
    )
    
    # 3. Save purchase to database
    purchase = Purchase(
        buyer_id=buyer.id,
        listing_id=listing_id,
        amount=amount,
        blockchain_tx=tx_hash
    )
    db.add(purchase)
    db.commit()
    
    return purchase
```

---

### **3️⃣ Buyer Consumes Energy** (On-Chain)

```
USER ACTION: Buyer's smart meter reports 50 kWh consumed
   ↓
SMART CONTRACT: Burn 50 tokens from buyer's wallet
   ↓
RESULT: Tokens destroyed, energy consumed
```

---

## 🛠️ What We'll Build

### **1. Smart Contract (Solidity)**

**File**: `contracts/EnergyToken.sol`

**Functions**:
```solidity
contract EnergyToken is ERC20 {
    // Mint tokens (seller produces energy)
    function mint(address to, uint256 amount) public onlyOwner;
    
    // Transfer tokens (buyer purchases)
    function transfer(address to, uint256 amount) public returns (bool);
    
    // Burn tokens (energy consumed)
    function burn(uint256 amount) public;
    
    // Get balance
    function balanceOf(address account) public view returns (uint256);
}
```

---

### **2. FastAPI Integration (Python)**

**New Files**:
```
app/
├── blockchain/
│   ├── __init__.py
│   ├── contract_abi.json      # Smart contract interface
│   ├── web3_client.py         # Web3.py connection
│   └── blockchain_service.py  # High-level functions
├── models/
│   ├── listing.py             # Energy listing model
│   └── purchase.py            # Purchase model
├── routers/
│   ├── listings.py            # /api/v1/listings
│   └── purchases.py           # /api/v1/purchases
└── services/
    ├── listing_service.py     # Listing business logic
    └── purchase_service.py    # Purchase business logic
```

---

### **3. Database Models (PostgreSQL)**

**New Tables**:

#### **listings** table:
```python
class Listing(Base):
    id = Column(UUID, primary_key=True)
    seller_id = Column(UUID, ForeignKey("users.id"))
    energy_kWh = Column(Integer)  # Amount of energy
    price_per_kWh = Column(Decimal)  # Price in ETH
    blockchain_tx = Column(String)  # Minting transaction hash
    created_at = Column(DateTime)
```

#### **purchases** table:
```python
class Purchase(Base):
    id = Column(UUID, primary_key=True)
    buyer_id = Column(UUID, ForeignKey("users.id"))
    listing_id = Column(UUID, ForeignKey("listings.id"))
    amount = Column(Integer)  # kWh purchased
    blockchain_tx = Column(String)  # Transfer transaction hash
    created_at = Column(DateTime)
```

---

## 🔐 Security & Trust

### **Why This is Secure**:

| Feature | How It Works |
|---------|-------------|
| **Wallet Verification** | Users prove wallet ownership by signing messages |
| **Immutable Records** | Blockchain transactions can't be changed |
| **Smart Contract** | Code is law - no human can cheat |
| **Transparent** | All transactions publicly visible |

### **User Wallet Flow**:

```
1. User registers on FastAPI → Provides email + password
2. User connects MetaMask → Provides wallet address
3. FastAPI asks user to sign message → "I own wallet 0x123..."
4. User signs with private key → Proves ownership
5. FastAPI verifies signature → Wallet linked to account
```

---

## 📊 Data Flow Example

### **Complete Transaction**:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SELLER PRODUCES ENERGY                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ FastAPI: POST /api/v1/listings                               │
│ Body: { energy_kWh: 100, price_per_kWh: 0.01 }             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ PostgreSQL: INSERT INTO listings                             │
│ (id, seller_id, energy_kWh, price_per_kWh, ...)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Smart Contract: mint(sellerWallet, 100)                     │
│ → Blockchain transaction                                     │
│ → Transaction hash: 0xabc123...                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ PostgreSQL: UPDATE listings SET blockchain_tx = '0xabc...'  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ RESULT: Seller has 100 energy tokens in wallet              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Concepts

### **ERC-20 Token**
- Standard for fungible tokens on Ethereum
- Like digital coins (1 token = 1 token, all identical)
- Easily tradeable on exchanges
- **In our case**: 1 token = 1 kWh of energy

### **Smart Contract**
- Code that runs on blockchain
- Automatically executes when conditions met
- Can't be stopped or changed (immutable)
- No middleman needed

### **Wallet Address**
- Like a bank account number (public)
- Example: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1`
- Used to receive/send tokens
- **In our DB**: Stored in `users.wallet_address`

### **Transaction Hash**
- Unique ID for blockchain transaction
- Proof that transaction occurred
- **In our DB**: Stored in `listings.blockchain_tx`, `purchases.blockchain_tx`

---

## 🔧 Technologies We'll Use

| Technology | Purpose | Example |
|------------|---------|---------|
| **Solidity** | Write smart contract | `EnergyToken.sol` |
| **Hardhat** | Develop, test, deploy contract | `npx hardhat compile` |
| **Web3.py** | Python library to interact with Ethereum | `web3.eth.contract()` |
| **Infura** | Connect to Ethereum network | `https://mainnet.infura.io/v3/...` |
| **MetaMask** | User's Ethereum wallet | Browser extension |

---

## 📝 Implementation Steps (What's Next)

### **Phase 1: Smart Contract** 🔨
1. Write `EnergyToken.sol` (ERC-20 token)
2. Add minting function (for sellers)
3. Add transfer function (for trading)
4. Add burn function (for consumption)
5. Test contract with Hardhat
6. Deploy to testnet (Sepolia)

### **Phase 2: FastAPI Integration** 🐍
1. Install Web3.py
2. Create `blockchain_service.py` (connect to Ethereum)
3. Add `listings.py` model (energy listings)
4. Add `purchases.py` model (transactions)
5. Create `/api/v1/listings` endpoints
6. Create `/api/v1/purchases` endpoints

### **Phase 3: Wallet Verification** 🔐
1. Add "Connect Wallet" endpoint
2. Generate signature challenge
3. Verify signature with Web3.py
4. Link wallet to user account

### **Phase 4: Testing** 🧪
1. Test smart contract functions
2. Test FastAPI integration
3. End-to-end transaction test
4. Security audit

---

## 💡 Why This Architecture?

### **Separation of Concerns**:

| Concern | Layer | Why |
|---------|-------|-----|
| **User Data** | PostgreSQL | Fast queries, privacy |
| **Business Logic** | FastAPI | Easy to change, flexible |
| **Financial Transactions** | Blockchain | Immutable, trustless |

### **Best of Both Worlds**:
- ✅ **Off-chain** (PostgreSQL + FastAPI) = Fast, cheap, private
- ✅ **On-chain** (Ethereum) = Secure, transparent, trustless

---

## 🎓 Simple Analogy

**Think of it like buying a house**:

| Step | Traditional | Our System |
|------|------------|------------|
| **Property Listing** | Real estate website | FastAPI (listings table) |
| **Ownership Proof** | Title deed | Blockchain (energy tokens) |
| **Payment** | Bank transfer | Ethereum transaction |
| **Record Keeping** | Government registry | Smart contract (immutable) |

---

## 🚀 End Goal

**Complete User Experience**:

```
1. Seller installs solar panels
   ↓
2. Seller lists energy on platform (FastAPI)
   ↓
3. Smart contract mints energy tokens
   ↓
4. Buyer browses listings (FastAPI)
   ↓
5. Buyer purchases energy with ETH
   ↓
6. Smart contract transfers tokens + payment
   ↓
7. Buyer consumes energy
   ↓
8. Smart contract burns tokens
   ↓
9. Transaction history visible on blockchain explorer
```

---

## 📋 TL;DR

**What**: Build smart contracts to handle energy token trading

**Why**: Enable trustless, transparent, peer-to-peer energy marketplace

**How**: 
- Smart contract (Solidity) = Energy tokens (ERC-20)
- FastAPI (Python) = Business logic & database
- Web3.py = Bridge between FastAPI and Ethereum

**Result**: Sellers mint tokens → Buyers purchase with ETH → Transparent, automatic settlement

---

**Next Step**: Write the `EnergyToken.sol` smart contract! 🔨

Let's start building the blockchain layer! 🚀

