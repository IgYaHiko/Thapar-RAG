
#STEP 3: Filter URLs to only relevant ones for RAG
# Output: data/sitemap/filtered_urls.txt

import os

INPUT_PATH = "data/sitemap/all_urls.txt"
OUTPUT_PATH = "data/sitemap/filtered_urls.txt"

# Categories you WANT (useful for student queries)
KEEP_KEYWORDS = [
    "academic", "programme", "program", "admission",
    "rule", "regulation", "exam", "hostel", "library",
    "facility", "campus", "student", "fee", "calendar",
    "syllabus", "curriculum", "policy", "notice", "faq",
    "department", "school", "placement", "research",
    "about", "contact", "scholarship", "under", "post",
    "phd", "doctoral", "ug", "pg",
]

# Categories to SKIP (noise)
SKIP_KEYWORDS = [
    "login", "masterpath", "forgotpassword", "alumni",
    "gallery", "photo", "video", "news", "event",
    "tender", "advertisement", "recruit", "career",
    "webinar", "conference", "workshop",
]

def is_relevant(url: str) -> bool:
    u = url.lower()
    
    # Skip if contains skip keywords
    if any(s in u for s in SKIP_KEYWORDS):
        return False
    
    # Keep if contains keep keywords
    if any(k in u for k in KEEP_KEYWORDS):
        return True
    
    # Keep top-level pages (short paths)
    path = u.replace("https://www.thapar.edu", "").strip("/")
    if path.count("/") <= 1:
        return True
    
    return False

def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    
    filtered = [u for u in urls if is_relevant(u)]
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(filtered))
    
    print(f"📊 Total URLs:     {len(urls)}")
    print(f"🎯 Filtered URLs:  {len(filtered)}")
    print(f"✅ Saved to {OUTPUT_PATH}")
    print("\n📋 Sample of filtered URLs:")
    for u in filtered[:25]:
        print(f"   {u}")

if __name__ == "__main__":
    main()