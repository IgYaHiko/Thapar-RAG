"""
STAGE 5: Streamlit chat UI
Run from project root: streamlit run src/06_app.py
"""
import sys
import os
import warnings
from pathlib import Path

# ---- Project root setup (MUST come before local imports) ----
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)
warnings.filterwarnings("ignore")   # hide torch/gemini deprecation noise

# ---- .env loading ----
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# ---- Local imports ----
import streamlit as st
from src.rag_chain_utils import ask


# ---- Page config ----
st.set_page_config(
    page_title="SmartCampus Assistant",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 SmartCampus Assistant")
st.caption("Ask about attendance, exams, hostel, campus, fees — anything!")


# ---- Sidebar ----
with st.sidebar:
    st.header("ℹ️ About")
    st.write(
        "This assistant uses **Retrieval-Augmented Generation (RAG)** "
        "to answer questions about Thapar Institute using official "
        "public documents."
    )
    st.divider()
    st.write("**Data sources:**")
    st.write("- thapar.edu (public pages)")
    st.write("- Official PDFs (handbooks, rules)")
    st.divider()
    st.caption(
        "⚠️ Answers are based on scraped documents. "
        "Always verify critical info with the admin office."
    )
    
    # Optional: clear chat button
    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()


# ---- Helper: render sources ----
def render_sources(sources: list):
    if not sources:
        st.caption("No sources available.")
        return
    
    for s in sources:
        name = s.get("friendly_name") or s.get("raw") or "Unknown source"
        link = s.get("link") or s.get("url")
        score = s.get("score", 0.0)
        preview = s.get("preview", "")
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"**{name}**")
            st.caption(f"Relevance: {score:.0%}")
            if preview:
                with st.popover("📄 Preview"):
                    st.write(preview + "...")
        
        with col2:
            if link and link.startswith("http"):
                st.link_button("Open ↗", link, use_container_width=True)
            else:
                st.caption("_Source offline_")
        
        st.divider()


# ---- Chat history ----
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # Use markdown for assistant, plain for user
        if msg["role"] == "assistant":
            st.markdown(msg["content"])
        else:
            st.write(msg["content"])
        
        if msg.get("sources"):
            with st.expander(f"📚 Sources ({len(msg['sources'])})", expanded=False):
                render_sources(msg["sources"])


# ---- Chat input ----
query = st.chat_input("Ask a question...")

if query:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)
    
    # Generate answer
    with st.chat_message("assistant"):
        with st.spinner("Searching university documents..."):
            try:
                result = ask(query)
                answer = result["answer"]
                sources = result["sources"]
            except Exception as e:
                answer = f"⚠️ Error: `{type(e).__name__}: {e}`"
                sources = []
        
        # ✅ Single render for answer (markdown)
        st.markdown(answer)
        
        # ✅ Single render for sources
        if sources:
            with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
                render_sources(sources)
    
    # Save to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })