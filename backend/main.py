from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import engine, Base, SessionLocal
from backend.routers import router
from backend.models import User, Activities  # Activities モデルをインポート
from typing import List, Optional

app = FastAPI()

# モデルの作成
Base.metadata.create_all(bind=engine)

# ルーターを追加
app.include_router(router)

@app.get("/")
def read_root():
    return {"Hello": "World"}

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

# ユーザーのCRUD操作用のエンドポイント

# Read (全てのユーザーを取得)
@app.get("/users/", response_model=List[str])
def read_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [user.username for user in users]

# Create (新規ユーザーを作成)
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(username=user.username, email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

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
        # 関連するActivitiesを削除
        db.query(Activities).filter(Activities.user_id == user_id).delete()
        
        # ユーザーを削除
        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "User and related activities deleted"}
