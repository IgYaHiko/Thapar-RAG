"""
Reusable RAG chain module — imported by both CLI and Streamlit app.
"""
import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from src.source_utils import format_source_for_display

# ---- Config ----
INDEX_PATH = "index/faiss_index/index.faiss"
META_PATH = "index/chunks_metadata.jsonl"
MODEL_NAME = "BAAI/bge-small-en-v1.5"
TOP_K = 8  # was 5 — more context = richer answers

GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# ---- Load once ----
print("🚀 Loading RAG components...")
embedder = SentenceTransformer(MODEL_NAME)
index = faiss.read_index(INDEX_PATH)

with open(META_PATH, "r", encoding="utf-8") as f:
    metadata = [json.loads(line) for line in f]

print(f"✅ Loaded {len(metadata)} chunks")


def retrieve(query: str, k: int = TOP_K, min_score: float = 0.30) -> list[dict]:
    """
    Return top-k chunks most similar to the query.
    Filters out anything below min_score to avoid garbage sources.
    """
    # Encode query
    q_emb = embedder.encode([query], normalize_embeddings=True).astype("float32")
    
    # Search FAISS
    scores, indices = index.search(q_emb, k)
    
    # Build results
    results = []
    for score, idx in zip(scores[0], indices[0]):   # ← singular `score` for loop, plural `scores` from FAISS
        if idx < 0:
            continue
        if score < min_score:   # skip weak matches
            continue
        chunk = metadata[idx].copy()
        chunk["score"] = float(score)
        results.append(chunk)
    
    return results

PROMPT_TEMPLATE = """You are SmartCampus Assistant for Thapar Institute students.

Your goal: give a THOROUGH, WELL-STRUCTURED answer using the CONTEXT below.

## FORMATTING RULES
- Use **markdown** formatting:
  - Use `##` or `###` for section headings when the answer has multiple parts
  - Use bullet points (`-`) for lists, rules, or steps
  - Use **bold** for key terms (e.g., numbers, deadlines, names)
  - Use numbered lists for step-by-step procedures
- Aim for 100–250 words unless the question is simple.
- Be comprehensive — include ALL relevant details from the context.

## ANSWERING RULES
1. If the context contains ANY relevant information, use it.
2. Do NOT copy the context verbatim — summarize and structure it.
3. If a rule has conditions (e.g., "unless medical proof"), always mention them.
4. If the context has numbers, dates, or percentages — state them exactly.
5. Only say "I don't have this information. Please contact the concerned department." 
   if the context is COMPLETELY unrelated to the question.
6. Never mention source filenames inline — sources are shown separately in the UI.
7. Never output raw context blocks — always produce a natural, structured answer.

## EXAMPLE (good answer style)

**Question:** What is the minimum attendance required?

**Good answer:**
### Attendance Requirement
- Students must maintain a minimum of **75% attendance** to appear for end-semester exams.
- Students with attendance between **65% and 75%** may apply for **condonation** with valid medical documentation.
- Students below **65%** are **not eligible** to appear for end-semester exams.

### Additional Notes
- Attendance is calculated per subject.
- Lab sessions may have separate requirements.

---

CONTEXT:
{context}

QUESTION: {question}

ANSWER (use markdown, be detailed and well-structured):"""


def generate_answer(query: str, retrieved: list[dict]) -> str:
    context_blocks = []
    for i, r in enumerate(retrieved, 1):
        context_blocks.append(f"[{i}] {r['text']}\n(Source: {r['source']})")
    context = "\n\n".join(context_blocks)
    prompt = PROMPT_TEMPLATE.format(context=context, question=query)

    if not GEMINI_API_KEY:
        return f"[RETRIEVAL ONLY — set GOOGLE_API_KEY]\n\n{context}"

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",  # 👈 change this to whichever works
        google_api_key=GEMINI_API_KEY,
        temperature=0.2,
    )
    response = llm.invoke(prompt)
    return response.content


def ask(query: str) -> dict:
    retrieved = retrieve(query, k=TOP_K)
    answer = generate_answer(query, retrieved)
    
    sources = []
    for r in retrieved:
        # Try new friendly format
        try:
            from src.source_utils import format_source_for_display
            display = format_source_for_display(r["source"])
            sources.append({
                "friendly_name": display["friendly_name"],
                "link": display["link"],
                "raw": r["source"],
                "score": r["score"],
                "preview": r["text"][:150],
            })
        except Exception:
            # Fallback to old format
            sources.append({
                "url": r["source"],
                "score": r["score"],
                "preview": r["text"][:150],
            })
    
    return {
        "query": query,
        "answer": answer,
        "sources": sources,
    }