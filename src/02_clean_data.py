"""
STAGE 1b: Clean scraped web pages + merge with PDF text
Inputs:
  - data/scraped/pages.jsonl
  - data/processed/pdf_pages.jsonl
Output: data/processed/all_documents.jsonl
"""
import os
import re
import json

INPUT_SCRAPED = "data/scraped/pages.jsonl"
INPUT_PDFS = "data/processed/pdf_pages.jsonl"
OUTPUT_PATH = "data/processed/all_documents.jsonl"


# Files to skip (admin/internal docs not useful for students)
SKIP_PDF_PATTERNS = [
    "MOM_",              # Minutes of Meeting
    "minutes_of_meeting",
    "SCC_",              # Standing Committee
    "senate",            # Senate documents
    "tender",
    "quotation",
    "invoice",
    "procurement",
    "audit",
    "budget_estimate",
    "internal_memo",
    "confidential",
]


# Common noise patterns in scraped web text
NOISE_PATTERNS = [
    r"(?i)cookie(s)?\s+(policy|notice|consent).*?(?=\n|$)",
    r"(?i)all rights reserved.*?(?=\n|$)",
    r"(?i)copyright\s+©.*?(?=\n|$)",
    r"(?i)subscribe\s+to\s+(our\s+)?newsletter.*?(?=\n|$)",
    r"(?i)follow\s+us\s+on.*?(?=\n|$)",
    r"(?i)click\s+here\s+to.*?(?=\n|$)",
    r"^\s*(home|about|contact|login|register|menu)\s*$",
    r"^\s*\|+\s*$",
]


def clean_text(text: str) -> str:
    """Clean a single text block."""
    # Remove noise patterns
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.MULTILINE)
    
    # Remove repeated whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    
    # Remove lines that are too short (likely nav/buttons)
    lines = text.split("\n")
    clean_lines = [l.strip() for l in lines if len(l.strip()) > 15]
    text = "\n".join(clean_lines)
    
    return text.strip()


def should_skip_pdf(filename: str) -> bool:
    """Check if a PDF filename matches any skip pattern."""
    fname_lower = filename.lower()
    return any(skip.lower() in fname_lower for skip in SKIP_PDF_PATTERNS)


def main():
    all_docs = []
    
    # ---- 1. Clean scraped web pages ----
    if os.path.exists(INPUT_SCRAPED):
        print(f"📥 Loading scraped pages...")
        with open(INPUT_SCRAPED, "r", encoding="utf-8") as f:
            scraped = [json.loads(line) for line in f]
        
        kept = 0
        for doc in scraped:
            cleaned = clean_text(doc["text"])
            if len(cleaned) < 200:
                continue
            
            all_docs.append({
                "source": doc["url"],
                "source_type": "web",
                "title": doc.get("title", ""),
                "text": cleaned,
            })
            kept += 1
        
        print(f"✅ Kept {kept}/{len(scraped)} web pages after cleaning")
    else:
        print(f"⚠️  {INPUT_SCRAPED} not found")
    
    # ---- 2. Add PDF pages (with skip filter) ----
    if os.path.exists(INPUT_PDFS):
        print(f"📥 Loading PDF pages...")
        with open(INPUT_PDFS, "r", encoding="utf-8") as f:
            pdf_pages = [json.loads(line) for line in f]
        
        kept = 0
        skipped = 0
        skipped_files = set()
        
        for doc in pdf_pages:
            # ⚠️ SKIP admin/internal PDFs
            if should_skip_pdf(doc["source"]):
                skipped += 1
                skipped_files.add(doc["source"])
                continue
            
            cleaned = clean_text(doc["text"])
            if len(cleaned) < 100:
                continue
            
            all_docs.append({
                "source": f"{doc['source']}#page={doc['page']}",
                "source_type": "pdf",
                "title": doc["source"],
                "page": doc["page"],
                "text": cleaned,
            })
            kept += 1
        
        print(f"✅ Kept {kept} PDF pages")
        print(f"🚫 Skipped {skipped} pages from {len(skipped_files)} admin PDFs")
        if skipped_files:
            print(f"   Skipped files: {sorted(skipped_files)[:10]}")
            if len(skipped_files) > 10:
                print(f"   ... and {len(skipped_files) - 10} more")
    else:
        print(f"⚠️  {INPUT_PDFS} not found")
    
    # ---- 3. Save ----
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for doc in all_docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    
    total_chars = sum(len(d["text"]) for d in all_docs)
    print(f"\n🎉 Total documents: {len(all_docs)}")
    print(f"   Total text: {total_chars:,} chars (~{total_chars//4:,} tokens)")
    print(f"💾 Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()