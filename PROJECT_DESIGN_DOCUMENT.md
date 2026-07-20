# 🌿 Green Energy Marketplace
### Design Document — HLD | LLD | Problem Statement | Tech Stack

> **Use Case:** 10–15 PPT Slides | Hackathon Presentation
> **Version:** 2.0 | July 2026

---

## SLIDE 1 — TITLE

# Green Energy Marketplace
**Peer-to-Peer Renewable Energy Trading Platform**

> *"Empowering communities to trade clean energy — trustlessly, transparently and profitably."*

**Built with:** Python · FastAPI · PostgreSQL (Neon) · Solidity · Ethereum · AWS Bedrock AI

---

## SLIDE 2 — PROBLEM STATEMENT

### What Problem Are We Solving?

| # | Pain Point |
|---|-----------|
| 1 | Energy producers waste surplus energy — no easy way to sell it |
| 2 | Buyers pay high utility rates with no transparent alternatives |
| 3 | Traditional trading requires middlemen who take large cuts |
| 4 | No trustless way to verify trades — double counting & fraud possible |
| 5 | Sellers/Buyers lack AI guidance to maximize trading profit |

### Our Answer
A **decentralized, peer-to-peer green energy marketplace** where:
- **Sellers** list surplus energy (Solar, Wind, Hydro, Biomass, Geothermal, Tidal)
- **Buyers** purchase energy credits directly — no middleman
- **Blockchain** records every trade — immutable, verifiable, trustless
- **AI Agent** analyzes historical data and predicts optimal pricing

---

## SLIDE 3 — SOLUTION OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                   GREEN ENERGY MARKETPLACE                  │
│                                                             │
│  👤 SELLER                                    👤 BUYER      │
│  Lists energy →      PLATFORM      ← Browses & Buys        │
│                          │                                  │
│                 ┌────────┴────────┐                         │
│                 │  FastAPI (REST) │                         │
│                 └────────┬────────┘                         │
│          ┌───────────────┼───────────────┐                  │
│      🗄️ DB          🔗 Blockchain      🤖 AI Agent         │
│    Neon PostgreSQL   EnergyToken.sol   Bedrock + RAG        │
│    (Render hosted)    (Ethereum)      Prediction Engine     │
└─────────────────────────────────────────────────────────────┘
```

**Key Value Propositions:**
- ✅ Multi-source energy trading — Solar, Wind, Hydro, Biomass and more
- ✅ Blockchain guarantees — every trade is verifiable, tamper-proof on-chain
- ✅ AI-powered insights — smart predictions using historical trading data
- ✅ Cloud-native — Render + Neon PostgreSQL + AWS Bedrock

---

## SLIDE 4 — HIGH-LEVEL DESIGN (HLD)

```
                     ┌──────────────────────────────────────────┐
                     │              CLIENT LAYER                 │
                     │   Web App / Mobile App / Postman          │
                     └─────────────────┬────────────────────────┘
                                       │  HTTPS REST API
                     ┌─────────────────▼────────────────────────┐
                     │           API GATEWAY LAYER               │
                     │    FastAPI + Uvicorn (ASGI Server)        │
                     │  JWT Auth | CORS | Input Validation       │
                     └──────────┬───────────────┬───────────────┘
                                │               │
           ┌────────────────────▼──┐  ┌─────────▼──────────────────┐
           │    BUSINESS LAYER      │  │     BLOCKCHAIN LAYER        │
           │  UserService           │  │  BlockchainService          │
           │  ListingService        │  │  EnergyToken.sol (Solidity) │
           │  PurchaseService       │  │  Web3.py → Ethereum Node    │
           └──────────┬────────────┘  └─────────┬──────────────────┘
                      │                          │
           ┌──────────▼──────────────────────────▼──────────────────┐
           │                    DATA LAYER                           │
           │        Neon PostgreSQL (hosted on Render)               │
           │        Tables: users, listings, purchases               │
           └─────────────────────────────────────────────────────────┘
                                      │
           ┌──────────────────────────▼─────────────────────────────┐
           │                    AI AGENT LAYER                       │
           │  RAG (OpenSearch + VectorDB + S3) + Bedrock LLM        │
           │  Prediction Engine → Graphs + Forecast Reports         │
           └─────────────────────────────────────────────────────────┘
```

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

### Database & Deployment
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Cloud DB | **Neon PostgreSQL** | Serverless, auto-scales |
| Hosting | **Render.com** | Free-tier cloud deployment |
| Driver | **psycopg2-binary** | Python ↔ PostgreSQL connector |
| Schema | **`public` schema** | Standard layout |

### Blockchain
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Smart Contract | **Solidity (.sol)** | EnergyToken contract |
| Network | **Ethereum Sepolia** | Testnet blockchain |
| Dev Toolchain | **Hardhat (Node.js)** | Compile, test, deploy |
| Python Bridge | **Web3.py (web3==6.15)** | FastAPI ↔ Ethereum |
| Contract Pattern | **ERC-20 + Custom** | Token + energy records |

### AI Layer
| Layer | Technology | Purpose |
|-------|-----------|---------|
| LLM | **AWS Bedrock (Claude)** | Natural language reasoning |
| Knowledge Base | **S3 + OpenSearch** | Document storage & indexing |
| Vector Search | **VectorDB (OpenSearch k-NN)** | Semantic similarity search |
| Embeddings | **Bedrock Titan Embeddings** | Text → vector conversion |
| Tokenizer | **Bedrock tokenizer** | Chunk documents for RAG |
| Prediction | **Custom ML Engine** | Price & demand forecasting |

---

## SLIDE 6 — ENERGY SOURCES

### Supported Green Energy Types

| Source | Token Symbol | Real-World Example |
|--------|-------------|-------------------|
| ☀️ **SOLAR** | SEC-SOLAR | Rooftop solar panels |
| 💨 **WIND** | SEC-WIND | Backyard wind turbines |
| 💧 **HYDRO** | SEC-HYDRO | Small-scale run-of-river |
| 🌿 **BIOMASS** | SEC-BIOMASS | Farm biogas digesters |
| 🌋 **GEOTHERMAL** | SEC-GEO | Ground-source heat pumps |
| 🌊 **TIDAL** | SEC-TIDAL | Coastal wave energy |
| ♻️ **OTHER** | SEC-OTHER | Any certified green source |

### API Filter Support
```
GET /api/v1/listings/active?energy_source=WIND   ← filter by source
GET /api/v1/listings/?energy_source=SOLAR        ← filter by source
POST /api/v1/listings/ { "energy_source": "HYDRO", ... }
```

---

## SLIDE 7 — BLOCKCHAIN LAYER (Deep Dive)

### How Blockchain Solves the Core Problems

#### The Problem Without Blockchain
```
Seller claims: "I produced 100 kWh"  ← just a number in a database
Buyer pays for 100 kWh               ← no proof it's real
Seller edits DB: changes 100 → 150   ← fraud! no one knows
Same energy sold to 2 buyers         ← double counting!
```

#### One Real Example — Trustless Trade

> **Aman (Seller)** has 50 kWh of wind energy.
> **Rahul (Buyer)** wants to buy 50 kWh.

```
Step 1 — Aman creates listing
  FastAPI → mintEnergy("0xAman", 50kWh, price=1ETH)
  ✅ Blockchain mints 50 SEC tokens to Aman's wallet
  ✅ TX Hash: 0xf490d9ea... stored in DB (immutable proof)

Step 2 — Rahul buys the listing
  FastAPI → recordPurchase("0xAman", "0xRahul", 50kWh)
  ✅ 50 SEC tokens transferred Aman → Rahul on-chain
  ✅ TX Hash: 0xb71c2c... stored in DB

Step 3 — Anyone verifies
  GET /blockchain/verify/listing/{id}
  ✅ DB hash matches on-chain hash → VERIFIED
  ✅ Aman's balance is now 0 — cannot sell same energy again
```

#### How Each Guarantee Works

| Guarantee | How |
|-----------|-----|
| **Trustless** | No middleman — smart contract executes automatically |
| **No Double Counting** | Tokens are burned on transfer — Aman's balance = 0 after sale |
| **Immutability** | TX hash stored on Ethereum — cannot be edited or deleted |
| **Tamper Detection** | SHA256 hash of listing fields stored on-chain — any DB edit = TAMPERED |
| **P2P** | Tokens move wallet-to-wallet — platform never holds energy credits |

#### Tamper Detection Example
```
DB record:  price_per_kwh = 3.00  ← someone edited it!
On-chain:   price_per_kwh = 1.00  ← original value

GET /blockchain/verify/listing/{id}
→ { "integrity": { "status": "TAMPERED",
    "checks": ["PRICE MISMATCH: DB=3.00 but blockchain=1.00"] } }
```

---

## SLIDE 8 — AI AGENT LAYER (Deep Dive)

### Architecture: RAG + Prediction Engine

```
User Question / Request
        │
        ▼
┌─────────────────────────────────────────────────────┐
│                   AI AGENT                          │
│                                                     │
│  ┌──────────────┐      ┌─────────────────────────┐  │
│  │  RAG Engine  │      │   Prediction Engine     │  │
│  │              │      │                         │  │
│  │ S3 (docs)    │      │ Invokes FastAPI          │  │
│  │    ↓         │      │ GET /purchases/history  │  │
│  │ Tokenizer    │      │ GET /listings/analytics │  │
│  │    ↓         │      │         ↓               │  │
│  │ Embeddings   │      │  Historical Data        │  │
│  │ (Bedrock     │      │         ↓               │  │
│  │  Titan)      │      │  ML Forecast Model      │  │
│  │    ↓         │      │         ↓               │  │
│  │ VectorDB     │      │  Price / Demand Graph   │  │
│  │ (OpenSearch) │      │  Forecast Report        │  │
│  └──────┬───────┘      └──────────┬──────────────┘  │
│         └──────────┬──────────────┘                  │
│                    ▼                                  │
│           AWS Bedrock (Claude)                       │
│           Final Answer / Report                      │
└─────────────────────────────────────────────────────┘
```

### RAG Flow — Static Knowledge Q&A

```
1. Knowledge docs stored in S3
   (energy regulations, trading guides, platform FAQs)

2. Tokenizer chunks documents → Bedrock Titan creates embeddings
   → stored in OpenSearch VectorDB

3. User asks: "What is the best time to sell wind energy?"
   → Question embedded → VectorDB k-NN search → top-k docs retrieved
   → Bedrock Claude answers using retrieved context
```

### Prediction Engine Flow — Agentic Behavior

```
User: "Show me my energy revenue forecast for next 30 days"
        │
        ▼
AI Agent invokes internal APIs autonomously:
  → GET /api/v1/purchases/history?seller_id=X&days=90
  → GET /api/v1/listings/analytics?seller_id=X
        │
        ▼
ML Model processes historical data:
  - Past prices, volumes, seasonal patterns
  - Location-based demand trends
        │
        ▼
Output delivered to Seller:
  📊 Revenue forecast chart (next 30 days)
  📈 Optimal price recommendation per kWh
  🔋 Demand prediction by energy source
  💡 "List 100 kWh WIND on Friday — 23% higher demand"
```

### Who Benefits

| User | AI Feature | Value |
|------|-----------|-------|
| **Seller** | Price prediction + demand forecast | List at optimal price, maximize revenue |
| **Buyer** | Price trend analysis + best deal alert | Buy at lowest price, right timing |
| **Both** | RAG chatbot — platform Q&A | Instant answers on trading rules |
| **Admin** | Anomaly detection in trades | Fraud/tamper alerts across platform |

---

## SLIDE 9 — LOW-LEVEL DESIGN (LLD) — Database

### Database Schema: `public` (Neon PostgreSQL)

#### Table: `users`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | Auto-generated |
| email | VARCHAR(255) | Unique, indexed |
| username | VARCHAR(100) | Unique, indexed |
| hashed_password | VARCHAR(255) | bcrypt hashed |
| role | ENUM | BUYER / SELLER / ADMIN |
| status | ENUM | ACTIVE / INACTIVE / BANNED |
| wallet_address | VARCHAR(42) | Ethereum `0x...` address |
| is_verified | BOOLEAN | Email verification |

#### Table: `listings`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| seller_id | UUID (FK → users) | |
| energy_kwh | INTEGER | Amount available |
| price_per_kwh | NUMERIC(10,6) | Price in ETH |
| energy_source | ENUM | SOLAR/WIND/HYDRO/BIOMASS/GEOTHERMAL/TIDAL/OTHER |
| location | VARCHAR(200) | City/region (immutable after mint) |
| status | ENUM | ACTIVE/SOLD/EXPIRED/CANCELLED |
| blockchain_tx_hash | VARCHAR(66) | Ethereum tx hash (tamper proof) |
| expires_at | TIMESTAMP | Immutable after mint |

#### Table: `purchases`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| buyer_id | UUID (FK → users) | |
| seller_id | UUID (FK → users) | |
| listing_id | UUID (FK → listings) | |
| energy_kwh | INTEGER | Amount bought |
| total_price | NUMERIC(12,6) | In ETH |
| status | ENUM | PENDING/COMPLETED/FAILED/REFUNDED/CONSUMED |
| blockchain_tx_hash | VARCHAR(66) | On-chain proof |
| consume_tx_hash | VARCHAR(66) | Burn proof when energy used |

### Blockchain Immutability Rules
```
Fields stored on-chain at mint (CANNOT change in DB):
  energy_kwh, price_per_kwh, energy_source,
  location, expires_at, seller_id, created_at

Any DB edit to above → verify endpoint returns TAMPERED ⚠️

Mutable fields (cosmetic only):
  title, description
```

---

## SLIDE 10 — APPLICATION STRUCTURE

```
rooftop-solar-marketplace/
│
├── app/
│   ├── main.py                   ← FastAPI app, middleware, routers
│   ├── config.py                 ← Settings (DATABASE_URL, BLOCKCHAIN, AI)
│   ├── database.py               ← SQLAlchemy engine (Neon PostgreSQL)
│   │
│   ├── models/                   ← DB table definitions
│   │   ├── user.py               → UserRole, UserStatus enums
│   │   ├── listing.py            → ListingStatus, EnergySource enums
│   │   └── purchase.py           → PurchaseStatus enum
│   │
│   ├── schemas/                  ← Pydantic request/response contracts
│   ├── services/
│   │   ├── user_service.py       → Auth, JWT, password
│   │   ├── listing_service.py    → CRUD, filters by energy_source
│   │   ├── purchase_service.py   → Buy energy, consume tokens
│   │   └── blockchain_service.py → Web3, mint, verify, tamper detection
│   │
│   ├── routers/
│   │   ├── users.py              → /api/v1/users/*
│   │   ├── listings.py           → /api/v1/listings/*
│   │   ├── purchases.py          → /api/v1/purchases/*
│   │   └── blockchain.py         → /api/v1/blockchain/*
│   │
│   └── blockchain/
│       └── EnergyToken.json      ← Bundled ABI (self-contained deploy)
│
├── alembic/versions/             ← DB migrations (0001→0004)
├── Dockerfile                    ← Container build
├── render.yaml                   ← Render deployment config
└── requirements.txt              ← Python dependencies (web3, fastapi...)
```

---

## SLIDE 11 — SECURITY DESIGN

| Layer | Mechanism |
|-------|-----------|
| Passwords | bcrypt hashed — never stored plain text |
| Auth | JWT Bearer Token — stateless, signed with SECRET_KEY |
| Token Expiry | Access: 60 min \| Refresh: 7 days |
| DB Connection | SSL required (`sslmode=require`) |
| CORS | Configurable allowed origins |
| Input Validation | Pydantic validates every request |
| Blockchain Keys | Private key in `.env` (gitignored) — AWS KMS for production |
| Tamper Detection | SHA256 hash of immutable fields stored on-chain |
| Immutable Fields | Blocked at API level after blockchain mint |

---

## SLIDE 12 — BLOCKCHAIN AUDIT ENDPOINTS

| Endpoint | Who | Purpose |
|----------|-----|---------|
| `GET /blockchain/status` | Anyone | Network + contract info + Etherscan links |
| `GET /blockchain/verify/listing/{id}` | Buyer/Seller/Admin | VERIFIED or TAMPERED check |
| `GET /blockchain/verify/purchase/{id}` | Buyer/Seller/Admin | Purchase proof on-chain |
| `GET /blockchain/my/balance` | Seller/Buyer | My SEC token balance |
| `GET /blockchain/my/listings` | Seller | All my listings with blockchain status |
| `GET /blockchain/admin/audit/listings` | Admin | Bulk tamper scan — all listings |
| `GET /blockchain/admin/platform-wallet` | Admin | ETH balance + low gas warning |

---

## SLIDE 13 — PUBLIC AI KNOWLEDGE BASE ENDPOINTS

> No authentication required. These are the **data feed** for the AI Agent.
> The Prediction Engine calls these endpoints autonomously to gather market signals.

### Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/public/listings` | All listings with supply summary per source |
| `GET /api/v1/public/listings/active` | Active listings with market share % + location breakdown |
| `GET /api/v1/public/purchases` | Purchase history with demand stats + price volatility per source |

### How Each Endpoint Powers the AI Agent

#### `GET /public/listings` — answers:
| # | Question |
|---|---------|
| 1 | Which renewable source currently has the highest available supply? |
| 11 | What % of active marketplace supply is Solar, Wind, Hydro? |
| 7 | Which location has the greatest wind-credit supply? |

**Key fields returned:** `supply_by_source` (count, total_kwh, avg/min/max price per source+status)

#### `GET /public/listings/active` — answers:
| # | Question |
|---|---------|
| 2 | What % of active supply comes from Solar, Wind, Small Hydro? |
| 10 | Show the demand-to-supply ratio by renewable source |
| 9 | Recommend best renewable credit by price + availability |
| 14 | Best available credit based on price + availability + predicted demand |
| 8 | Should I list Solar or Wind credits this week? |

**Key fields returned:** `source_breakdown` (market_share_pct, total_kwh_available), `location_breakdown`

#### `GET /public/purchases` — answers:
| # | Question |
|---|---------|
| 3 | Compare demand for Solar, Wind, Hydro during selected period |
| 4 | Which source had highest average selling price? |
| 5 | Predict which source will have highest demand next month |
| 6 | Is Noida likely to face Solar-credit shortage next month? |
| 12 | Which source experienced highest price volatility? |
| 13 | Which source is predicted to have highest price next month? |

**Key fields returned:** `demand_by_source` (demand_share_pct, avg_price, price_volatility), `location_demand_breakdown`

### Example AI Agent Flow

```
User: "Is Noida likely to face a Solar-credit shortage next month?"
           │
           ▼
AI Agent calls autonomously:
  GET /public/purchases?location=Noida&energy_source=SOLAR&completed_from=...
  GET /public/listings/active?location=Noida&energy_source=SOLAR
           │
           ▼
Agent receives:
  demand: { Noida → SOLAR → kwh_sold: 500 last 30 days }
  supply: { Noida → SOLAR → total_kwh_available: 80 }
           │
           ▼
Bedrock Claude reasons:
  "Demand (500 kWh) >> Supply (80 kWh available).
   Shortage probability: HIGH. Recommend listing Solar in Noida."
```

### Filter Reference

| Endpoint | Key Filters |
|----------|------------|
| `GET /public/listings` | `energy_source`, `location`, `status`, `created_from`, `created_to` |
| `GET /public/listings/active` | `energy_source`, `location`, `min/max_price_per_kwh`, `min_energy_kwh`, `sort_by`, `sort_order` |
| `GET /public/purchases` | `energy_source`, `location`, `status`, `completed_from`, `completed_to` |

---

## SLIDE 13 — INFRASTRUCTURE & DEPLOYMENT

```
┌─────────────────────────────────────────────────┐
│                  CLOUD LAYER                     │
│                                                  │
│  ┌─────────────┐    ┌──────────────────────┐    │
│  │ Render.com  │    │   Neon PostgreSQL     │    │
│  │             │    │   (Serverless)        │    │
│  │ FastAPI App │    │   Auto-scales         │    │
│  │ Free Tier   │    │   Free Tier           │    │
│  └──────┬──────┘    └──────────────────────┘    │
│         │                                        │
│  ┌──────▼──────────────────────────────────┐    │
│  │        Ethereum Sepolia Testnet          │    │
│  │   EnergyToken Contract: 0xd8dB33...     │    │
│  │   Platform Wallet: 0x1F4ab8...          │    │
│  │   Explorer: sepolia.etherscan.io        │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │           AWS AI Services                │   │
│  │  Bedrock (Claude + Titan Embeddings)     │   │
│  │  OpenSearch (VectorDB)                   │   │
│  │  S3 (Knowledge Base Documents)          │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## SLIDE 14 — FUTURE ENHANCEMENTS

### Phase 1 — Complete Current Features (Immediate)

| Priority | Feature | Business Value |
|----------|---------|---------------|
| 🔴 High | **AI Agent Live** | Bedrock RAG + Prediction Engine — sellers earn 20–30% more by listing at optimal price |
| 🔴 High | **Mainnet Deployment** | EnergyToken.sol on Ethereum Mainnet — real ETH transactions, real trust |
| 🔴 High | **Frontend (React on Vercel)** | UI for buyers/sellers with VERIFIED badges, Etherscan links, forecast charts |
| 🔴 High | **Carbon Credit Tracking** | Track CO₂ saved per kWh sold — sell carbon offset certificates as NFTs |

---

### Phase 2 — Business Growth (3–6 Months)

| Feature | Business Value |
|---------|---------------|
| **IoT Smart Meter Integration** | Real-time energy production data → auto-create listings when surplus detected |
| **Dynamic Pricing Engine** | AI adjusts listing price in real-time based on grid demand and time-of-day |
| **Energy Futures / Bidding** | Buyers pre-book energy at fixed price — like commodity futures trading |
| **Subscription Plans** | Premium sellers get AI forecasts + priority listing — recurring revenue model |
| **Carbon NFTs** | Each trade mints a verifiable carbon credit NFT — tradeable on OpenSea |
| **Multi-Currency Support** | Accept USDC / stablecoin payments — remove ETH price volatility for buyers |

---

### Phase 3 — Production AWS Stack (Replace Free Tools)

> Current free tools are great for hackathon. Production requires enterprise-grade AWS services.

| Current (Free/Testnet) | Production (AWS) | Why Upgrade |
|------------------------|-----------------|-------------|
| **Render.com** | **AWS ECS Fargate** | Auto-scaling containers, zero downtime deploys |
| **Neon PostgreSQL** | **AWS Aurora PostgreSQL** | Multi-AZ, read replicas, 99.99% SLA |
| **Ethereum Sepolia** | **Ethereum Mainnet** | Real value transactions |
| **Vercel (UI)** | **AWS CloudFront + S3** | Global CDN, sub-50ms latency worldwide |
| **Manual `.env` secrets** | **AWS Secrets Manager + KMS** | Encrypted key rotation, audit trail |
| **Single region** | **AWS Multi-Region (Route 53)** | Geo-routing, disaster recovery |
| **Alchemy RPC** | **AWS Managed Blockchain** | Private Ethereum node, no rate limits |
| **Basic logging** | **AWS CloudWatch + X-Ray** | Distributed tracing, real-time alerts |

```
PRODUCTION AWS ARCHITECTURE

   Users (Global)
        │
   ┌────▼────────────────────────────────────────┐
   │  CloudFront CDN  ←  S3 (React Frontend)     │
   └────────────────────┬────────────────────────┘
                        │
   ┌────────────────────▼────────────────────────┐
   │  AWS ALB (Application Load Balancer)         │
   └──────────┬─────────────────┬────────────────┘
              │                 │
   ┌──────────▼──┐    ┌─────────▼──────────────┐
   │ ECS Fargate │    │  ECS Fargate            │
   │ FastAPI     │    │  AI Agent Service       │
   │ (Auto-scale)│    │  (Bedrock + RAG)        │
   └──────┬──────┘    └─────────┬──────────────┘
          │                     │
   ┌──────▼─────────────────────▼──────────────┐
   │           AWS Aurora PostgreSQL            │
   │   Primary (Write) + Read Replica           │
   │   Multi-AZ | Automated Backups             │
   └───────────────────────────────────────────┘
          │
   ┌──────▼───────────────────────────────────┐
   │        AWS Managed Blockchain             │
   │   Private Ethereum Node (No rate limits) │
   └──────────────────────────────────────────┘
```

---

### Phase 4 — High Availability & Scaling

| Concern | Solution | Target |
|---------|---------|--------|
| **API Availability** | ECS Fargate multi-AZ + ALB health checks | 99.99% uptime |
| **DB Failover** | Aurora Multi-AZ — auto failover in < 30 sec | RPO < 1 min |
| **Traffic Spikes** | ECS auto-scaling on CPU/request metrics | 0 → 1000 TPS in 2 min |
| **Blockchain Throughput** | Queue-based minting (SQS) — async transactions | No API timeout on mint |
| **Global Latency** | CloudFront 400+ edge locations | < 50ms UI worldwide |
| **Data Backup** | Aurora automated backups + S3 cross-region | 7-year retention |
| **Secret Rotation** | AWS KMS + Secrets Manager auto-rotation | Zero manual key handling |
| **Observability** | CloudWatch dashboards + X-Ray tracing | Full request trace end-to-end |

---

### Phase 5 — Smart Contract — Mainnet Deployment Plan

> Moving from Sepolia Testnet → Ethereum Mainnet is a one-way door. Requires:

```
Step 1 — Security Audit
  → Third-party Solidity audit (CertiK / OpenZeppelin)
  → Fix all HIGH/MEDIUM findings
  → Bug bounty program on Immunefi

Step 2 — Mainnet Deploy
  → Fund deployer wallet with real ETH (~0.1 ETH for gas)
  → Deploy EnergyToken.sol to Ethereum Mainnet
  → Verify contract on Etherscan (public, transparent)
  → Multisig wallet (Gnosis Safe) for contract ownership

Step 3 — Post-Deploy
  → Update FastAPI BLOCKCHAIN_NETWORK=mainnet
  → All new listings → real immutable records on Ethereum
  → Every trade visible at etherscan.io forever
```

| Testnet (Now) | Mainnet (Future) |
|--------------|-----------------|
| Sepolia ETH (free, fake) | Real ETH (gas fees ~$2–5 per tx) |
| Resets periodically | Permanent — forever on chain |
| For development only | Real user trust & legal validity |
| Etherscan Sepolia | Etherscan.io (public, worldwide) |

---

## SLIDE 15 — SUMMARY

### What We Built

| Component | Status |
|-----------|--------|
| FastAPI REST API (Render hosted) | ✅ Done |
| User Registration & Login (JWT) | ✅ Done |
| Multi-source Energy Listings (7 types) | ✅ Done |
| Energy Purchases + Consume | ✅ Done |
| Neon PostgreSQL (cloud DB) | ✅ Done |
| Blockchain Service (Web3.py) | ✅ Done |
| Smart Contract (Solidity + Hardhat) | ✅ Done |
| Tamper Detection + Audit Endpoints | ✅ Done |
| Etherscan Integration | ✅ Done |
| Public AI Knowledge Base Endpoints (3) | ✅ Done |
| AI RAG + Prediction Engine | 🔲 In Progress |
| Frontend | 🔲 Planned |

### Business Impact
- 🌱 **Environmental** — multi-source renewable energy accelerates green adoption
- 💰 **Economic** — sellers earn from wasted energy; buyers save vs utility rates
- 🔗 **Trust** — blockchain eliminates fraud, double counting and price tampering
- 🤖 **Intelligence** — AI agent maximizes profit for both buyers and sellers

---


*Document updated: July 2026 | Project: Green Energy Marketplace*
