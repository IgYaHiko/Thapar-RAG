"""
STAGE 4: RAG chain — retrieve + generate
Test: python src/05_rag_chain.py
"""
import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI

# ---- Config ----
INDEX_PATH = "index/faiss_index/index.faiss"
META_PATH = "index/chunks_metadata.jsonl"
MODEL_NAME = "BAAI/bge-small-en-v1.5"
TOP_K = 5

# Set your API key as env var: GOOGLE_API_KEY
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


# ---- Load once ----
print("🚀 Loading RAG components...")
embedder = SentenceTransformer(MODEL_NAME)
index = faiss.read_index(INDEX_PATH)

with open(META_PATH, "r", encoding="utf-8") as f:
    metadata = [json.loads(line) for line in f]

print(f"✅ Loaded {len(metadata)} chunks")


# ---- Retrieval ----
def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """Return top-k chunks most similar to query."""
    q_emb = embedder.encode([query], normalize_embeddings=True).astype("float32")
    scores, indices = index.search(q_emb, k)
    
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        chunk = metadata[idx].copy()
        chunk["score"] = float(score)
        results.append(chunk)
    return results


# ---- Generation ----
PROMPT_TEMPLATE = """You are SmartCampus Assistant for Thapar Institute students.

RULES:
1. Answer ONLY using the context below.
2. If the answer is not in the context, say: "I don't have this information. Please contact the concerned department."
3. Cite sources at the end using the format: [Source: <url_or_file>]
4. Be concise, clear, and student-friendly.
5. If the question is unrelated to the university, politely decline.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""


def generate_answer(query: str, retrieved: list[dict]) -> str:
    """Generate final answer using LLM."""
    context_blocks = []
    for i, r in enumerate(retrieved, 1):
        context_blocks.append(
            f"[{i}] {r['text']}\n(Source: {r['source']})"
        )
    context = "\n\n".join(context_blocks)
    
    prompt = PROMPT_TEMPLATE.format(context=context, question=query)
    
    if not GEMINI_API_KEY:
        # Fallback: return context only (retrieval-only mode)
        return f"[RETRIEVAL ONLY — set GOOGLE_API_KEY for full answers]\n\n{context}"
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.2,
    )
    response = llm.invoke(prompt)
    return response.content


def ask(query: str) -> dict:
    """Full RAG pipeline."""
    retrieved = retrieve(query, k=TOP_K)
    answer = generate_answer(query, retrieved)
    return {
        "query": query,
        "answer": answer,
        "sources": [
            {"url": r["source"], "score": r["score"], "preview": r["text"][:100]}
            for r in retrieved
        ],
    }


# ---- CLI test ----
if __name__ == "__main__":
    test_queries = [
        "What is the minimum attendance required for end semester exams?",
        "Where is the campus park?",
        "What are the hostel gate timings?",
    ]
    
    for q in test_queries:
        print(f"\n{'='*60}")
        print(f"❓ {q}")
        print("="*60)
        
        result = ask(q)
        print(f"\n💬 {result['answer']}")
        print(f"\n📚 Sources:")
        for s in result["sources"]:
            print(f"   • {s['url']} (score: {s['score']:.3f})")