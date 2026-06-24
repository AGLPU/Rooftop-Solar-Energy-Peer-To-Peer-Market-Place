# 🚀 Quick Start Guide - RoofTop Solar Energy Marketplace

Your FastAPI application is **up and running**!

---

## ✅ Your Setup

### **Database Configuration**
- **Primary (Writer)**: `eccc-dev-qa-db-cluster.cluster-cmlzbcc6shng.ca-central-1.rds.amazonaws.com`
- **Replica (Reader)**: `eccc-dev-qa-db-cluster.cluster-ro-cmlzbcc6shng.ca-central-1.rds.amazonaws.com`
- **Database**: `ecccqadbcapt`
- **Schema**: `Dummy`
- **SSL**: Enabled

### **Server**
- **URL**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs (Swagger UI)
- **ReDoc**: http://127.0.0.1:8000/redoc (Alternative docs)

---

## 🎯 Available Endpoints

### **Root / Welcome**
```bash
GET http://127.0.0.1:8000/
```
Returns API welcome message and available endpoints.

### **Health Check**
```bash
GET http://127.0.0.1:8000/health
```
Returns API status and database connectivity.

### **User Management** (All under `/api/v1/users`)

#### 1️⃣ **Register a new user**
```bash
POST /api/v1/users/register
```
Body:
```json
{
  "email": "seller@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "role": "seller",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
}
```

#### 2️⃣ **Login**
```bash
POST /api/v1/users/login
```
Body:
```json
{
  "email": "seller@example.com",
  "password": "SecurePass123!"
}
```
Returns JWT tokens (access + refresh).

#### 3️⃣ **Get current user** (requires authentication)
```bash
GET /api/v1/users/me
Headers: Authorization: Bearer {access_token}
```

#### 4️⃣ **List all users** (admin only)
```bash
GET /api/v1/users?skip=0&limit=20
Headers: Authorization: Bearer {access_token}
```

#### 5️⃣ **Get user by ID**
```bash
GET /api/v1/users/{user_id}
Headers: Authorization: Bearer {access_token}
```

#### 6️⃣ **Update user**
```bash
PATCH /api/v1/users/{user_id}
Headers: Authorization: Bearer {access_token}
Body:
{
  "full_name": "Updated Name",
  "wallet_address": "0x..."
}
```

#### 7️⃣ **Delete user** (admin only)
```bash
DELETE /api/v1/users/{user_id}
Headers: Authorization: Bearer {access_token}
```

#### 8️⃣ **Change password**
```bash
POST /api/v1/users/change-password
Headers: Authorization: Bearer {access_token}
Body:
{
  "old_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

---

## 🧪 Testing with Swagger UI

1. **Open**: http://127.0.0.1:8000/docs
2. **Register a user** using `/api/v1/users/register`
3. **Login** using `/api/v1/users/login` → Copy the `access_token`
4. **Click "Authorize" button** (top right) → Paste token: `Bearer {access_token}`
5. **Try other endpoints** - you're now authenticated!

---

## 🔧 How to Run

### **Start the server**
```powershell
cd C:\CATS\hackathon\rooftop-solar-marketplace
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### **Run tests**
```powershell
pytest tests/ -v
```

### **Run database migrations**
```powershell
alembic upgrade head
```

---

## 📊 Read/Write Split (Aurora Optimization)

Your app uses **read replicas** for better performance:

- **Write operations** (CREATE, UPDATE, DELETE) → Primary instance
- **Read operations** (GET, LIST) → Read replicas (load balanced)

This happens automatically in your routes:
- `Depends(get_db)` → Primary (writes)
- `Depends(get_read_db)` → Replicas (reads)

---

## 🔐 Security Features

✅ Password hashing with bcrypt  
✅ JWT authentication (access + refresh tokens)  
✅ Role-based access (buyer, seller, admin)  
✅ SSL/TLS database connections  
✅ CORS middleware configured  

---

## 📝 User Roles

| Role | Can Do |
|------|--------|
| **buyer** | Purchase solar energy credits |
| **seller** | List rooftop solar energy for sale |
| **admin** | Manage users, view all data |

---

## 🛠️ Project Structure

```
app/
├── main.py              # FastAPI app & routes registration
├── config.py            # Settings (DB, JWT, etc.)
├── database.py          # SQLAlchemy setup (read/write split)
├── models/
│   └── user.py          # User database model
├── schemas/
│   └── user.py          # Pydantic schemas (validation)
├── routers/
│   └── users.py         # User API endpoints
├── services/
│   └── user_service.py  # Business logic
└── utils/
    ├── auth.py          # JWT handling
    └── hashing.py       # Password hashing
```

---

## 🎓 Learning Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **Pydantic**: https://docs.pydantic.dev
- **JWT**: https://jwt.io

---

## 🚨 Common Issues

### Server not starting?
```powershell
# Check if port is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID {process_id} /F
```

### Database connection issues?
- Verify `.env` credentials are correct
- Check VPN/network access to Aurora
- Verify schema "Dummy" exists in your database

### Import errors?
```powershell
pip install -r requirements.txt
```

---

## 📧 Next Steps

1. ✅ **Server is running** - Test endpoints via Swagger UI
2. 🗄️ **Run migrations** - Create database tables: `alembic upgrade head`
3. 👤 **Register users** - Create buyer/seller/admin accounts
4. 🧪 **Run tests** - `pytest tests/ -v`
5. 🎨 **Add features** - Implement solar energy listings, transactions, etc.

---

**Happy Coding! 🌞⚡**

