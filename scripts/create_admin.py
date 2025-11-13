"""Script to create admin user."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def create_admin_user():
    """Create admin user."""
    # Check if SessionLocal is initialized
    if not SessionLocal:
        raise ValueError(
            "DATABASE_URL is required. Please set it in .env file.\n"
            "Format: postgresql://username:password@host:port/database_name\n"
            "Example: postgresql://postgres:your_password@localhost:5433/chatbot_db"
        )
    
    db: Session = SessionLocal()
    try:
        # Check if admin user already exists
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("=" * 60)
            print("Admin user already exists!")
            print("=" * 60)
            print(f"Username: {admin.username}")
            print(f"Role: {admin.role}")
            print(f"Email: {admin.email}")
            print("=" * 60)
            return
        
        # Create admin user
        admin_user = User(
            username="admin",
            password_hash=get_password_hash("admin"),
            role=UserRole.ADMIN,
            full_name="Administrator",
            email="admin@company.com",
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("=" * 60)
        print("Admin user created successfully!")
        print("=" * 60)
        print(f"Username: admin")
        print(f"Password: admin")
        print("Please change the password after first login!")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
        print("\nTroubleshooting:")
        print("1. Check DATABASE_URL in .env file")
        print("2. Check database connection")
        print("3. Check if migrations have been run: alembic upgrade head")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()
