from app.database import engine
from app.models.user import User

# Create only users table
User.metadata.create_all(bind=engine)
print("✅ Users table created!")