from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    face_encoding = Column(Text, nullable=True)
    face_image_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())

    profile = relationship("UserProfile", back_populates="user", uselist=False)
