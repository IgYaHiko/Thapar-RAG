
# STEP 4: Scrape each filtered URL and save text content

import os
import time
import json
import re
import requests
from bs4 import BeautifulSoup

INPUT_PATH = "data/sitemap/filtered_urls.txt"
OUTPUT_DIR = "data/scraped"
OUTPUT_JSONL = "data/scraped/pages.jsonl"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (StudentProject; contact: your.email@thapar.edu)"
}

DELAY = 1.5          # seconds between requests
TIMEOUT = 20         # seconds
MIN_TEXT_LENGTH = 200  # skip pages with less text


def clean_text(text: str) -> str:
    """Remove excess whitespace and menu noise."""
    # Collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def extract_content(html: str, url: str) -> dict:
    """Extract title and main content text from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove junk elements
    for tag in soup(["script", "style", "nav", "footer",
                     "header", "noscript", "iframe", "svg"]):
        tag.decompose()
    
    # Title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    
    # Try to find main content area
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id="content")
        or soup.find(class_="content")
        or soup.body
    )
    
    if main is None:
        return {"title": title, "text": ""}
    
    text = main.get_text(separator="\n", strip=True)
    text = clean_text(text)
    
    return {"title": title, "text": text}


def safe_filename(url: str) -> str:
    """Convert URL to a safe filename."""
    name = url.replace("https://", "").replace("http://", "")
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    return name[:150] + ".txt"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"🚀 Starting scrape of {len(urls)} URLs")
    print(f"   Delay: {DELAY}s between requests (please be patient)\n")
    
    results = []
    failed = []
    
    for i, url in enumerate(urls, 1):
        try:
            r = requests.get(
                url,
                headers=HEADERS,
                timeout=TIMEOUT,
                allow_redirects=True,
            )
            
            if r.status_code != 200:
                failed.append((url, f"HTTP {r.status_code}"))
                print(f"[{i}/{len(urls)}] ❌ {url} (HTTP {r.status_code})")
                time.sleep(DELAY)
                continue
            
            # Ensure proper encoding
            r.encoding = r.apparent_encoding or "utf-8"
            
            content = extract_content(r.text, url)
            
            if len(content["text"]) < MIN_TEXT_LENGTH:
                print(f"[{i}/{len(urls)}] ⚠️  Skipped (too short): {url}")
                time.sleep(DELAY)
                continue
            
            record = {
                "url": url,
                "title": content["title"],
                "text": content["text"],
                "length": len(content["text"]),
            }
            results.append(record)
            
            # Save individual file
            fname = safe_filename(url)
            with open(os.path.join(OUTPUT_DIR, fname), "w", encoding="utf-8") as f:
                f.write(f"SOURCE: {url}\n")
                f.write(f"TITLE: {content['title']}\n")
                f.write("-" * 60 + "\n\n")
                f.write(content["text"])
            
            print(f"[{i}/{len(urls)}] ✅ {url} ({len(content['text'])} chars)")
        
        except requests.exceptions.Timeout:
            failed.append((url, "timeout"))
            print(f"[{i}/{len(urls)}] ⏱️  Timeout: {url}")
        except Exception as e:
            failed.append((url, str(e)[:80]))
            print(f"[{i}/{len(urls)}] ❌ {url}: {str(e)[:80]}")
        
        time.sleep(DELAY)
    
    # Save combined JSONL
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for record in results:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    # Save failure log
    if failed:
        with open("data/scraped/failed.txt", "w", encoding="utf-8") as f:
            for url, err in failed:
                f.write(f"{url}\t{err}\n")
    
    print(f"\n{'='*60}")
    print(f"🎉 SCRAPING DONE")
    print(f"   ✅ Success: {len(results)}")
    print(f"   ❌ Failed:  {len(failed)}")
    print(f"   📄 Output:  {OUTPUT_JSONL}")
    if failed:
        print(f"   📋 Failures: data/scraped/failed.txt")


if __name__ == "__main__":
    main()