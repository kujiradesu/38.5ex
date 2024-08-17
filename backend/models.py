from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)  # ハッシュ化されたパスワードを格納するカラム

    posts = relationship("Posts", back_populates="user", cascade="all, delete-orphan")

class Posts(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    activity_type = Column(String(50), index=True)
    status = Column(String(50), index=True)
    comment = Column(String(50), index=True)
    title = Column(String(100), index=True)
    description = Column(String(200))
    embedding = Column(LargeBinary)  # バイナリとして保存するカラム

    user = relationship("User", back_populates="posts")
