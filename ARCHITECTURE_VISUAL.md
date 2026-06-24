# 🗺️ Quick Visual Reference - Files & Their Roles

## 📂 File Responsibility Map

```
┌─────────────────────────────────────────────────────────────┐
│                      INCOMING REQUEST                        │
│           POST /api/v1/users/register + JSON Body            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  📄 main.py - Entry Point                                    │
│  • Creates FastAPI app                                       │
│  • Adds middleware (CORS)                                    │
│  • Includes routers                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  📄 routers/users.py - URL Handler                           │
│  • Receives request at /users/register                       │
│  • Injects dependencies (db session, services)               │
│  • Calls: svc.register(db, payload)                          │
└───────────┬────────────────────────────┬────────────────────┘
            │                            │
            ↓                            ↓
┌──────────────────────┐     ┌──────────────────────┐
│ 📄 schemas/user.py   │     │ 📄 database.py       │
│ • Validates JSON     │     │ • Provides DB        │
│ • Checks email valid │     │   connection         │
│ • Min 8 char pass    │     │ • Session factory    │
└──────────────────────┘     └──────────────────────┘
            │
            ↓
┌─────────────────────────────────────────────────────────────┐
│  📄 services/user_service.py - Business Logic                │
│  • Check if email exists                                     │
│  • Hash password (calls utils/hashing.py)                    │
│  • Create User object                                        │
│  • Save to database                                          │
└─────────────┬────────────────────────┬──────────────────────┘
              │                        │
              ↓                        ↓
┌──────────────────────┐   ┌──────────────────────┐
│ 📄 utils/hashing.py  │   │ 📄 models/user.py    │
│ • hash_password()    │   │ • User table         │
│ • Uses bcrypt        │   │   structure          │
└──────────────────────┘   │ • Columns: id,       │
                           │   email, etc.        │
                           └──────────┬───────────┘
                                      │
                                      ↓
                           ┌──────────────────────┐
                           │  🗄️ PostgreSQL DB   │
                           │  (Aurora)            │
                           │  • Table: users      │
                           │  • Schema: Dummy     │
                           └──────────────────────┘
```

---

## 🎯 Each File's Job (One-Liner)

| File | Job | When Used |
|------|-----|-----------|
| **main.py** | "I'm the boss - I start everything" | App startup |
| **config.py** | "I hold all secrets & settings" | App startup, reading .env |
| **database.py** | "I connect to the database" | Every DB operation |
| **models/user.py** | "I define the users table structure" | Creating/querying users |
| **schemas/user.py** | "I validate API inputs/outputs" | Every API request/response |
| **routers/users.py** | "I handle /users/* URLs" | When /api/v1/users/* is called |
| **services/user_service.py** | "I contain the business logic" | Register, login, update, etc. |
| **utils/hashing.py** | "I encrypt passwords" | Registration, login |
| **utils/auth.py** | "I create & verify JWT tokens" | Login, protected endpoints |

---

## 🔄 Data Flow Diagram

### Registration Flow:
```
1. Client                    2. Router               3. Schema
   ┌────────┐                  ┌────────┐              ┌────────┐
   │ POST   │─────JSON────────→│ Receive│──validate──→│ Check  │
   │/register│                  │ request│              │ format │
   └────────┘                  └────────┘              └────────┘
                                    │                       │
                                    ↓                       ↓
4. Service                   5. Hashing              6. Model
   ┌────────┐                  ┌────────┐              ┌────────┐
   │Business│──hash_pass──────→│ Bcrypt │              │ Create │
   │ Logic  │                  │        │              │  User  │
   └────────┘                  └────────┘              └────────┘
       │                                                    │
       └──────────────────save─────────────────────────────┘
                                  │
                                  ↓
7. Database                  8. Response
   ┌────────┐                  ┌────────┐
   │ INSERT │                  │ Return │
   │  user  │──success────────→│  JSON  │────→ Client
   └────────┘                  └────────┘
```

### Login Flow:
```
1. Client sends email + password
         ↓
2. Router receives (/login)
         ↓
3. Schema validates format
         ↓
4. Service finds user by email
         ↓
5. Hashing.verify_password() checks password
         ↓
6. Auth.create_access_token() generates JWT
         ↓
7. Return tokens to client
```

### Authenticated Request Flow:
```
1. Client sends: Authorization: Bearer <token>
         ↓
2. Router receives request
         ↓
3. Depends(get_current_user) extracts token
         ↓
4. Auth.decode_token() validates JWT
         ↓
5. Database query: Find user by ID from token
         ↓
6. Endpoint function runs with current_user
         ↓
7. Return response
```

---

## 🧩 How Files Work Together

### Example: User Registration

```python
# 1. main.py includes router
app.include_router(users.router, prefix="/api/v1")

# 2. routers/users.py defines endpoint
@router.post("/register", response_model=UserResponse)
def register(
    payload: UserRegisterRequest,    # 3. schemas/user.py validates
    db: Session = Depends(get_db),   # 4. database.py provides session
    svc: UserService = Depends()     # 5. services/user_service.py
):
    return svc.register(db, payload)

# 6. services/user_service.py does the work
def register(self, db, payload):
    # 7. utils/hashing.py encrypts password
    hashed = hash_password(payload.password)
    
    # 8. models/user.py structure
    user = User(
        id=uuid4(),
        email=payload.email,
        password_hash=hashed,
        ...
    )
    
    # 9. database.py connection saves
    db.add(user)
    db.commit()
    
    return user  # 10. Auto-converted to UserResponse schema
```

---

## 📚 Cheat Sheet: Common Operations

### Add New Endpoint
```python
# In routers/users.py
@router.get("/new-endpoint")
def my_function(db: Session = Depends(get_db)):
    # Your code here
    return {"message": "success"}
```

### Query Database
```python
# Find one
user = db.query(User).filter(User.email == email).first()

# Find all
users = db.query(User).all()

# With limit/offset
users = db.query(User).offset(skip).limit(limit).all()

# Count
count = db.query(User).count()
```

### Create Database Record
```python
user = User(id=uuid4(), email="test@example.com", ...)
db.add(user)
db.commit()
db.refresh(user)  # Get updated data from DB
```

### Update Database Record
```python
user = db.query(User).filter(User.id == user_id).first()
user.full_name = "New Name"
db.commit()
db.refresh(user)
```

### Delete Database Record
```python
user = db.query(User).filter(User.id == user_id).first()
db.delete(user)
db.commit()
```

### Raise API Error
```python
raise HTTPException(
    status_code=400,
    detail="Email already exists"
)
```

### Create Schema
```python
class MyRequest(BaseModel):
    field1: str
    field2: int = Field(ge=0)  # Greater or equal to 0
    field3: EmailStr
    field4: str | None = None  # Optional
```

---

## 🎨 Design Patterns Used

### 1. Layered Architecture
```
Presentation Layer  → routers/     (Handle HTTP)
Business Layer      → services/    (Business logic)
Data Layer          → models/      (Database)
```

### 2. Dependency Injection
```python
def get_db():
    # Provide database session
    yield db

@router.get("/")
def endpoint(db: Session = Depends(get_db)):
    # db is automatically injected
```

### 3. Repository Pattern
```python
# Service acts as repository
class UserService:
    def get_by_email(self, db, email):
        return db.query(User).filter(User.email == email).first()
```

### 4. DTO (Data Transfer Object)
```python
# Schemas are DTOs
class UserResponse(BaseModel):
    # Only safe fields for API
```

---

## 💡 Pro Tips

### 1. Always Use Schemas for API
```python
# ✅ Good
@router.post("/users", response_model=UserResponse)
def create_user(payload: UserRequest):
    pass

# ❌ Bad
@router.post("/users")
def create_user(email: str, password: str):
    pass
```

### 2. Never Return Password Hashes
```python
# ✅ UserResponse excludes password_hash
class UserResponse(BaseModel):
    id: UUID
    email: str
    # NO password_hash field!
```

### 3. Use Depends for Common Logic
```python
# ✅ Reusable
def get_current_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403)
    return user

@router.delete("/users/{id}")
def delete_user(admin: User = Depends(get_current_admin)):
    # Automatically checks if admin
```

### 4. Use Read Replicas for GET
```python
# ✅ Better performance
@router.get("/users")
def list_users(db: Session = Depends(get_read_db)):
    # Uses replica

# ✅ For writes, use primary
@router.post("/users")
def create_user(db: Session = Depends(get_db)):
    # Uses primary
```

---

## 🎯 What Each Layer Knows About

| Layer | Knows About | Doesn't Know About |
|-------|-------------|-------------------|
| **Routers** | HTTP, URLs, Schemas | Database, Business logic |
| **Services** | Business logic, Database | HTTP, Request/Response |
| **Models** | Database structure | API, Business logic |
| **Schemas** | Validation rules | Database, Business logic |
| **Utils** | Helper functions | Specific business logic |

---

**This is your quick reference! Keep it handy while coding.** 🚀

