from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary, Float, Text
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy import Double
from pydantic import BaseModel
from typing import Optional


# Userモデル: ユーザー情報を保存するためのテーブル
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)  # ハッシュ化されたパスワードを格納するカラム

    posts = relationship("Posts", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="user", uselist=False)

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    job_title = Column(String, nullable=True)
    job_description = Column(String, nullable=True)
    interests = Column(String, nullable=True)
    skills = Column(String, nullable=True)
    values = Column(String, nullable=True)
    office_floor = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)
    
    user = relationship("User", back_populates="profile")


# Postsモデル: 投稿情報を保存するためのテーブル
class Posts(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    activity_type = Column(String(255), nullable=False)
    status = Column(String(255), nullable=False)
    comment = Column(String(255), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    embedding = Column(LargeBinary, nullable=True)

    x_coord = Column(Double, nullable=True)
    y_coord = Column(Double, nullable=True)

    user = relationship("User", back_populates="posts")

class ProfileResponse(BaseModel):
    username: str
    jobTitle: Optional[str] = None
    jobDescription: Optional[str] = None
    interests: Optional[str] = None
    skills: Optional[str] = None
    values: Optional[str] = None
    officeFloor: Optional[str] = None
    profileImage: Optional[str] = None  # プロフィール画像のURLなど
    class Config:
        from_attributes = True