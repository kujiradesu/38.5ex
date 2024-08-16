from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import engine, Base, SessionLocal
from backend.routers import router
from backend.models import User, Posts
from typing import List, Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from passlib.context import CryptContext
import os
import bcrypt

load_dotenv()  # .envファイルを読み込む

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

app = FastAPI()

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 3000ポートからのリクエストを許可
    allow_credentials=True,
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
)

# モデルの作成
Base.metadata.create_all(bind=engine)

# ルーターを追加
app.include_router(router)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# パスワードハッシュ化のためのコンテキストを作成
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# パスワードをハッシュ化するヘルパー関数
def get_password_hash(password):
    return pwd_context.hash(password)

# JWTトークンの生成
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# DBセッションの取得
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ユーザー作成用のPydanticモデル
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

# ユーザー更新用のPydanticモデル
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

# Create (新規ユーザーを作成)
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Read (全てのユーザーを取得)
@app.get("/users/", response_model=List[str])
def read_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [user.username for user in users]

# Update (既存のユーザーを更新)
@app.put("/users/{user_id}")
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.username:
        user.username = user_update.username
    if user_update.email:
        user.email = user_update.email

    db.commit()
    db.refresh(user)
    return user

# Delete (ユーザーを削除)
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # 関連するPostsを削除
        db.query(Posts).filter(Posts.user_id == user_id).delete()
        
        # ユーザーを削除
        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "User and related posts deleted"}

# ログイン用のリクエストボディモデル
class LoginRequest(BaseModel):
    username: str
    password: str

# ログインエンドポイントの作成
@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    print(f"Login attempt with username: {request.username}")
    user = db.query(User).filter(User.username == request.username).first()
    if user and bcrypt.checkpw(request.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        access_token = create_access_token(data={"sub": str(user.id)})
        print(f"Token generated: {access_token}")
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        print("Invalid username or password")
        raise HTTPException(status_code=401, detail="Invalid username or password")


# 新規投稿を作成するためのPydanticモデル
class PostCreate(BaseModel):
    activity_type: str
    status: str
    comment: str
    title: str
    description: str

# ユーザーを取得するヘルパー関数
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# 投稿作成エンドポイント
@app.post("/posts/")
def create_post(post: PostCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_post = Posts(user_id=current_user.id, **post.dict())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post
