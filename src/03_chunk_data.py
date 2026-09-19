"""
STAGE 2: Smarter chunking — bigger chunks with section awareness
Input:  data/processed/all_documents.jsonl
Output: data/chunks/chunks.jsonl
"""
import os
import re
import json

INPUT_PATH = "data/processed/all_documents.jsonl"
OUTPUT_PATH = "data/chunks/chunks.jsonl"

# Larger chunks → more complete context per retrieval
CHUNK_SIZE = 1200        # was 600
CHUNK_OVERLAP = 200      # was 100
MIN_CHUNK_SIZE = 200     # was 100

# Patterns that indicate a chunk is just a TOC / cover page / header (skip these)
SKIP_PATTERNS = [
    r"^table of contents",
    r"^contents\s*$",
    r"^index\s*$",
    r"^page \d+\s*$",
    r"^chapter \d+\s*$",
    r"^\d+\s*$",                  # pure page numbers
    r"^(list of|appendix|annexure)\s+",
]

os.makedirs("data/chunks", exist_ok=True)


def is_noise_chunk(text: str) -> bool:
    """Detect TOC / cover / header junk."""
    if len(text.strip()) < 50:
        return True
    first_line = text.strip().split("\n")[0].lower()
    for pattern in SKIP_PATTERNS:
        if re.match(pattern, first_line):
            return True
    # Ratio of digits/symbols to letters — TOC pages have lots of dots/numbers
    letters = sum(c.isalpha() for c in text)
    if len(text) > 0 and letters / len(text) < 0.4:
        return True
    return False


def smart_split(text: str) -> list[str]:
    """Recursive splitting — prefer paragraph > sentence > word."""
    if len(text) <= CHUNK_SIZE:
        return [text] if len(text) >= MIN_CHUNK_SIZE else []
    
    chunks = []
    
    # 1. Try splitting on double newlines (paragraphs)
    paragraphs = re.split(r"\n\s*\n", text)
    
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current) + len(para) + 2 <= CHUNK_SIZE:
            current = (current + "\n\n" + para).strip()
        else:
            if current and len(current) >= MIN_CHUNK_SIZE:
                chunks.append(current)
            
            # If a single paragraph is too big, split it further
            if len(para) > CHUNK_SIZE:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                sub = ""
                for sent in sentences:
                    if len(sub) + len(sent) + 1 <= CHUNK_SIZE:
                        sub = (sub + " " + sent).strip()
                    else:
                        if sub and len(sub) >= MIN_CHUNK_SIZE:
                            chunks.append(sub)
                        sub = sent
                if sub and len(sub) >= MIN_CHUNK_SIZE:
                    chunks.append(sub)
                current = ""
            else:
                current = para
    
    if current and len(current) >= MIN_CHUNK_SIZE:
        chunks.append(current)
    
    # 2. Add overlap between chunks
    overlapped = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            overlapped.append(chunk)
        else:
            prev_tail = chunks[i-1][-CHUNK_OVERLAP:]
            overlapped.append(prev_tail + "\n\n" + chunk)
    
    return overlapped


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        docs = [json.loads(line) for line in f]
    
    print(f"📥 Loaded {len(docs)} documents")
    
    all_chunks = []
    chunk_id = 0
    skipped_noise = 0
    
    for doc in docs:
        pieces = smart_split(doc["text"])
        
        for piece in pieces:
            piece = piece.strip()
            if len(piece) < MIN_CHUNK_SIZE:
                continue
            if is_noise_chunk(piece):
                skipped_noise += 1
                continue
            
            chunk_id += 1
            all_chunks.append({
                "id": f"chunk_{chunk_id:06d}",
                "text": piece,
                "source": doc["source"],
                "source_type": doc["source_type"],
                "title": doc.get("title", ""),
                "page": doc.get("page", None),
                "length": len(piece),
            })
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    
    avg_len = sum(c["length"] for c in all_chunks) / len(all_chunks)
    print(f"\n🎉 Created {len(all_chunks)} chunks")
    print(f"   Average size: {avg_len:.0f} chars  (was ~490)")
    print(f"   Skipped noise: {skipped_noise}")
    print(f"💾 Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()