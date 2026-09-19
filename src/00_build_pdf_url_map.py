"""
Build a filename → source URL mapping from pdf_urls.txt
Output: data/pdf_url_map.json
"""
import json
import os
from urllib.parse import urlparse, unquote

URLS_FILE = "data/pdfs/pdf_urls.txt"
OUTPUT = "data/pdf_url_map.json"

def main():
    if not os.path.exists(URLS_FILE):
        print(f"❌ {URLS_FILE} not found")
        return
    
    mapping = {}
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if not url:
                continue
            
            # Extract filename from URL
            path = urlparse(url).path
            filename = unquote(path.split("/")[-1].split("?")[0])
            
            if not filename.lower().endswith(".pdf"):
                continue
            
            # Also store a safe version (matching what we saved to disk)
            import re
            safe = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)[:150]
            
            mapping[filename] = url
            mapping[safe] = url            # key by both original and safe name
            mapping[safe.replace(".pdf", "")] = url
    
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    
    print(f"✅ Saved {len(mapping)} mappings to {OUTPUT}")
    print(f"   Sample:")
    for k, v in list(mapping.items())[:5]:
        print(f"   {k} → {v}")

if __name__ == "__main__":
    main()