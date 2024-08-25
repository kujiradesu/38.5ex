from pydantic import BaseModel
# PydanticのLoginRequestモデル: ログインリクエストのためのモデル
class LoginRequest(BaseModel):
    username: str
    password: str

import os
import numpy as np
import base64
import bcrypt
import umap
import pinecone 
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from typing import List, Optional
from pinecone import Pinecone, ServerlessSpec  # 修正ポイント：Pineconeのインポート

from backend.database import engine, Base, SessionLocal
from backend.models import User, Posts
from backend.routers import router
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

# Initialize Pinecone
api_key = os.getenv("PINECONE_API_KEY")
if not api_key:
    raise ValueError("Pinecone APIキーが設定されていません。")

# 修正ポイント：Pineconeのインスタンスを作成
pc = Pinecone(api_key=api_key)

index_name = "my-index"

# 既存のインデックスを削除（もし存在する場合）
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=768,  # 1536次元に設定
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )

index = pc.Index(index_name)  # インデックスオブジェクトを作成

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.include_router(router)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
model = SentenceTransformer('paraphrase-mpnet-base-v2') # 1536次元のベクトルを生成するモデル

# Utility functions
def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def vectorize_post(title: str, description: str) -> np.ndarray:
    title_embedding = model.encode(title)
    description_embedding = model.encode(description)
    
    # 生成されたベクトルの次元数を確認
    print(f"Title embedding dimension: {title_embedding.shape}")
    print(f"Description embedding dimension: {description_embedding.shape}")
    
    combined_embedding = (title_embedding + description_embedding) / 2
    
    # 結合されたベクトルの次元数を確認
    print(f"Combined embedding dimension: {combined_embedding.shape}")
    
    return combined_embedding



def get_2d_embeddings(embeddings):
    umap_model = umap.UMAP(n_neighbors=15, min_dist=0.1, metric='cosine')
    reduced_embeddings = umap_model.fit_transform(embeddings)
    print(f"Reduced Embeddings: {reduced_embeddings}")  # デバッグのために出力
    return reduced_embeddings



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

# Models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

class PostCreate(BaseModel):
    activity_type: str
    status: str
    comment: str
    title: str
    description: str

# Endpoints
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[str])
def read_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [user.username for user in users]

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

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        db.query(Posts).filter(Posts.user_id == user_id).delete()
        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "User and related posts deleted"}

@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    
    if user is None or not bcrypt.checkpw(request.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/posts/")
def create_post(post: PostCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # タイトルと説明からベクトルを作成します
    embedding = vectorize_post(post.title, post.description)
    
    # 新しいポストをデータベースに保存します
    db_post = Posts(
        user_id=current_user.id, 
        activity_type=post.activity_type, 
        status=post.status, 
        comment=post.comment, 
        title=post.title, 
        description=post.description,
        embedding=embedding.tobytes()  # ここでベクトルを保存
    )
    
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    # Pineconeにベクトルをアップサートします
    pinecone_key = f"{current_user.id}#{db_post.id}"  # ユニークキーを作成
    index.upsert(vectors=[(pinecone_key, embedding.tolist())])  # Pineconeにアップサート

    # x_coordとy_coordもデータベースに保存する場合
    reduced_embedding = get_2d_embeddings([embedding])[0]
    db_post.x_coord = reduced_embedding[0]
    db_post.y_coord = reduced_embedding[1]
    print(f"x_coord: {db_post.x_coord}, y_coord: {db_post.y_coord}")  # コミット前に確認
    db.commit()
    db.refresh(db_post)

    response_data = {
        "id": db_post.id,
        "activity_type": db_post.activity_type,
        "status": db_post.status,
        "comment": db_post.comment,
        "title": db_post.title,
        "description": db_post.description,
        "embedding": base64.b64encode(db_post.embedding).decode('utf-8'),
        "x_coord": db_post.x_coord,
        "y_coord": db_post.y_coord
    }
    
    return response_data



@app.get("/map/")
def get_map_data(db: Session = Depends(get_db)):
    posts = db.query(Posts).all()
    
    embeddings = []
    valid_posts = []
    for post in posts:
        if post.embedding:
            embedding = np.frombuffer(post.embedding)
            if embedding.shape == (768,):  # 正しい形状か確認
                embeddings.append(embedding)
                valid_posts.append(post)
            else:
                print(f"Unexpected embedding shape: {embedding.shape}")
    
    if len(embeddings) == 0:
        raise HTTPException(status_code=404, detail="No valid embeddings found.")

    # 次元削減を適用
    reduced_embeddings = get_2d_embeddings(np.array(embeddings))
    print("Reduced Embeddings:", reduced_embeddings)  # 圧縮されたベクトルの確認


    # 縮小したベクトルを保存
    for post, coord in zip(valid_posts, reduced_embeddings):
        print(f"Saving coordinates for post {post.id}: x={coord[0]}, y={coord[1]}")
        post.x_coord = float(coord[0])
        post.y_coord = float(coord[1])
        db.commit()

    
    map_data = [
        {
            "id": post.id,
            "title": post.title,
            "description": post.description,
            "x": post.x_coord,
            "y": post.y_coord,
            "status": post.status
        } for post in valid_posts
    ]
    
    return map_data



@app.post("/search/")
def search_posts(query: str, db: Session = Depends(get_db)):
    query_embedding = model.encode(query).tolist()
    search_result = index.query(queries=[query_embedding], top_k=5)
    
    # post_idsを抽出
    post_ids = [int(match['id'].split("#")[1]) for match in search_result['matches']]
    similar_posts = db.query(Posts).filter(Posts.id.in_(post_ids)).all()
    
    return similar_posts

@app.get("/get_reduced_embeddings/")
def get_reduced_embeddings(query: str, db: Session = Depends(get_db)):
    # クエリに基づいてPineconeからベクトルを取得
    query_embedding = model.encode(query).tolist()
    search_result = index.query(queries=[query_embedding], top_k=100)
    
    # 取得したベクトルのIDから対応する投稿を取得
    post_ids = [int(match['id'].split("#")[1]) for match in search_result['matches']]
    posts = db.query(Posts).filter(Posts.id.in_(post_ids)).all()
    
    embeddings = []
    valid_posts = []
    
    for post in posts:
        if post.embedding:
            embedding = np.frombuffer(post.embedding, dtype=np.float32)
            if embedding.shape == (768,):  # 正しい形状か確認
                embeddings.append(embedding)
                valid_posts.append(post)
            else:
                print(f"Unexpected embedding shape: {embedding.shape}")

    if len(embeddings) == 0:
        raise HTTPException(status_code=404, detail="No valid embeddings found.")

    # 次元削減を行う
    reduced_embeddings = get_2d_embeddings(np.array(embeddings))

    # 次元削減された結果をDBに保存
    for post, coord in zip(valid_posts, reduced_embeddings):
        post.x_coord = float(coord[0])
        post.y_coord = float(coord[1])
    
    db.commit()

    return {"message": "Reduced embeddings saved to database."}
