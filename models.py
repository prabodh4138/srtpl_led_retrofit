from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


# =====================================================
# USER TABLE
# =====================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="staff")  # admin / vendor / staff
    vendor_team = Column(String, nullable=True)

    password_hash = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================
# FIXTURE MASTER TABLE
# =====================================================

class Fixture(Base):
    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True, index=True)
    old_watt = Column(String, unique=True, nullable=False)
    new_watt = Column(String, nullable=False)
    saving_watt = Column(Integer, nullable=False)


# =====================================================
# MASTER CHAINAGE TABLE
# =====================================================

class MasterChainage(Base):
    __tablename__ = "master_chainage"

    id = Column(Integer, primary_key=True, index=True)

    chainage_code = Column(String, index=True, nullable=False)
    old_watt = Column(String, nullable=False)
    target_qty = Column(Integer, nullable=False)

    vendor_assigned = Column(String, nullable=True)


# =====================================================
# DISMANTLE LOG TABLE
# =====================================================

class DismantleLog(Base):
    __tablename__ = "dismantle_logs"

    id = Column(Integer, primary_key=True, index=True)

    entry_date = Column(Date, nullable=False)
    chainage_code = Column(String, nullable=False)
    old_watt = Column(String, nullable=False)

    qty = Column(Integer, nullable=False)
    manpower_deployed = Column(Integer)
    team = Column(String)

    entered_by = Column(Integer, ForeignKey("users.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================
# INSTALL LOG TABLE
# =====================================================

class InstallLog(Base):
    __tablename__ = "install_logs"

    id = Column(Integer, primary_key=True, index=True)

    entry_date = Column(Date, nullable=False)
    chainage_code = Column(String, nullable=False)
    old_watt = Column(String, nullable=False)
    new_watt = Column(String, nullable=False)

    qty = Column(Integer, nullable=False)
    manpower_deployed = Column(Integer)
    team = Column(String)

    entered_by = Column(Integer, ForeignKey("users.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
