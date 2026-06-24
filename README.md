# 🌞 RoofTop Solar Energy — Peer-to-Peer Marketplace

A **FastAPI** backend for a decentralised solar energy trading platform where **sellers** list rooftop solar energy and **buyers** purchase energy credits settled via **Ethereum smart contracts**.

**Database**: AWS RDS Aurora PostgreSQL

---

## 🏗️ Architecture

```
rooftop-solar-marketplace/
├── app/
│   ├── main.py               # FastAPI app, CORS, routers
│   ├── config.py             # Pydantic settings (reads .env)
│   ├── database.py           # SQLAlchemy engine + get_db dependency
│   ├── models/
│   │   └── user.py           # User ORM model (UUID PK, roles, wallet)
│   ├── schemas/
│   │   └── user.py           # Pydantic request / response schemas
│   ├── routers/
│   │   └── users.py          # All /api/v1/users/* endpoints
│   ├── services/
│   │   └── user_service.py   # Business logic (no HTTP concerns)
│   └── utils/
│       ├── auth.py           # JWT create / verify + FastAPI dependencies
│       └── hashing.py        # bcrypt password hashing
├── alembic/                  # DB migrations
│   ├── env.py
│   └── versions/
│       └── 0001_create_users_table.py
├── tests/
│   ├── conftest.py           # In-memory SQLite fixtures
│   └── test_users.py         # Full endpoint test suite
├── .env.example
├── alembic.ini
└── requirements.txt
```

---

## 🚀 Quick Start

### 1 — Clone & create virtual environment
```bash
cd C:\CATS\hackathon\rooftop-solar-marketplace
python -m venv venv
venv\Scripts\activate          # Windows
```

### 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### 3 — Configure environment
```bash
copy .env.example .env
# Edit .env — set your Aurora DATABASE_URL and SECRET_KEY
```

### 4 — Run DB migrations
```bash
alembic upgrade head
```

### 5 — Start the server
```bash
uvicorn app.main:app --reload
```

API docs → http://localhost:8000/docs

---

## 📡 User API Endpoints

| Method   | Path                                  | Auth     | Description              |
|----------|---------------------------------------|----------|--------------------------|
| `POST`   | `/api/v1/users/register`              | Public   | Register a new user      |
| `POST`   | `/api/v1/users/login`                 | Public   | Login → JWT tokens       |
| `GET`    | `/api/v1/users/me`                    | Bearer   | Current user profile     |
| `GET`    | `/api/v1/users/`                      | Admin    | List all users           |
| `GET`    | `/api/v1/users/{id}`                  | Bearer   | Get user by ID           |
| `PATCH`  | `/api/v1/users/{id}`                  | Bearer   | Update profile           |
| `POST`   | `/api/v1/users/{id}/change-password`  | Bearer   | Change password          |
| `POST`   | `/api/v1/users/{id}/deactivate`       | Bearer   | Soft-deactivate account  |
| `DELETE` | `/api/v1/users/{id}`                  | Admin    | Hard delete              |
| `GET`    | `/health`                             | Public   | Health check             |

---

## 🧪 Run Tests
```bash
pytest tests/ -v
```

---

## 🔮 Coming Next
- `listings/` — Seller posts solar energy listings
- `purchases/` — Buyer purchases energy credits
- `contracts/` — Solidity smart contract (EnergyToken ERC-20)
- Ethereum wallet signature verification on register

