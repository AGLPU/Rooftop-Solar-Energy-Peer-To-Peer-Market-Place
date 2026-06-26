# 🌞 RoofTop Solar Energy — Peer-to-Peer Marketplace

A **FastAPI** backend for a decentralised solar energy trading platform where **sellers** list rooftop solar energy and **buyers** purchase energy credits settled via **Ethereum smart contracts**.

**Database**: AWS RDS Aurora PostgreSQL

---

## ✨ Features

### **Built & Working** ✅
- 🔐 **User Authentication** — JWT-based access & refresh tokens
- 👥 **User Management** — Registration, login, profile updates
- 🛡️ **Role-based Access Control** — Buyer, Seller, Admin roles
- 🔒 **Password Security** — Bcrypt hashing (never store plain passwords)
- 📧 **Email Validation** — Automatic with Pydantic
- 🏷️ **Ethereum Wallet** — Optional wallet address for users
- 🗄️ **Database Optimization** — Read/write split for Aurora PostgreSQL
- 📝 **API Documentation** — Auto-generated Swagger UI & ReDoc
- 🧪 **Testing** — Full test suite with in-memory SQLite
- 🔄 **Auto-reload** — Development server with hot reload

### **Coming Soon** 🚧
- ⚡ **Solar Listings** — Sellers list available energy
- 💰 **Energy Purchases** — Buyers purchase energy credits
- 📜 **Smart Contracts** — Ethereum ERC-20 token settlement
- 🔗 **Blockchain Integration** — Web3.py for transaction verification

---

## 🛠️ Technology Stack

### **Backend**
- **FastAPI** — Modern, fast Python web framework
- **Uvicorn** — ASGI server for async Python
- **SQLAlchemy** — ORM for database operations
- **Alembic** — Database migration tool
- **Pydantic** — Data validation and settings management

### **Security**
- **Python-JOSE** — JWT token generation and validation
- **Passlib** — Password hashing with bcrypt
- **Cryptography** — Additional crypto utilities

### **Database**
- **AWS RDS Aurora PostgreSQL** — Managed relational database
- **Psycopg2** — PostgreSQL adapter for Python
- **Read Replica Support** — Optimized query performance

### **Testing**
- **Pytest** — Testing framework
- **HTTPX** — Async HTTP client for testing

### **Development**
- **Python-dotenv** — Environment variable management
- **Python-multipart** — File upload support

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

### 🔄 **For Cloned Repository (Windows Environment)**

If you've **cloned** this repository from GitHub and want to run it on Windows:

#### 1️⃣ Navigate to project directory
```powershell
cd C:\CATS\hackathon\rooftop-solar-marketplace
```

#### 2️⃣ Create Python virtual environment
```powershell
python -m venv venv
```

#### 3️⃣ Activate virtual environment
```powershell
# Windows PowerShell
venv\Scripts\activate

# Windows Command Prompt
venv\Scripts\activate.bat
```
✅ You should see `(venv)` prefix in your terminal

#### 4️⃣ Install all dependencies
```powershell
pip install -r requirements.txt
```

#### 5️⃣ Set up environment variables
```powershell
# Copy template to create .env file
copy .env.example .env
```

**Edit `.env` file** and configure:
- `DATABASE_USERNAME` — Your Aurora PostgreSQL username
- `DATABASE_PASSWORD` — Your Aurora PostgreSQL password
- `DATABASE_HOST` — Aurora cluster endpoint
- `DATABASE_READ_HOST` — Aurora read replica endpoint
- `DATABASE_NAME` — Database name (e.g., `ecccqadbcapt`)
- `DATABASE_SCHEMA` — Schema name (e.g., `Dummy`)
- `SECRET_KEY` — JWT secret key (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

#### 6️⃣ Run database migrations
```powershell
alembic upgrade head
```
This creates the `users` table in your database.

#### 7️⃣ Start the development server
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
✅ Server running! You'll see: `Uvicorn running on http://127.0.0.1:8000`

#### 8️⃣ Access the application
- **API Documentation (Swagger)**: http://127.0.0.1:8000/docs
- **Alternative Docs (ReDoc)**: http://127.0.0.1:8000/redoc
- **Health Check**: http://127.0.0.1:8000/health
- **Welcome Page**: http://127.0.0.1:8000/

#### 9️⃣ Stop the server
Press `Ctrl + C` in the terminal where the server is running.

---

### 📚 **Learning Resources**

If you're new to FastAPI or Python:
- **SUMMARY.md** — Quick overview of the architecture (5 min read)
- **ARCHITECTURE_VISUAL.md** — Visual diagrams and data flows
- **LEARNING_GUIDE.md** — Complete detailed explanation of every file
- **QUICKSTART.md** — How to use the API endpoints

---

### 🔧 **Troubleshooting**

**Port already in use?**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

**Database connection issues?**
- Verify `.env` credentials are correct
- Check VPN/network access to AWS Aurora
- Test connection: http://127.0.0.1:8000/health

**Module not found errors?**
```powershell
# Make sure venv is activated (you should see (venv) in prompt)
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 🗄️ Database Configuration

### **AWS Aurora PostgreSQL with Read/Write Split**

This application uses **AWS RDS Aurora PostgreSQL** with optimized read replica support:

**Connection Details** (configured in `.env`):
- **Primary (Writer)**: Handles INSERT, UPDATE, DELETE operations
- **Read Replica**: Handles SELECT queries (load balanced)
- **Schema**: `Dummy` (or your custom schema)
- **SSL**: Enabled for secure connections

**Environment Variables**:
```env
DATABASE_USERNAME=your_username
DATABASE_PASSWORD=your_password
DATABASE_HOST=eccc-dev-qa-db-cluster.cluster-xxxxx.ca-central-1.rds.amazonaws.com
DATABASE_READ_HOST=eccc-dev-qa-db-cluster.cluster-ro-xxxxx.ca-central-1.rds.amazonaws.com
DATABASE_PORT=5432
DATABASE_NAME=ecccqadbcapt
DATABASE_SCHEMA=Dummy
```

**Benefits**:
- ✅ Better performance (reads don't block writes)
- ✅ Automatic failover (Aurora managed)
- ✅ Scalability (add more read replicas as needed)

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

