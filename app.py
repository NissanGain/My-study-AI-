from datetime import datetime
import streamlit as st
from groq import Groq
import logging
import requests
import json
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- 1. SETUP & SECRETS ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY")

st.set_page_config(page_title="StudyAI Master", page_icon="🎯", layout="wide")

# --- 2. STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600&display=swap');

    .answer-box {
        background-color: rgba(128, 128, 128, 0.1);
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #4A90E2;
        margin-bottom: 10px;
        color: inherit;
    }
    .stButton>button { border-radius: 10px; width: 100%; font-weight: bold; }
    .footer { text-align: center; padding: 20px; font-size: 1.1em; opacity: 0.8; }
    .style-selector {
        background-color: rgba(74, 144, 226, 0.1);
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 15px;
    }

    /* ── ChatGPT-style search UI ── */
    .search-status-bar {
        display: flex;
        align-items: center;
        gap: 10px;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 10px 16px;
        margin: 8px 0;
        font-size: 0.88em;
        color: #94a3b8;
        font-family: 'Space Grotesk', monospace;
    }
    .search-status-bar .step-done  { color: #4ade80; }
    .search-status-bar .step-active { color: #facc15; }

    .search-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(74,144,226,0.12);
        border: 1px solid rgba(74,144,226,0.35);
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 0.78em;
        color: #60a5fa;
        margin: 3px 2px;
        font-family: monospace;
    }

    .source-panel {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 14px 18px;
        margin: 10px 0 4px 0;
    }
    .source-panel-header {
        font-size: 0.82em;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 10px;
        font-weight: 600;
    }
    .source-card {
        display: flex;
        gap: 10px;
        align-items: flex-start;
        background: #1e293b;
        border-radius: 8px;
        padding: 10px 12px;
        margin: 6px 0;
        border-left: 3px solid #3b82f6;
        transition: background 0.2s;
    }
    .source-number {
        background: #3b82f6;
        color: #fff;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        min-width: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.72em;
        font-weight: 700;
        margin-top: 2px;
    }
    .source-title {
        font-weight: 600;
        color: #e2e8f0;
        font-size: 0.88em;
        margin-bottom: 3px;
    }
    .source-snippet {
        color: #94a3b8;
        font-size: 0.80em;
        line-height: 1.45;
        margin-bottom: 4px;
    }
    .source-url {
        color: #4ade80;
        font-size: 0.74em;
        word-break: break-all;
        text-decoration: none;
    }

    .citation-inline {
        display: inline-flex;
        align-items: center;
        background: rgba(59,130,246,0.15);
        border: 1px solid rgba(59,130,246,0.4);
        border-radius: 4px;
        padding: 0px 5px;
        font-size: 0.75em;
        color: #93c5fd;
        margin: 0 2px;
        vertical-align: middle;
        cursor: pointer;
        font-weight: 600;
    }

    .query-rewrite-box {
        background: rgba(250,204,21,0.07);
        border: 1px solid rgba(250,204,21,0.25);
        border-radius: 8px;
        padding: 8px 14px;
        margin: 6px 0;
        font-size: 0.83em;
        color: #fde68a;
        font-family: monospace;
    }
    </style>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# 3. CHATGPT-STYLE SEARCH ENGINE
# ═══════════════════════════════════════════════════════════════

def rewrite_query_for_search(user_question: str, model="llama-3.1-8b-instant") -> list[str]:
    """
    Phase 1 — Query rewriting (like ChatGPT does).
    Turns a conversational question into 1-3 optimised search queries.
    Returns a list of query strings.
    """
    if not GROQ_KEY:
        return [user_question]
    try:
        client = Groq(api_key=GROQ_KEY)
        today = datetime.now().strftime("%B %Y")
        system = (
            "You are a search query optimizer. "
            "Given a user question, output 1 to 3 short, targeted search-engine queries "
            "(like you would type in Google) that together cover the question. "
            f"Today is {today}. "
            "Respond ONLY with a JSON array of strings. No explanation. Example: "
            '["query one", "query two"]'
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_question}
            ],
            temperature=0.1,
            max_tokens=200
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"```[a-z]*", "", raw).strip("` \n")
        queries = json.loads(raw)
        if isinstance(queries, list) and queries:
            return [str(q) for q in queries[:3]]
    except Exception as e:
        logger.warning(f"Query rewrite failed: {e}")
    return [user_question]


def search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    """DuckDuckGo search backend."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS(timeout=10) as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title":   r.get("title", "No Title"),
                    "snippet": r.get("body", r.get("snippet", "")),
                    "url":     r.get("href", "#"),
                    "source":  "DuckDuckGo",
                    "query":   query,
                })
        return results
    except Exception as e:
        logger.error(f"DuckDuckGo error: {e}")
        return []


def search_searx(query: str, max_results: int = 5) -> list[dict]:
    """Searx fallback backend."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(
            "https://searx.be/search",
            params={"q": query, "format": "json", "pageno": 1},
            timeout=10, headers=headers
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for r in data.get("results", [])[:max_results]:
                results.append({
                    "title":   r.get("title", "No Title"),
                    "snippet": r.get("content", r.get("summary", "")),
                    "url":     r.get("url", "#"),
                    "source":  "Searx",
                    "query":   query,
                })
            return results
    except Exception as e:
        logger.error(f"Searx error: {e}")
    return []


def fetch_page_chunks(url: str, max_chars: int = 1200) -> str:
    """
    Phase 3 — Sliding-window page reader (like ChatGPT does).
    Fetches a URL and returns plain-text chunks up to max_chars.
    Falls back silently on error.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, timeout=8, headers=headers)
        if resp.status_code != 200:
            return ""
        # Strip HTML tags → plain text
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        # Return first max_chars (the most important content is usually at top)
        return text[:max_chars]
    except Exception:
        return ""


def chatgpt_style_search(user_question: str, max_results_per_query: int = 4) -> dict:
    """
    Full ChatGPT-style search pipeline:
      1. Rewrite query → optimised search terms
      2. Search each term (DuckDuckGo → Searx fallback)
      3. Deduplicate results
      4. Fetch page chunks (sliding window)
      5. Return structured result for AI + UI
    """
    # Phase 1: Query rewriting
    queries = rewrite_query_for_search(user_question)
    logger.info(f"Rewritten queries: {queries}")

    all_results = []
    seen_urls = set()

    for q in queries:
        # Phase 2a: DuckDuckGo
        results = search_duckduckgo(q, max_results=max_results_per_query)
        if not results:
            # Phase 2b: Searx fallback
            results = search_searx(q, max_results=max_results_per_query)

        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_results.append(r)

    # Phase 3: Fetch page content chunks for top results
    for r in all_results[:6]:
        if r["url"] != "#":
            chunk = fetch_page_chunks(r["url"])
            if chunk:
                # Prefer page chunk over snippet (richer content)
                r["snippet"] = chunk[:600] if len(chunk) > len(r["snippet"]) else r["snippet"]

    return {
        "queries":  queries,
        "results":  all_results[:8],   # cap at 8 deduplicated sources
    }


# ═══════════════════════════════════════════════════════════════
# 4. UI HELPERS
# ═══════════════════════════════════════════════════════════════

def render_search_status(queries: list[str], result_count: int):
    """Shows the animated status bar (phases done)."""
    query_pills = " ".join(
        f'<span class="search-pill">🔍 {q}</span>' for q in queries
    )
    st.markdown(
        f'<div class="search-status-bar">'
        f'<span class="step-done">✓ Query rewritten</span> · '
        f'<span class="step-done">✓ Web searched</span> · '
        f'<span class="step-done">✓ Pages read</span> · '
        f'<span class="step-done">✓ {result_count} sources found</span>'
        f'</div>'
        f'<div style="margin:4px 0 8px 0">{query_pills}</div>',
        unsafe_allow_html=True
    )


def render_sources_panel(results: list[dict]):
    """Renders the ChatGPT-style collapsible sources panel."""
    if not results:
        return
    with st.expander(f"📄 Sources ({len(results)})", expanded=False):
        st.markdown('<div class="source-panel">', unsafe_allow_html=True)
        st.markdown('<div class="source-panel-header">Web Sources</div>', unsafe_allow_html=True)
        for i, r in enumerate(results, 1):
            st.markdown(
                f'<div class="source-card">'
                f'  <div class="source-number">{i}</div>'
                f'  <div>'
                f'    <div class="source-title">{r["title"]}</div>'
                f'    <div class="source-snippet">{r["snippet"][:220]}…</div>'
                f'    <a class="source-url" href="{r["url"]}" target="_blank">{r["url"][:70]}</a>'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)


def format_results_for_ai(results: list[dict]) -> str:
    """Formats search results into a clean context block for the LLM."""
    if not results:
        return ""
    block = "\n\n[LIVE WEB SEARCH CONTEXT]\n"
    block += "Use the sources below. Cite them inline as [1], [2], etc.\n"
    block += "=" * 60 + "\n"
    for i, r in enumerate(results, 1):
        block += f"\n[{i}] {r['title']}\n"
        block += f"URL: {r['url']}\n"
        block += f"Content: {r['snippet']}\n"
        block += "-" * 40 + "\n"
    return block


# ═══════════════════════════════════════════════════════════════
# 5. GROQ CALL
# ═══════════════════════════════════════════════════════════════

def get_response_style_config(style):
    styles = {
        "📚 Factual":  {"temperature": 0.1, "hint": "Be precise, data-driven, and focus on facts."},
        "⚖️ Balanced": {"temperature": 0.5, "hint": "Provide balanced, clear explanations with examples."},
        "✨ Creative": {"temperature": 0.8, "hint": "Be creative, use analogies, and make learning engaging."},
        "🎨 Poetic":   {"temperature": 1.0, "hint": "Use poetic language, metaphors, and storytelling."},
    }
    return styles.get(style, styles["⚖️ Balanced"])


def call_groq(user_prompt, model="llama-3.1-8b-instant", temperature=0.2, style_hint=""):
    if not GROQ_KEY:
        return "Error: Missing GROQ_API_KEY in Streamlit secrets."
    client = Groq(api_key=GROQ_KEY)
    system_message = (
        "You are 'StudyAI Master' created by Nissan Gain. "
        f"Today is {datetime.now().strftime('%B %d, %Y')}. "
        "You have access to REAL-TIME web search results provided in the prompt. "
        "When web results are provided, synthesise them into a clear answer. "
        "Always cite sources inline using [1], [2], etc. corresponding to the numbered sources. "
        "If no web results are provided, answer from your training knowledge and say so. "
        f"{style_hint}"
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user",   "content": user_prompt}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Connection Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════
# 6. MAIN INTERFACE
# ═══════════════════════════════════════════════════════════════

st.title("🎯 StudyAI Master")
st.caption("2026 Board Exam Hub · ChatGPT-Style Web Search · Powered by Groq")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "response_style" not in st.session_state:
    st.session_state.response_style = "⚖️ Balanced"

# Global style selector
st.markdown('<div class="style-selector">', unsafe_allow_html=True)
col1, col2 = st.columns([2, 3])
with col1:
    st.markdown("**🎯 Response Style:**")
with col2:
    st.session_state.response_style = st.radio(
        "Choose AI behavior",
        ["📚 Factual", "⚖️ Balanced", "✨ Creative", "🎨 Poetic"],
        horizontal=True,
        label_visibility="collapsed",
        key="response_style_selector"
    )
st.markdown('</div>', unsafe_allow_html=True)

# Debug panel
with st.expander("🔧 Debug & Search Test"):
    test_query = st.text_input("Test query:", value="2026 CBSE Science syllabus", key="manual_test")
    if st.button("▶ Run Full Search Pipeline"):
        with st.spinner("Running ChatGPT-style search…"):
            res = chatgpt_style_search(test_query, max_results_per_query=4)
        render_search_status(res["queries"], len(res["results"]))
        render_sources_panel(res["results"])

tab1, tab2, tab3, tab4 = st.tabs(["🚀 Doubt Solver", "📈 Predictor", "📜 PYQ Vault", "📝 Sample Gen"])

# ── TAB 1: DOUBT SOLVER ──────────────────────────────────────
with tab1:
    st.subheader("Instant Doubt Solver — ChatGPT-Style Search")

    col_search, col_num = st.columns([3, 1])
    with col_search:
        ds_search = st.toggle("🌐 Search Web (ChatGPT Style)?", key="ds_search", value=True)
    with col_num:
        num_results = st.slider("Results per query:", 3, 8, 4, key="ds_results")

    # Chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask any doubt… (web search enabled by default)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("🔍 Searching the web…"):
            web_context = ""
            search_data = None

            if ds_search:
                # Full ChatGPT-style pipeline
                search_data = chatgpt_style_search(prompt, max_results_per_query=num_results)

                if search_data["results"]:
                    # Show status bar + rewritten queries
                    render_search_status(search_data["queries"], len(search_data["results"]))
                    # Show sources panel (collapsible, like ChatGPT)
                    render_sources_panel(search_data["results"])
                    web_context = format_results_for_ai(search_data["results"])
                else:
                    st.info("⚠️ Web search returned no results — using knowledge base.")

        with st.spinner("🤖 Generating answer…"):
            # Build prompt with history + web context
            history_text = "\n".join(
                [f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]]
            )
            full_query = (
                f"{web_context}\n\n"
                f"Chat History:\n{history_text}\n\n"
                f"Current Question: {prompt}"
            )
            style_config = get_response_style_config(st.session_state.response_style)
            response = call_groq(full_query, temperature=style_config["temperature"], style_hint=style_config["hint"])

            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

# ── TAB 2: PREDICTOR ─────────────────────────────────────────
with tab2:
    st.subheader("2026 Topic Predictor")
    bp_search = st.toggle("🌐 Search latest CBSE info?", value=True, key="bp_search")
    subject = st.text_input("Subject (e.g. Science):")

    if st.button("Predict High-Weightage Topics", use_container_width=True):
        with st.spinner("🔍 Analysing with web data…"):
            web_context = ""
            if bp_search and subject:
                search_data = chatgpt_style_search(
                    f"Class 10 {subject} 2026 CBSE board exam high weightage important topics",
                    max_results_per_query=4
                )
                if search_data["results"]:
                    render_search_status(search_data["queries"], len(search_data["results"]))
                    render_sources_panel(search_data["results"])
                    web_context = format_results_for_ai(search_data["results"])

            style_config = get_response_style_config(st.session_state.response_style)
            res = call_groq(
                f"{web_context}\n\nPredict 10 high-probability topics for Class 10 CBSE {subject} 2026.",
                model="llama-3.3-70b-versatile",
                temperature=style_config["temperature"],
                style_hint=style_config["hint"]
            )
            st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)

# ── TAB 3: PYQ VAULT ─────────────────────────────────────────
with tab3:
    st.subheader("PYQ Vault")
    pyq_sub = st.selectbox("Subject:", ["Math", "Science", "SST", "English"], key="pyq_v")
    chapter  = st.text_input("Chapter Name:", key="pyq_c")

    if st.button("Fetch PYQs", use_container_width=True):
        with st.spinner("Fetching…"):
            style_config = get_response_style_config(st.session_state.response_style)
            res = call_groq(
                f"List last 10 years PYQs for Class 10 CBSE {pyq_sub}, Chapter: {chapter}.",
                temperature=style_config["temperature"],
                style_hint=style_config["hint"]
            )
            st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)

# ── TAB 4: SAMPLE GEN ────────────────────────────────────────
with tab4:
    st.subheader("Sample Question Generator")
    sq_sub   = st.selectbox("Subject:", ["Math", "Science", "SST", "English"], key="sq_v")
    
