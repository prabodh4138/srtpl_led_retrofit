from sqlalchemy.orm import Session
from models import User
import bcrypt
import re


# =====================================================
# Hash Password
# =====================================================

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )
    return hashed.decode("utf-8")


# =====================================================
# Verify Password
# =====================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False

    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# =====================================================
# Password Strength Validation
# =====================================================

def validate_password_strength(password: str) -> bool:

    if len(password) < 8:
        return False

    if not re.search(r"[A-Z]", password):
        return False

    if not re.search(r"[0-9]", password):
        return False

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False

    return True


# =====================================================
# Get User by Employee ID
# =====================================================

def get_user_by_employee_id(db: Session, employee_id: str):
    return db.query(User).filter(
        User.employee_id == employee_id
    ).first()


# =====================================================
# Set User Password
# =====================================================

def set_user_password(db: Session, user: User, new_password: str):

    hashed = hash_password(new_password)

    user.password_hash = hashed
    db.commit()
    db.refresh(user)

    return True
