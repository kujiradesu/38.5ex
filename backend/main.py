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
from backend.database import engine, Base, SessionLocal

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from typing import List, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import DBSCAN
from pydantic import BaseModel
from typing import Optional

from backend.database import engine, Base, SessionLocal
from backend.models import User, Posts, UserProfile, ProfileResponse
from backend.routers import router
from passlib.context import CryptContext  # 修正ポイント：CryptContextのインポート


# Load environment variables
load_dotenv()

# Initialize Pinecone
api_key = os.getenv("PINECONE_API_KEY")
if not api_key:
    raise ValueError("Pinecone APIキーが設定されていません。")
print("Pinecone APIキー:", api_key)
# 修正ポイント：Pineconeのインスタンスを作成
pc = pinecone.Pinecone(api_key=api_key)

index_name = "my-index"

# 既存のインデックスを削除（もし存在する場合）
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=768,  # 1536次元でもOK
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

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

# main.pyのvectorize_post関数内に追加

def vectorize_post(title: str, description: str) -> np.ndarray:
    title_embedding = model.encode(title)
    description_embedding = model.encode(description)
    
    # タイトルに0.6、詳細説明に0.4の重みを付けて平均化
    combined_embedding = 0.6 * title_embedding + 0.4 * description_embedding

    # エンベディングのデバッグ出力
    print(f"Title embedding: {title_embedding}")
    print(f"Description embedding: {description_embedding}")
    print(f"Combined embedding: {combined_embedding}")

    return combined_embedding

# クラスタリングを実行する関数
def cluster_embeddings(embeddings):
    # DBSCANを使ってクラスタリング
    clustering = DBSCAN(eps=0.5, min_samples=5, metric='cosine').fit(embeddings)
    labels = clustering.labels_
    
    # ラベルが-1の場合、ノイズとして扱う
    print(f"Labels: {labels}")
    return labels


# t-SNEを使って次元削減を行う関数
def get_2d_embeddings_with_tsne(embeddings):
    embeddings = np.array(embeddings)
    
    try:
        tsne = TSNE(n_components=2, perplexity=5, random_state=42)
        reduced_embeddings = tsne.fit_transform(embeddings)
        print(f"Reduced Embeddings with t-SNE: {reduced_embeddings}")
    except Exception as e:
        print(f"t-SNE failed: {e}")
        reduced_embeddings = embeddings[:, :2]  # 最初の2つの次元を使用
    
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

# 埋め込みデータを標準化
def standardize_embeddings(embeddings):
    scaler = StandardScaler()
    standardized_embeddings = scaler.fit_transform(embeddings)
    return standardized_embeddings

def preprocess_embeddings(embeddings, n_components=100):
    pca = PCA(n_components=n_components)
    reduced_embeddings = pca.fit_transform(embeddings)
    return reduced_embeddings

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

@app.get("/profile", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile_data = {
        "username": current_user.username,
        "jobTitle": profile.job_title,
        "jobDescription": profile.work_description,
        "interests": profile.interests,
        "skills": profile.skills,
        "values": profile.values,
        "officeFloor": profile.frequent_floor,
        "profileImage": profile.profile_picture
    }
    return profile_data

@app.put("/profile", response_model=ProfileResponse)
def update_profile(profile_data: ProfileResponse, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile.job_title = profile_data.jobTitle
    profile.job_description = profile_data.jobDescription
    profile.interests = profile_data.interests
    profile.skills = profile_data.skills
    profile.values = profile_data.values
    profile.office_floor = profile_data.officeFloor
    profile.profile_image = profile_data.profileImage
    
    db.commit()
    db.refresh(profile)
    
    return ProfileResponse(
        username=current_user.username,
        jobTitle=profile.job_title,
        jobDescription=profile.job_description,
        interests=profile.interests,
        skills=profile.skills,
        values=profile.values,
        officeFloor=profile.office_floor,
        profileImage=profile.profile_image
    )

@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    
    if user is None or not bcrypt.checkpw(request.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

# POSTリクエストの処理部分に追加
@app.post("/home/")
def create_post(post: PostCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # タイトルと説明からベクトルを作成します
    embedding = vectorize_post(post.title, post.description)
    
    # クラスタリングを実行
    labels = cluster_embeddings([embedding])
    
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

    # t-SNEで次元削減を行う
    reduced_embeddings = get_2d_embeddings_with_tsne([embedding])
    print(f"Reduced 2D Embeddings: {reduced_embeddings}")

    if reduced_embeddings.shape[1] == 2:  # 次元数が2であることを確認
        db_post.x_coord = float(reduced_embeddings[0][0])
        db_post.y_coord = float(reduced_embeddings[0][1])
        print(f"x_coord: {db_post.x_coord}, y_coord: {db_post.y_coord}")  # コミット前に確認
        db.commit()
    else:
        print("Error: Reduced embedding does not have 2 dimensions")

    # デバッグ: データベースに保存された値を再度取得して確認
    db.refresh(db_post)
    print(f"Database x_coord: {db_post.x_coord}, y_coord: {db_post.y_coord}")

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

@app.post("/search/")
def search_posts(query: str, db: Session = Depends(get_db)):
    query_embedding = model.encode(query).tolist()
    search_result = index.query(queries=[query_embedding], top_k=5)
    
    post_ids = [int(match['id'].split("#")[1]) for match in search_result['matches']]
    similar_posts = db.query(Posts).filter(Posts.id.in_(post_ids)).all()
    
    return similar_posts

@app.get("/home/")
def get_map_data(db: Session = Depends(get_db)):
    try:
        posts = db.query(Posts).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    map_data = [
        {
            "id": post.id,
            "title": post.title,
            "description": post.description,
            "x": post.x_coord,
            "y": post.y_coord,
            "status": post.status
        } for post in posts if post.x_coord is not None and post.y_coord is not None
    ]
    return map_data


@app.on_event("startup")
def startup_event():
    try:
        # データベース接続をテストするための簡単なクエリ
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connected successfully.")
    except Exception as e:
        print("Database connection failed:", e)