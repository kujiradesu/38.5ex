import os
import numpy as np
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import umap

# .env ファイルを読み込む
load_dotenv()

# APIキーを取得
api_key = os.getenv("PINECONE_API_KEY")

# APIキーが取得できない場合、エラーメッセージを出力
if not api_key:
    raise ValueError("Pinecone APIキーが設定されていません。")

# Pineconeクライアントの初期化
pc = Pinecone(
    api_key=api_key
)

index_name = "my-index"  # 既存のインデックス名を指定
index = pc.Index(index_name)  # インデックスオブジェクトを取得

def check_vectors_from_pinecone(vector_id):
    # Pineconeからベクトルを取得
    response = index.fetch(ids=[vector_id])
    vectors = response['vectors']

    # 取得したベクトルを確認
    if vector_id in vectors:
        vector_data = vectors[vector_id]['values']
        print(f"Vector for ID {vector_id}: {vector_data}")
        return np.array(vector_data)
    else:
        print(f"Vector with ID {vector_id} not found.")
        return None

# 次元削減処理
def perform_dimensionality_reduction(embedding):
    # UMAPを使用して次元削減を行う
    umap_model = umap.UMAP(n_neighbors=5, min_dist=0.3, metric='cosine')
    reduced_embedding = umap_model.fit_transform(embedding.reshape(1, -1))
    print(f"Reduced Embedding (2D): {reduced_embedding}")
    return reduced_embedding

# 確認したいベクトルIDを指定
vector_id = "1#3"  # 例: '1#3'
vector_data = check_vectors_from_pinecone(vector_id)

if vector_data is not None:
    print("ベクトルが正しく取得されました。")
    # 次元削減を実行
    reduced_embedding = perform_dimensionality_reduction(vector_data)
else:
    print("ベクトルが見つかりませんでした。")
