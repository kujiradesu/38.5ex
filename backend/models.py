from sqlalchemy import Column, Integer, String, ForeignKey, LargeBinary, Float, Text
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy import Double


# Userモデル: ユーザー情報を保存するためのテーブル
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)  # ハッシュ化されたパスワードを格納するカラム

    posts = relationship("Posts", back_populates="user", cascade="all, delete-orphan")

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
