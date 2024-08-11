from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# FastAPIインスタンスを作成
app = FastAPI()

# データベース設定
DATABASE_URL = "mysql+mysqlconnector://root:385-ban@localhost/38.5ex_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# データベースと接続するための依存関係を追加
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ルートエンドポイント ("/") を定義
@app.get("/")
def read_root():
    return {"Hello": "World"}

# "/items/{item_id}" エンドポイントを定義
# ここでは、URLパラメータ item_id と、オプションのクエリパラメータ q を受け取ります
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
