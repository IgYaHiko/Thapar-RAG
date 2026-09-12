
# STEP 2: Parse all URLs from sitemap XML
# Output: data/sitemap/all_urls.txt

import os
from bs4 import BeautifulSoup

SITEMAP_PATH = "data/sitemap/thapar_sitemap.xml"
OUTPUT_PATH = "data/sitemap/all_urls.txt"

def main():
    if not os.path.exists(SITEMAP_PATH):
        print(f"❌ Missing {SITEMAP_PATH}. Run 01_download_sitemap.py first.")
        return
    
    with open(SITEMAP_PATH, "r", encoding="utf-8") as f:
        xml_content = f.read()
    
    # Use XML parser (not HTML)
    soup = BeautifulSoup(xml_content, "xml")
    
    # Find all <loc> tags
    url_tags = soup.find_all("loc")
    urls = [tag.text.strip() for tag in url_tags]
    
    # Normalize: force HTTPS, strip trailing slashes
    urls = [u.replace("http://", "https://").rstrip("/") for u in urls]
    
    # Remove duplicates, keep order
    seen = set()
    unique_urls = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(unique_urls))
    
    print(f"🎯 Found {len(unique_urls)} unique URLs")
    print(f"✅ Saved to {OUTPUT_PATH}")
    print("\n📋 First 20 URLs:")
    for u in unique_urls[:20]:
        print(f"   {u}")

if __name__ == "__main__":
    main()