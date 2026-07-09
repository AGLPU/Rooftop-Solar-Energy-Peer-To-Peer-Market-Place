# 🌞 RoofTop Solar Energy Marketplace
### Design Document — HLD | LLD | Problem Statement | Tech Stack

> **Use Case:** 10–15 PPT Slides | Hackathon Presentation
> **Version:** 1.0 | July 2026

---

---

## SLIDE 1 — TITLE

# RoofTop Solar Energy Marketplace
**Peer-to-Peer Renewable Energy Trading Platform**

> *"Turning every rooftop into a power plant and every homeowner into an energy entrepreneur."*

**Built with:** Python · FastAPI · PostgreSQL (Aurora) · Solidity · Ethereum · AI Chatbot

---

---

## SLIDE 2 — PROBLEM STATEMENT

### What Problem Are We Solving?

| # | Pain Point |
|---|-----------|
| 1 | Homeowners with rooftop solar panels **waste excess energy** — they can't sell it easily |
| 2 | Energy buyers (businesses, households) **pay high rates** to utility companies with no alternative |
| 3 | Traditional energy trading requires **middlemen** (brokers, utilities) who take large cuts |
| 4 | There is **no transparent, trustless way** to verify energy trades and payments |
| 5 | Buyers have **no AI guidance** to find the best energy deal or predict prices |

### Our Answer
A **decentralized, peer-to-peer solar energy marketplace** where:
- **Sellers** list their surplus rooftop solar energy
- **Buyers** purchase energy credits directly
- **Blockchain** records every trade — immutable, transparent, no middleman
- **AI Chatbot** helps users make smart decisions

> *This platform democratizes energy trading, making renewable energy accessible and profitable for everyone.*

---

---

## SLIDE 3 — SOLUTION OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                    ROOFTOP SOLAR MARKETPLACE                │
│                                                             │
│  👤 SELLER                                    👤 BUYER      │
│  Lists solar energy →    PLATFORM    ← Browses & Buys       │
│                             │                               │
│                    ┌────────┴────────┐                      │
│                    │  FastAPI (REST) │                      │
│                    └────────┬────────┘                      │
│             ┌───────────────┼───────────────┐               │
│         🗄️  DB          🔗 Blockchain      🤖 AI           │
│      Aurora RDS        EnergyToken.sol    Chatbot           │
│      PostgreSQL         (Ethereum)       Prediction         │
└─────────────────────────────────────────────────────────────┘
```

**Key Value Propositions:**
- ✅ Direct P2P energy trading — no middleman
- ✅ Blockchain guarantees — every trade is verifiable on-chain
- ✅ AI predictions — smart price guidance for buyers & sellers
- ✅ Cloud-native — AWS Aurora RDS with read/write replica separation

---

---

## SLIDE 4 — HIGH-LEVEL DESIGN (HLD)

```
                          ┌──────────────────────────────────────────────┐
                          │               CLIENT LAYER                    │
                          │   Postman / Web App / Mobile App              │
                          └──────────────────┬───────────────────────────┘
                                             │  HTTPS REST API
                          ┌──────────────────▼───────────────────────────┐
                          │            API GATEWAY LAYER                  │
                          │      FastAPI + Uvicorn (ASGI Server)          │
                          │   JWT Auth Middleware | CORS | Rate Limit     │
                          └──────────┬──────────────────┬────────────────┘
                                     │                  │
              ┌──────────────────────▼──┐    ┌──────────▼──────────────────┐
              │     BUSINESS LAYER       │    │      BLOCKCHAIN LAYER        │
              │  UserService             │    │  BlockchainService           │
              │  ListingService          │    │  EnergyToken.sol (Solidity)  │
              │  PurchaseService         │    │  Web3.py → Ethereum Node     │
              └──────────┬──────────────┘    └──────────┬──────────────────┘
                         │                              │ (async, optional)
              ┌──────────▼──────────────────────────────▼──────────────────┐
              │                     DATA LAYER                              │
              │   AWS Aurora PostgreSQL (Read/Write Replica Separation)     │
              │   Schema: Dummy  |  Tables: users, listings, purchases      │
              └─────────────────────────────────────────────────────────────┘
                                             │
              ┌──────────────────────────────▼─────────────────────────────┐
              │                     AI LAYER (Planned)                      │
              │         Price Prediction + AI Chatbot (GPT/OpenAI)          │
              └─────────────────────────────────────────────────────────────┘
```

---

---

## SLIDE 5 — TECH STACK

### Backend
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | **FastAPI 0.111** | REST API, auto Swagger docs |
| Server | **Uvicorn (ASGI)** | Async HTTP server |
| Language | **Python 3.12** | Core application logic |
| ORM | **SQLAlchemy 2.0** | Database models & queries |
| Migrations | **Alembic 1.13** | DB schema version control |
| Validation | **Pydantic v2** | Input/output data validation |
| Auth | **JWT (python-jose)** | Secure token-based auth |
| Passwords | **Passlib + bcrypt** | Password hashing |
| Config | **Pydantic-Settings** | `.env` config management |

### Database
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Cloud DB | **AWS Aurora PostgreSQL** | Managed, scalable DB |
| Driver | **psycopg2-binary** | Python ↔ PostgreSQL connector |
| Pattern | **Read/Write Replica** | Write → Primary, Read → Replica |
| Schema | **`Dummy` schema** | Logical DB separation |

### Blockchain
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Smart Contract | **Solidity (.sol)** | EnergyToken contract |
| Network | **Ethereum (EVM)** | Blockchain platform |
| Dev Toolchain | **Hardhat (Node.js)** | Compile, test, deploy contracts |
| Python Bridge | **Web3.py (web3==7.16)** | FastAPI ↔ Ethereum connection |
| Contract Pattern | **ERC-20 + Custom** | Token + energy record functions |

### AI Layer *(Planned)*
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Chatbot | **OpenAI GPT API** | Natural language energy advisor |
| Prediction | **scikit-learn / TensorFlow** | Energy price forecasting |
| Integration | **FastAPI AI Router** | `/api/v1/ai/chat`, `/predict` |

### Infrastructure
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Cloud | **AWS** | Hosting |
| DB Cluster | **AWS Aurora RDS** | PostgreSQL managed cluster |
| Secrets | **AWS Secrets Manager** | Credentials (planned) |
| CI/CD | **GitHub** | Version control |

---

---

## SLIDE 6 — BUSINESS LAYER (Deep Dive)

### What the Business Layer Does
All business logic lives in `app/services/` — routers are thin, services are smart.

```
app/
├── routers/          ← HTTP endpoints (thin layer, just routes)
│   ├── users.py      → /api/v1/users/*
│   ├── listings.py   → /api/v1/listings/*
│   ├── purchases.py  → /api/v1/purchases/*
│   └── blockchain.py → /api/v1/blockchain/*
│
├── services/         ← Business logic (all rules live here)
│   ├── user_service.py      → Register, Login, JWT, Password
│   ├── listing_service.py   → Create listing, filter, paginate
│   └── purchase_service.py  → Buy energy, update status
│
├── models/           ← Database table definitions (SQLAlchemy ORM)
│   ├── user.py       → users table
│   ├── listing.py    → listings table
│   └── purchase.py   → purchases table
│
└── schemas/          ← Request/Response contracts (Pydantic)
    ├── user.py       → UserRegisterRequest, UserResponse, TokenResponse
    ├── listing.py    → ListingCreateRequest, ListingResponse
    └── purchase.py   → PurchaseRequest, PurchaseResponse
```

### Key Business API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users/register` | Register buyer/seller |
| POST | `/api/v1/users/login` | Login → JWT token |
| GET | `/api/v1/users/me` | Current user profile |
| POST | `/api/v1/listings/` | Seller creates energy listing |
| GET | `/api/v1/listings/` | Browse all available listings |
| GET | `/api/v1/listings/{id}` | View listing details |
| POST | `/api/v1/purchases/` | Buyer purchases energy |
| GET | `/api/v1/purchases/my` | My purchase history |
| GET | `/api/v1/blockchain/status` | Check blockchain connection |

### User Roles
| Role | Can Do |
|------|--------|
| **SELLER** | Create listings, view sales, receive ETH payments |
| **BUYER** | Browse listings, purchase energy credits |
| **ADMIN** | Manage users, moderate platform |

---

---

## SLIDE 7 — BLOCKCHAIN LAYER (Deep Dive)

### How Blockchain Fits In

```
  Seller creates listing            Buyer purchases energy
         │                                   │
         ▼                                   ▼
  FastAPI saves to DB           FastAPI calls BlockchainService
         │                                   │
         └─────────────┬─────────────────────┘
                       ▼
            Web3.py calls Ethereum Node
                       │
                       ▼
         EnergyToken.sol Smart Contract
         ┌─────────────────────────────────┐
         │  mintEnergy(seller, kWh)         │  ← tokens created for seller
         │  recordPurchase(seller, buyer)   │  ← trade recorded on-chain
         │  getEnergyBalance(address)       │  ← check wallet balance
         └─────────────────────────────────┘
                       │
                       ▼
              Ethereum Blockchain
           (Immutable transaction log)
```

### Smart Contract: `EnergyToken.sol`
- Lives in sibling project: `solar-blockchain/`
- Built with **Hardhat** (Node.js toolchain)
- **ERC-20 compatible** — energy = tokens (1 token = 1 kWh)
- Key functions:
  - `mintEnergy()` — platform mints tokens for verified sellers
  - `recordPurchase()` — logs buyer↔seller trade on-chain
  - `getEnergyBalance()` — query wallet's energy token balance

### Blockchain is Optional (Graceful Degradation)
```
BLOCKCHAIN_ENABLED=false → Server runs in "Database-Only" mode
BLOCKCHAIN_ENABLED=true  → Full P2P trading with on-chain settlement
```
> This means the app works perfectly during development without Ethereum.

### Wallet Integration
- Users register with an **Ethereum wallet address** (`0x...` 42-char format)
- Stored in `users.wallet_address` column
- Used for on-chain energy minting and purchase recording

---

---

## SLIDE 8 — AI LAYER (Planned)

### Why AI?
The platform has data that AI can use to make it smarter:
- Historical energy prices per listing
- Location-based solar production patterns
- Buyer/Seller behavior patterns

### Planned AI Features

#### 1. 🤖 AI Energy Advisor Chatbot
```
User: "I have 500 kWh to sell in Toronto, what price should I set?"
Bot:  "Based on current market, similar listings in Toronto are priced
       at 0.0045–0.0060 ETH/kWh. I recommend 0.0052 ETH/kWh."
```
- **Tech:** OpenAI GPT API + LangChain
- **Endpoint:** `POST /api/v1/ai/chat`

#### 2. 📈 Energy Price Prediction
- Predict optimal listing price based on location + season + demand
- **Tech:** scikit-learn regression model trained on marketplace data
- **Endpoint:** `GET /api/v1/ai/predict-price?kwh=500&location=Toronto`

#### 3. 🔋 Demand Forecasting
- Predict energy demand for a region for next 7 days
- Helps sellers know WHEN to list for maximum profit

### AI Integration Architecture
```
FastAPI
  └── /api/v1/ai/
        ├── chat          → OpenAI GPT (conversational)
        ├── predict-price → ML model (pricing)
        └── demand        → Forecasting model
```

---

---

## SLIDE 9 — LOW-LEVEL DESIGN (LLD) — Database


### Read/Write Replica Pattern
```
WRITE operations (INSERT, UPDATE, DELETE) → PRIMARY endpoint
  └── AWS Aurora Writer: cluster-cmlzbcc6shng.ca-central-1.rds.amazonaws.com

READ operations (SELECT, GET) → REPLICA endpoint
  └── AWS Aurora Reader: cluster-ro-cmlzbcc6shng.ca-central-1.rds.amazonaws.com
```
> Why? Aurora replica handles read traffic → primary is free for writes → better performance.

---

---

## SLIDE 10 — LOW-LEVEL DESIGN (LLD) — Request Flow

### Request Flow (Register User Example)
```
POST /api/v1/users/register
    │
    ▼ Router (users.py)
    │   validates schema via Pydantic → UserRegisterRequest
    │
    ▼ Service (user_service.py)
    │   check duplicate email/username
    │   hash password (bcrypt)
    │   create User object
    │   save to DB (write engine → Aurora Primary)
    │
    ▼ Response
        returns UserResponse (Pydantic) → JSON
```

---

---

## SLIDE 11 — SECURITY DESIGN

### Security Layers

| Layer | Mechanism |
|-------|-----------|
| Passwords | bcrypt hashed — never stored as plain text |
| Auth | JWT Bearer Token — stateless, signed with SECRET_KEY |
| Token Expiry | Access token: 60 min \| Refresh token: 7 days |
| DB Connection | SSL required (`sslmode=require`) |
| Schema Isolation | Dedicated `Dummy` schema — isolated from other apps |
| CORS | Only allowed origins can call the API |
| Input Validation | Pydantic validates every request body — rejects bad data |
| Wallet Address | Validated as `0x` + 40 hex chars format |

### JWT Token Flow
```
Login → POST /api/v1/users/login
  │
  └── Returns: { access_token, refresh_token, expires_in }

Protected API → GET /api/v1/users/me
  │
  └── Header: Authorization: Bearer <access_token>
        └── Decoded → get_current_user → inject User object
```

---

---

## SLIDE 12 — INFRASTRUCTURE & DEPLOYMENT

```
                     ┌─────────────────────────────────┐
                     │           AWS CLOUD              │
                     │                                  │
                     │  ┌──────────────────────────┐   │
                     │  │  Aurora PostgreSQL Cluster│   │
                     │  │                          │   │
                     │  │  [Writer Instance]        │   │
                     │  │  cluster-cmlzbcc6shng ... │   │
                     │  │           │               │   │
                     │  │  [Reader Instance]        │   │
                     │  │  cluster-ro-cmlzbcc6s ... │   │
                     │  └──────────────────────────┘   │
                     │                                  │
                     │  ┌──────────────────────────┐   │
                     │  │   AWS Secrets Manager     │   │
                     │  │  (DB credentials — TBD)  │   │
                     │  └──────────────────────────┘   │
                     └─────────────────────────────────┘
                                    │
                     ┌──────────────▼──────────────────┐
                     │       LOCAL / SERVER              │
                     │  Python 3.12 + Uvicorn            │
                     │  FastAPI App                      │
                     │  .env (config)                    │
                     └─────────────────────────────────┘
```

### Environment Configuration (`.env`)
```
DATABASE_HOST = Aurora Writer endpoint
DATABASE_READ_HOST = Aurora Reader endpoint
DATABASE_SCHEMA = Dummy
SECRET_KEY = JWT signing key
BLOCKCHAIN_ENABLED = true/false
BLOCKCHAIN_RPC_URL = Ethereum node URL
```

---

---

## SLIDE 13 — FUTURE ENHANCEMENTS

### Priority Roadmap

| Priority | Feature | Description |
|----------|---------|-------------|
| 🔴 High | **AWS Secrets Manager** | Move DB credentials out of `.env` → Secrets Manager |
| 🔴 High | **AI Chatbot (GPT)** | Energy advisor via OpenAI API |
| 🔴 High | **Deploy Smart Contract** | Deploy EnergyToken.sol to Ethereum Sepolia testnet |
| 🟡 Medium | **Email Verification** | Send OTP after user registration |
| 🟡 Medium | **Price Prediction ML** | Train model on listing history |
| 🟡 Medium | **Alembic Migrations** | Full DB migration management |
| 🟡 Medium | **Frontend (React)** | Web UI for buyers and sellers |
| 🟢 Low | **Push Notifications** | Alert buyer when listing matches price |
| 🟢 Low | **Carbon Credit Tracking** | Track CO₂ saved per kWh sold |
| 🟢 Low | **IoT Integration** | Real-time solar meter data feed |
| 🟢 Low | **Mobile App** | iOS/Android buyer/seller app |

### AI Enhancement Vision
```
Current:  Manual browsing → pick listing → buy
Future:   AI suggests listings → price predicts → auto-negotiate → smart contract settles
```

---

---

## SLIDE 14 — SUMMARY

### What We Built

| Component | Status |
|-----------|--------|
| FastAPI REST API | ✅ Done |
| User Registration & Login (JWT) | ✅ Done |
| Energy Listings (CRUD) | ✅ Done |
| Energy Purchases | ✅ Done |
| Read/Write Replica DB (Aurora) | ✅ Done |
| Blockchain Service (Web3.py) | ✅ Done |
| Smart Contract (Solidity) | ✅ Done |
| AI Chatbot | 🔲 Planned |
| Frontend | 🔲 Planned |
| AWS Secrets Manager | 🔲 Planned |

### Business Impact
- 🌱 **Environmental** — accelerates renewable energy adoption
- 💰 **Economic** — sellers earn from wasted energy; buyers save vs utility
- 🔗 **Trust** — blockchain eliminates fraud in energy trades
- 🤖 **Intelligence** — AI makes optimal pricing accessible to everyone

---

---

## Quick Reference — One-Liner Descriptions

| Layer | One-Line Summary |
|-------|-----------------|
| **FastAPI** | The web framework that handles HTTP requests and returns JSON responses |
| **SQLAlchemy** | Maps Python classes to database tables — no raw SQL needed |
| **Pydantic** | Validates every incoming request — wrong data is rejected automatically |
| **JWT** | Secure tokens that prove "who you are" without storing sessions |
| **Aurora RDS** | AWS-managed PostgreSQL — highly available, auto-scales |
| **Web3.py** | Python library that lets FastAPI talk to Ethereum blockchain |
| **Solidity** | Language to write smart contracts — code that runs on Ethereum |
| **Hardhat** | Node.js tool to compile and deploy Solidity contracts |
| **Alembic** | Tracks database schema changes like Git tracks code |
| **Uvicorn** | The server that runs FastAPI in production (async, fast) |

---

*Document generated: July 2026 | Project: RoofTop Solar Energy Marketplace*

