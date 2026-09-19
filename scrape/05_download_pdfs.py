"""
STEP 5: Find and download all PDFs linked from scraped pages
Output: data/pdfs/*.pdf
"""
import os
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

INPUT_PATH = "data/sitemap/filtered_urls.txt"
OUTPUT_DIR = "data/pdfs"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (StudentProject; contact: your.email@thapar.edu)"
}

DELAY = 1.0
TIMEOUT = 60


def safe_pdf_name(url: str) -> str:
    """Extract a safe filename from PDF URL."""
    path = urlparse(url).path
    name = path.split("/")[-1].split("?")[0]
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name[:150]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"🔍 Scanning {len(urls)} pages for PDF links...\n")
    
    # -------- Phase 1: Collect PDF URLs --------
    pdf_urls = set()
    for i, url in enumerate(urls, 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
            if r.status_code != 200:
                continue
            
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.lower().endswith(".pdf"):
                    pdf_urls.add(urljoin(url, href))
            
            print(f"[{i}/{len(urls)}] 🔗 {url} (found {len(pdf_urls)} so far)")
            time.sleep(DELAY)
        except Exception as e:
            print(f"[{i}/{len(urls)}] ⚠️  {url}: {str(e)[:60]}")
    
    print(f"\n📄 Found {len(pdf_urls)} unique PDF URLs")
    
    # Save list
    with open("data/pdfs/pdf_urls.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(pdf_urls)))
    
    # -------- Phase 2: Download PDFs --------
    print(f"\n⬇️  Downloading PDFs...\n")
    
    downloaded = 0
    failed = 0
    
    for i, pdf_url in enumerate(sorted(pdf_urls), 1):
        fname = safe_pdf_name(pdf_url)
        fpath = os.path.join(OUTPUT_DIR, fname)
        
        # Skip if already downloaded
        if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
            print(f"[{i}/{len(pdf_urls)}] ⏭️  Already exists: {fname}")
            downloaded += 1
            continue
        
        try:
            r = requests.get(pdf_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            ctype = r.headers.get("Content-Type", "").lower()
            
            if r.status_code == 200 and ("pdf" in ctype or pdf_url.lower().endswith(".pdf")):
                with open(fpath, "wb") as f:
                    f.write(r.content)
                size_kb = len(r.content) / 1024
                print(f"[{i}/{len(pdf_urls)}] 📄 {fname} ({size_kb:.1f} KB)")
                downloaded += 1
            else:
                print(f"[{i}/{len(pdf_urls)}] ⚠️  Not a PDF: {pdf_url}")
                failed += 1
        except Exception as e:
            print(f"[{i}/{len(pdf_urls)}] ❌ {pdf_url}: {str(e)[:60]}")
            failed += 1
        
        time.sleep(DELAY)
    
    print(f"\n{'='*60}")
    print(f"🎉 PDF DOWNLOAD DONE")
    print(f"   ✅ Downloaded: {downloaded}")
    print(f"   ❌ Failed:     {failed}")
    print(f"   📁 Location:   {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()