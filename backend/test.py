""""
import sys
import os
import numpy as np
import umap
import matplotlib.pyplot as plt
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base
from backend.models import Posts

# プロジェクトのルートディレクトリをsys.pathに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

# データベースセッションを取得する関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 特定のポストIDに対する埋め込みベクトルを確認する関数
def check_embedding_in_db(post_id: int):
    db = next(get_db())  # セッションを取得
    post = db.query(Posts).filter(Posts.id == post_id).first()
    if post and post.embedding:
        embedding = np.frombuffer(post.embedding, dtype=np.float32)
        print(f"Embedding vector for post {post_id}: {embedding}")
        return embedding
    else:
        print(f"No embedding found for post {post_id}")
        return None

# UMAPによる次元削減
def reduce_dimensions(embeddings):
    umap_model = umap.UMAP(n_neighbors=15, min_dist=0.1, metric='cosine')
    reduced_embeddings = umap_model.fit_transform(embeddings)
    print("Reduced 2D embeddings:")
    print(reduced_embeddings)  # 2次元ベクトルを出力
    return reduced_embeddings

# データベースから全ての埋め込みを取得し、UMAPで2次元に削減して保存する
def update_all_post_coordinates():
    db = next(get_db())  # セッションを取得
    try:
        posts = db.query(Posts).all()
        embeddings = []
        valid_posts = []

        for post in posts:
            if post.embedding:
                # BLOB データを NumPy 配列に変換
                embedding = np.frombuffer(post.embedding, dtype=np.float32)
                if embedding.shape == (768,):  # 期待される次元数か確認
                    embeddings.append(embedding)
                    valid_posts.append(post)

        if len(embeddings) == 0:
            print("No valid embeddings found.")
            return

        # 次元削減を行う
        reduced_embeddings = reduce_dimensions(np.array(embeddings))

        # 2次元ベクトルを保存
        for post, coord in zip(valid_posts, reduced_embeddings):
            post.x_coord = float(coord[0])
            post.y_coord = float(coord[1])
            db.commit()
            db.refresh(post)

        print("All post coordinates updated successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    # まず、埋め込みベクトルを確認
    embedding_vector = check_embedding_in_db(post_id=1)  # 1は例で、実際のポストIDに置き換えてください
    
    # すべてのポストの埋め込みをUMAPで次元削減して保存し、2次元ベクトルを出力
    update_all_post_coordinates()
"""