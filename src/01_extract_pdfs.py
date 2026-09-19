"""
STAGE 1a: Extract text from all PDFs in data/pdfs/
Output: data/processed/pdf_pages.jsonl
"""
import os
import json
from pypdf import PdfReader

PDF_DIR = "data/pdfs"
OUTPUT_PATH = "data/processed/pdf_pages.jsonl"

os.makedirs("data/processed", exist_ok=True)


def extract_pdf(pdf_path: str) -> list[dict]:
    """Extract text page-by-page from a PDF."""
    pages = []
    try:
        reader = PdfReader(pdf_path)
        filename = os.path.basename(pdf_path)
        
        for page_num, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text() or ""
                text = text.strip()
                
                if len(text) < 50:  # skip empty pages
                    continue
                
                pages.append({
                    "source": filename,
                    "source_type": "pdf",
                    "page": page_num,
                    "text": text,
                })
            except Exception as e:
                print(f"  ⚠️  Page {page_num} failed: {e}")
    
    except Exception as e:
        print(f"❌ Failed to read {pdf_path}: {e}")
    
    return pages


def main():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print(f"❌ No PDFs found in {PDF_DIR}/")
        return
    
    print(f"📄 Processing {len(pdf_files)} PDFs...\n")
    
    all_pages = []
    for i, pdf_file in enumerate(pdf_files, 1):
        path = os.path.join(PDF_DIR, pdf_file)
        pages = extract_pdf(path)
        all_pages.extend(pages)
        print(f"[{i}/{len(pdf_files)}] ✅ {pdf_file} → {len(pages)} pages")
    
    # Save JSONL
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for record in all_pages:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"\n🎉 Extracted {len(all_pages)} PDF pages total")
    print(f"💾 Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()