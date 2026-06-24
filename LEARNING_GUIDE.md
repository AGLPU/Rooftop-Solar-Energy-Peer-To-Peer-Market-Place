# 📚 FastAPI Learning Guide - What We Built

> **Goal**: Understand the RoofTop Solar Energy Marketplace architecture and how everything connects.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                               │
│              (Browser / Mobile App / Postman)                │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP Requests
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                     FASTAPI APP                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Routers   │→ │  Services  │→ │   Models   │            │
│  │ (Routes)   │  │ (Logic)    │  │ (Database) │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│         ↑               ↑              ↓                     │
│  ┌────────────┐  ┌────────────┐  Database                  │
│  │  Schemas   │  │   Utils    │  Engine                     │
│  │(Validation)│  │(Auth/Hash) │                             │
│  └────────────┘  └────────────┘                             │
└──────────────────────┬──────────────────────────────────────┘
                       │ SQL Queries
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              AWS AURORA POSTGRESQL                           │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Primary    │         │ Read Replica │                 │
│  │   (Write)    │────────→│   (Read)     │                 │
│  └──────────────┘         └──────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure Explained

```
app/
├── main.py              # 🚪 Entry point - Creates FastAPI app
├── config.py            # ⚙️  Settings - Database, JWT, environment vars
├── database.py          # 🗄️  Database connection - SQLAlchemy setup
│
├── models/              # 📊 Database Tables (What data looks like in DB)
│   └── user.py          # User table structure
│
├── schemas/             # ✅ Validation (What data looks like in API)
│   └── user.py          # Request/Response formats
│
├── routers/             # 🛣️  Routes (API endpoints - URLs)
│   └── users.py         # /api/v1/users/* endpoints
│
├── services/            # 🧠 Business Logic (What happens when endpoint is called)
│   └── user_service.py  # User operations (register, login, etc.)
│
└── utils/               # 🔧 Helper Functions (Reusable code)
    ├── auth.py          # JWT token handling
    └── hashing.py       # Password encryption
```

---

## 🔍 Files Explained (Simple!)

### 1️⃣ **`main.py`** - The Starting Point

**What it does**: Creates the FastAPI app and connects everything together.

```python
app = FastAPI(title="Solar Marketplace")  # Create app

# Add CORS (allow frontend to call API)
app.add_middleware(CORSMiddleware)

# Connect routes
app.include_router(users.router, prefix="/api/v1")

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome!"}

# Health check
@app.get("/health")
def health():
    # Test if database is working
```

**Think of it as**: The main door of your house - everything comes through here.

---

### 2️⃣ **`config.py`** - Configuration Settings

**What it does**: Stores all settings (database URL, JWT secret, etc.)

```python
class Settings(BaseSettings):
    # Database
    database_username: str
    database_password: str
    database_host: str
    
    # JWT
    secret_key: str
    
    # Computed properties
    @property
    def db_url(self):
        # Build connection string automatically
```

**Think of it as**: Your app's settings panel - all configurations in one place.

**Why important**: 
- ✅ Reads from `.env` file
- ✅ Keeps secrets safe (not hardcoded)
- ✅ Easy to change settings

---

### 3️⃣ **`database.py`** - Database Connection

**What it does**: Connects to PostgreSQL database.

```python
# Create engine (connection to database)
engine = create_engine(settings.db_url)  # Writer (Primary)
read_engine = create_engine(settings.db_read_url)  # Reader (Replicas)

# Session factory
SessionLocal = sessionmaker(bind=engine)

# Dependency function
def get_db():
    db = SessionLocal()
    try:
        yield db  # Give database session
    finally:
        db.close()  # Always close connection
```

**Think of it as**: A phone line to the database - you use it to talk to the DB.

**Key concepts**:
- **Engine**: The connection itself
- **Session**: One conversation with the database
- **Dependency**: Function that gives you a DB session when needed

---

### 4️⃣ **`models/user.py`** - Database Table

**What it does**: Defines how data is stored in the database.

```python
class User(Base):
    __tablename__ = "users"  # Table name in DB
    
    # Columns
    id = Column(UUID, primary_key=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    full_name = Column(String)
    role = Column(Enum("buyer", "seller", "admin"))
    wallet_address = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
```

**Think of it as**: A blueprint for a database table (like an Excel sheet structure).

**Key concepts**:
- **Column**: Each field in the table
- **Primary Key**: Unique identifier (like ID card number)
- **Unique**: No duplicates allowed (like email)
- **Nullable**: Can be empty or not

---

### 5️⃣ **`schemas/user.py`** - Data Validation

**What it does**: Defines what data the API accepts/returns (validation rules).

```python
# What client sends when registering
class UserRegisterRequest(BaseModel):
    email: EmailStr  # Must be valid email
    password: str = Field(min_length=8)  # At least 8 chars
    full_name: str
    role: Literal["buyer", "seller", "admin"]
    wallet_address: str | None = None

# What API returns
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    # NOTE: Never return password_hash!
```

**Think of it as**: A form with validation rules (like "email must be valid", "password min 8 chars").

**Key concepts**:
- **Request Schema**: What comes IN (from client)
- **Response Schema**: What goes OUT (to client)
- **Validation**: Automatic checking (Pydantic does this!)

---

### 6️⃣ **`routers/users.py`** - API Endpoints (URLs)

**What it does**: Defines all the URLs your API responds to.

```python
router = APIRouter(prefix="/users")

@router.post("/register")  # POST /api/v1/users/register
def register(
    payload: UserRegisterRequest,  # Validate input
    db: Session = Depends(get_db),  # Get database session
    svc: UserService = Depends(get_user_service)  # Get service
):
    return svc.register(db, payload)  # Call business logic

@router.post("/login")  # POST /api/v1/users/login
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    # Business logic...

@router.get("/me")  # GET /api/v1/users/me
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user  # Authenticated user
```

**Think of it as**: A menu in a restaurant - lists what you can order (API endpoints).

**Key concepts**:
- **@router.get/post/patch/delete**: HTTP methods
- **Depends()**: Inject dependencies (DB session, current user, etc.)
- **Path parameters**: `/users/{user_id}` - dynamic values

---

### 7️⃣ **`services/user_service.py`** - Business Logic

**What it does**: Contains the actual logic (what happens when an endpoint is called).

```python
class UserService:
    def register(self, db: Session, payload: UserRegisterRequest):
        # 1. Check if email already exists
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email exists")
        
        # 2. Hash password
        password_hash = hash_password(payload.password)
        
        # 3. Create user
        user = User(
            id=uuid4(),
            email=payload.email,
            password_hash=password_hash,
            full_name=payload.full_name,
            role=payload.role
        )
        
        # 4. Save to database
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
```

**Think of it as**: The kitchen in a restaurant - where the actual work happens.

**Key concepts**:
- **Separation of concerns**: Routes just receive requests, services do the work
- **Database operations**: Query, add, commit
- **Error handling**: Raise exceptions when something goes wrong

---

### 8️⃣ **`utils/hashing.py`** - Password Security

**What it does**: Hashes passwords so they're never stored in plain text.

```python
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
```

**Think of it as**: A one-way lock - you can lock it (hash) but can't unlock it (can only verify).

**Why important**: Even if database is hacked, passwords are safe!

---

### 9️⃣ **`utils/auth.py`** - JWT Authentication

**What it does**: Creates and validates JWT tokens for user authentication.

```python
def create_access_token(data: dict) -> str:
    # Create token that expires in 60 minutes
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode = {"sub": str(data["user_id"]), "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def get_current_user(token: str, db: Session):
    # Decode token
    payload = jwt.decode(token, SECRET_KEY)
    user_id = payload.get("sub")
    
    # Find user in database
    user = db.query(User).filter(User.id == user_id).first()
    return user
```

**Think of it as**: A temporary badge that proves who you are.

**Key concepts**:
- **Access Token**: Short-lived (60 min) - for API calls
- **Refresh Token**: Long-lived (7 days) - to get new access tokens
- **Depends(get_current_user)**: Automatically checks if user is logged in

---

## 🔄 Request Flow (How Everything Works Together)

Let's trace what happens when a user **registers**:

```
1. CLIENT sends POST request
   ↓
   URL: POST /api/v1/users/register
   Body: {"email": "john@example.com", "password": "Pass123!", ...}

2. ROUTER (users.py) receives request
   ↓
   @router.post("/register")
   - Validates input using UserRegisterRequest schema
   - Injects database session (Depends(get_db))
   - Calls service

3. SCHEMA (user.py) validates data
   ↓
   - Checks email format is valid
   - Checks password is at least 8 chars
   - If validation fails → return 422 error
   - If valid → continue

4. SERVICE (user_service.py) processes request
   ↓
   - Checks if email already exists in DB
   - Hashes password (utils/hashing.py)
   - Creates User model instance
   - Saves to database
   - Returns user object

5. MODEL (user.py) represents database row
   ↓
   User(id=..., email=..., password_hash=..., ...)

6. DATABASE (database.py) saves to PostgreSQL
   ↓
   INSERT INTO users (id, email, password_hash, ...) VALUES (...)

7. RESPONSE goes back to client
   ↓
   - Converts User model to UserResponse schema
   - Removes sensitive fields (password_hash)
   - Returns JSON: {"id": "...", "email": "...", ...}
```

---

## 🔐 Authentication Flow

**Login Process**:
```
1. User sends email + password
2. Service finds user by email
3. Verify password (compare hash)
4. Create JWT tokens (access + refresh)
5. Return tokens to client
6. Client stores tokens
```

**Accessing Protected Endpoints**:
```
1. Client sends request with token in header:
   Authorization: Bearer <access_token>

2. Depends(get_current_user) runs automatically:
   - Extracts token from header
   - Decodes JWT
   - Finds user in database
   - Returns user object

3. If token invalid/expired → 401 Unauthorized
4. If valid → endpoint function runs with current_user
```

---

## 🗄️ Database: Read/Write Split

**Why we have 2 database connections**:

```python
engine = create_engine(db_url)        # Primary (Writer)
read_engine = create_engine(db_read_url)  # Replicas (Readers)
```

**Usage**:
- **Writes** (INSERT, UPDATE, DELETE) → Primary
  ```python
  db: Session = Depends(get_db)  # Uses primary
  ```

- **Reads** (SELECT) → Replicas
  ```python
  db: Session = Depends(get_read_db)  # Uses replicas
  ```

**Benefits**:
- ✅ Better performance (distribute load)
- ✅ Primary handles heavy writes
- ✅ Replicas handle many reads

---

## 🎯 Key FastAPI Concepts

### **Dependency Injection**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    # FastAPI automatically calls get_db() and passes result
```

**What it does**: Automatically provides things you need (database, current user, etc.)

---

### **Pydantic Validation**
```python
class UserRegisterRequest(BaseModel):
    email: EmailStr  # Auto-validates email format
    password: str = Field(min_length=8)  # Min 8 chars
```

**What it does**: Automatically validates incoming data. If invalid → returns 422 error with details.

---

### **Path Operations (Decorators)**
```python
@app.get("/")      # Handle GET requests
@app.post("/")     # Handle POST requests
@app.patch("/{id}") # Handle PATCH requests with path parameter
@app.delete("/{id}")# Handle DELETE requests
```

**What it does**: Maps URLs to Python functions.

---

### **Response Models**
```python
@router.get("/users", response_model=list[UserResponse])
def list_users():
    # Return list of User objects
    # FastAPI automatically converts to UserResponse
```

**What it does**: Ensures responses match the schema (removes extra fields, formats data).

---

## 📊 Data Models vs Schemas (Confused? Read This!)

| Aspect | **Model** (models/user.py) | **Schema** (schemas/user.py) |
|--------|---------------------------|------------------------------|
| **Purpose** | Database table structure | API request/response format |
| **Used in** | Database operations | API input/output |
| **Library** | SQLAlchemy | Pydantic |
| **Contains** | All DB columns (including password_hash) | Only safe fields for API |
| **Example** | `class User(Base)` | `class UserResponse(BaseModel)` |

**Simple rule**:
- **Model** = What's in the database
- **Schema** = What goes over the API

---

## 🔑 Important Patterns Used

### 1. **Repository Pattern** (Service Layer)
- Routes don't talk directly to database
- Services handle all business logic
- Easy to test and maintain

### 2. **DTO Pattern** (Schemas)
- Data Transfer Objects
- Validate and shape data going in/out

### 3. **Dependency Injection**
- Functions automatically get what they need
- Clean, testable code

### 4. **Environment-based Config**
- Settings from `.env` file
- No hardcoded secrets

---

## 🧪 How to Test Everything

### **Test Registration**:
```bash
POST http://127.0.0.1:8000/api/v1/users/register
{
  "email": "test@example.com",
  "password": "Password123!",
  "full_name": "Test User",
  "role": "buyer"
}
```

### **Test Login**:
```bash
POST http://127.0.0.1:8000/api/v1/users/login
{
  "email": "test@example.com",
  "password": "Password123!"
}
# Returns: {"access_token": "...", "refresh_token": "..."}
```

### **Test Protected Endpoint**:
```bash
GET http://127.0.0.1:8000/api/v1/users/me
Headers: Authorization: Bearer <access_token>
# Returns: Your user info
```

---

## 💡 What You've Learned

✅ **FastAPI basics** - Routes, dependencies, validation  
✅ **SQLAlchemy** - Database models and sessions  
✅ **Pydantic** - Data validation and serialization  
✅ **JWT Authentication** - Secure token-based auth  
✅ **Password Security** - Hashing with bcrypt  
✅ **Clean Architecture** - Separation of concerns  
✅ **Database Optimization** - Read/write split  
✅ **Environment Config** - Using .env files  

---

## 🚀 Next Steps to Learn More

1. **Add more models** - Create `SolarListing`, `Transaction`, etc.
2. **Add relationships** - User has many listings
3. **Add pagination** - Limit/offset for large datasets
4. **Add filtering** - Search and filter listings
5. **Add file upload** - Upload solar panel images
6. **Add background tasks** - Send emails, process payments
7. **Add WebSockets** - Real-time notifications
8. **Add caching** - Redis for better performance

---

## 📖 Recommended Reading Order

1. ✅ **This guide** - Understand what we built
2. 📄 **QUICKSTART.md** - Learn how to use the API
3. 🌐 **FastAPI Docs** - https://fastapi.tiangolo.com (Official tutorial)
4. 📚 **SQLAlchemy Docs** - https://docs.sqlalchemy.org
5. ✅ **Pydantic Docs** - https://docs.pydantic.dev

---

## 🎓 Quick Reference Card

```python
# Create endpoint
@router.get("/path")
def function_name():
    return {"data": "value"}

# Get database session
db: Session = Depends(get_db)

# Get current user
user: User = Depends(get_current_user)

# Validate input
payload: SchemaName

# Query database
user = db.query(User).filter(User.email == email).first()

# Add to database
db.add(object)
db.commit()
db.refresh(object)

# Raise error
raise HTTPException(status_code=400, detail="Error message")
```

---

**You now understand the complete architecture! 🎉**

Start with small changes, test them, and gradually build more features. You've got a solid foundation!

