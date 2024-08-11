from fastapi import FastAPI
from .database import engine, Base
from .routers import item

app = FastAPI()

# モデルの作成
Base.metadata.create_all(bind=engine)

# ルーターを追加
app.include_router(item.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}
