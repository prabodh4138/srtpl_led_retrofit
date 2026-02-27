import re
import bcrypt
from sqlalchemy.orm import Session
from models import User

# ---------------------------
# Password Validation
# ---------------------------

def validate_password_strength(password: str) -> bool:
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
    return re.match(pattern, password) is not None


# ---------------------------
# Hash Password
# ---------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ---------------------------
# Get User by Employee ID
# ---------------------------

def get_user_by_employee_id(db: Session, employee_id: str):
    return db.query(User).filter(
        User.employee_id == employee_id.upper(),
        User.is_active == 1
    ).first()


# ---------------------------
# Set Password (First Time)
# ---------------------------

def set_user_password(db: Session, user: User, password: str):
    user.password_hash = hash_password(password)
    db.commit()