 
#STEP 1: Download Thapar's sitemap.xml
# Output: data/sitemap/thapar_sitemap.xml

import requests
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (StudentProject; contact: skolay_mca26@thapar.edu"
}

SITEMAP_URL = "https://www.thapar.edu/sitemap.xml"
OUTPUT_PATH = "data/sitemap/thapar_sitemap.xml"

def main():
    os.makedirs("data/sitemap", exist_ok=True)
    
    print(f"📥 Fetching: {SITEMAP_URL}")
    
    try:
        r = requests.get(
            SITEMAP_URL,
            headers=HEADERS,
            timeout=30,
            allow_redirects=True,   # handle HTTP → HTTPS redirect
        )
        r.raise_for_status()
        
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(r.text)
        
        print(f"✅ Saved sitemap: {OUTPUT_PATH}")
        print(f"   Size: {len(r.text):,} bytes")
        print(f"   Preview (first 300 chars):\n{r.text[:300]}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    main()