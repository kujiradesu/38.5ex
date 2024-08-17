import numpy as np
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
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
import os
import bcrypt

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

app = FastAPI()

# CORS 設定
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

def get_password_hash(password):
    return pwd_context.hash(password)

model = SentenceTransformer('all-MiniLM-L6-v2')

def vectorize_post(title: str, description: str) -> np.ndarray:
    title_embedding = model.encode(title)
    description_embedding = model.encode(description)
    combined_embedding = (title_embedding + description_embedding) / 2
    return combined_embedding

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

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

class LoginRequest(BaseModel):
    username: str
    password: str

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

class PostCreate(BaseModel):
    activity_type: str
    status: str
    comment: str
    title: str
    description: str

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

@app.post("/posts/")
def create_post(post: PostCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    embedding = vectorize_post(post.title, post.description)
    db_post = Posts(
        user_id=current_user.id,
        activity_type=post.activity_type,
        status=post.status,
        comment=post.comment,
        title=post.title,
        description=post.description,
        embedding=embedding.tobytes()  # ベクトルをバイナリとして保存
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get("/map/")
def get_map_data(db: Session = Depends(get_db)):
    posts = db.query(Posts).all()
    embeddings = np.array([np.frombuffer(post.embedding) for post in posts])
    
    tsne = TSNE(n_components=2)
    reduced_embeddings = tsne.fit_transform(embeddings)
    
    map_data = [{"id": post.id, "x": float(coord[0]), "y": float(coord[1])} for post, coord in zip(posts, reduced_embeddings)]
    
    return map_data

@app.post("/search/")
def search_posts(query: str, db: Session = Depends(get_db)):
    query_embedding = model.encode(query)
    posts = db.query(Posts).all()
    embeddings = np.array([np.frombuffer(post.embedding) for post in posts])
    
    similarities = cosine_similarity([query_embedding], embeddings)[0]
    similar_posts = [post for post, similarity in zip(posts, similarities) if similarity > 0.5]
    
    return similar_posts
