from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    employee_id = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)
    role = Column(String, nullable=False)  # admin / staff / vendor
    vendor_team = Column(String, nullable=True)  # A / B
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Fixture(Base):
    __tablename__ = "fixtures"

    old_watt = Column(Integer, primary_key=True)
    new_watt = Column(Integer, nullable=False)
    saving_watt = Column(Integer, nullable=False)


class MasterChainage(Base):
    __tablename__ = "master_chainage"

    id = Column(Integer, primary_key=True)
    chainage_code = Column(String, index=True)
    old_watt = Column(Integer)
    target_qty = Column(Integer)
    vendor_assigned = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DismantleLog(Base):
    __tablename__ = "dismantle_log"

    id = Column(Integer, primary_key=True)
    entry_date = Column(Date)
    chainage_code = Column(String, index=True)
    old_watt = Column(Integer)
    qty = Column(Integer)
    manpower_deployed = Column(Integer)
    team = Column(String)
    entered_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InstallLog(Base):
    __tablename__ = "install_log"

    id = Column(Integer, primary_key=True)
    entry_date = Column(Date)
    chainage_code = Column(String, index=True)
    old_watt = Column(Integer)
    new_watt = Column(Integer)
    qty = Column(Integer)
    manpower_deployed = Column(Integer)
    team = Column(String)
    entered_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())