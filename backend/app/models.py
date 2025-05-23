# app/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime , JSON
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    twofa_secret = Column(String)
    role=Column(String, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FileUpload(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))    
    file_hash = Column(String)
    chunk_count = Column(Integer)
    ivs = Column(JSON)  # Base64-encoded IVs for each chunk
    aws_url = Column(String)  # AWS S3 URL
    azure_url = Column(String)  # Azure Blob Storage URL
    encrypted_key = Column(String)  # Base64-encoded AES key (encrypted)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    ip = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
