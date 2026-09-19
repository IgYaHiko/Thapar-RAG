"""
Map internal source identifiers → friendly display info with REAL URLs.
"""
import json
import os
from urllib.parse import quote_plus

PDF_URL_MAP = "data/pdf_url_map.json"
TITLES_PATH = "data/source_titles.json"


# Load PDF URL mapping
_pdf_urls = {}
if os.path.exists(PDF_URL_MAP):
    with open(PDF_URL_MAP, "r", encoding="utf-8") as f:
        _pdf_urls = json.load(f)

# Load friendly titles
_titles = {}
if os.path.exists(TITLES_PATH):
    with open(TITLES_PATH, "r", encoding="utf-8") as f:
        _titles = json.load(f)


def _extract_filename(source: str) -> str:
    """Get filename from 'MOM_SCC_2018.pdf#page=23' → 'MOM_SCC_2018.pdf'"""
    base = source.split("#page=")[0]
    return os.path.basename(base)


def friendly_source_name(source: str) -> str:
    """Human-readable name for a source."""
    page = None
    if "#page=" in source:
        _, page = source.split("#page=")
    
    filename = _extract_filename(source)
    
    if filename in _titles:
        name = _titles[filename]
    elif filename.endswith(".pdf"):
        name = filename.replace(".pdf", "").replace("_", " ").title()
    elif source.startswith("http"):
        name = "Thapar Website — " + source.rstrip("/").split("/")[-1].replace("-", " ").title()
    else:
        name = source
    
    if page:
        name += f", Page {page.strip()}"
    
    return name


def source_link(source: str) -> str | None:
    """
    Return REAL clickable URL:
    - Web pages: the URL itself
    - PDFs: looked up from pdf_url_map.json (real URL from scraping)
    - Fallback: None (so UI hides the button instead of showing a wrong link)
    """
    # Direct web URLs
    if source.startswith("http"):
        return source.split("#")[0]
    
    # PDFs: look up real URL
    filename = _extract_filename(source)
    
    # Try exact filename first
    if filename in _pdf_urls:
        return _pdf_urls[filename]
    
    # Try without .pdf
    base = filename.replace(".pdf", "")
    if base in _pdf_urls:
        return _pdf_urls[base]
    
    # Try safe version (underscores)
    import re
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)[:150]
    if safe in _pdf_urls:
        return _pdf_urls[safe]
    
    # No reliable URL — return None (don't show broken Google links)
    return None


def format_source_for_display(source: str) -> dict:
    return {
        "friendly_name": friendly_source_name(source),
        "link": source_link(source),   # may be None
        "raw": source,
    }