import os
import pinecone
from sentence_transformers import SentenceTransformer
from backend.database import SessionLocal
from backend.models import Posts

# Pineconeクライアントの初期化
pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment="us-west1-gcp")

# Pineconeインデックスの指定
index = pinecone.Index("post_embeddings")

# SentenceTransformerのロード（main.pyで使用しているモデルと同じものを使用）
model = SentenceTransformer('paraphrase-mpnet-base-v2')

# データベースセッションを作成
db = SessionLocal()

# 投稿データの取得
posts = db.query(Posts).all()

# 各投稿のベクトルを生成し、Pineconeにアップロード
for post in posts:
    text = post.title + " " + post.description
    embedding = model.encode(text)
    if embedding.shape == (768,):  # 期待する次元数
        post.embedding = embedding.tobytes()  # 埋め込みをデータベースに保存
        index.upsert([(str(post.id), embedding.tolist())])
    else:
        print(f"Unexpected embedding shape: {embedding.shape} for post ID: {post.id}")

db.commit()  # 変更をコミットしてデータベースに保存
db.close()

print("ベクトルデータがPineconeにアップロードされました。")
