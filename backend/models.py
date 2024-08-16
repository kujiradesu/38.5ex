from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    # password カラムはプレーンなパスワードを格納していたが、セキュリティ上の理由で不要になるので削除可能
    # password = Column(String)  # 既存のプレーンなパスワードカラム（削除予定）
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

    user = relationship("User", back_populates="posts")

class TestItem(Base):
    __tablename__ = "test_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
