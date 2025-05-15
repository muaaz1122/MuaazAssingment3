from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

# ✅ User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for Google users
    google_id = Column(String, unique=True, nullable=True)  # For Google OAuth2 users
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # ✅ Relationship to tasks
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")

# ✅ Task model
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    deadline = Column(DateTime, nullable=False)
    is_completed = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    # ✅ Foreign key to users
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="tasks")