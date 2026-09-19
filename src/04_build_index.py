"""
STAGE 3: Embed chunks and build FAISS index
Input:  data/chunks/chunks.jsonl
Output: index/faiss_index/  +  index/chunks_metadata.jsonl
"""
import os
import json
import time
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

INPUT_PATH = "data/chunks/chunks.jsonl"
INDEX_DIR = "index/faiss_index"
META_PATH = "index/chunks_metadata.jsonl"
MODEL_NAME = "BAAI/bge-small-en-v1.5"

os.makedirs(INDEX_DIR, exist_ok=True)


def main():
    print(f"📥 Loading chunks...")
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]
    
    print(f"   Total: {len(chunks)} chunks")
    
    # ---- Load embedding model ----
    print(f"\n🧠 Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    dim = model.get_sentence_embedding_dimension()
    print(f"   Embedding dimension: {dim}")
    
    # ---- Embed in batches ----
    print(f"\n⚡ Embedding {len(chunks)} chunks (this may take 5-15 min)...")
    
    texts = [c["text"] for c in chunks]
    BATCH_SIZE = 64
    all_embeddings = []
    
    start = time.time()
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        emb = model.encode(
            batch,
            normalize_embeddings=True,   # for cosine similarity via inner product
            show_progress_bar=False,
        )
        all_embeddings.append(emb)
        
        done = min(i + BATCH_SIZE, len(texts))
        elapsed = time.time() - start
        speed = done / elapsed if elapsed > 0 else 0
        eta = (len(texts) - done) / speed if speed > 0 else 0
        print(f"   [{done}/{len(texts)}] {speed:.1f} chunks/s, ETA {eta:.0f}s")
    
    embeddings = np.vstack(all_embeddings).astype("float32")
    print(f"\n✅ Embeddings shape: {embeddings.shape}")
    
    # ---- Build FAISS index ----
    print(f"\n🏗️  Building FAISS index (inner product)...")
    index = faiss.IndexFlatIP(dim)   # cosine similarity (since vectors normalized)
    index.add(embeddings)
    
    faiss.write_index(index, os.path.join(INDEX_DIR, "index.faiss"))
    print(f"✅ Index saved: {INDEX_DIR}/index.faiss")
    
    # ---- Save metadata ----
    with open(META_PATH, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"✅ Metadata saved: {META_PATH}")
    
    print(f"\n🎉 INDEX READY")
    print(f"   Chunks:     {len(chunks):,}")
    print(f"   Dimension:  {dim}")
    print(f"   Index size: {os.path.getsize(os.path.join(INDEX_DIR, 'index.faiss'))/1e6:.1f} MB")


if __name__ == "__main__":
    main()