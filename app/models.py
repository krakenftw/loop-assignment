# models.py

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Store(Base):
    __tablename__ = "stores"

    id = Column(BigInteger, primary_key=True, index=True)
    timezone = Column(String, default="America/Chicago")
    statuses = relationship("StoreStatus", back_populates="store")
    business_hours = relationship("StoreBusinessHours", back_populates="store")

class StoreStatus(Base):
    __tablename__ = "store_statuses"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(BigInteger, ForeignKey("stores.id"))
    timestamp_utc = Column(DateTime)
    status = Column(String)
    store = relationship("Store", back_populates="statuses")

class StoreBusinessHours(Base):
    __tablename__ = "store_business_hours"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(BigInteger, ForeignKey("stores.id"))
    day_of_week = Column(Integer)
    start_time_local = Column(DateTime)
    end_time_local = Column(DateTime)
    store = relationship("Store", back_populates="business_hours")

class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, index=True)
    status = Column(String, default="running")
    generated_at = Column(DateTime)
    report_csv = Column(String, nullable=True)