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


def fetch_page_chunks(url: str, max_chars: int = 1500) -> str:
    """
    Phase 3 — Sliding-window page reader.
    Fetches a URL, strips boilerplate/JS, returns clean readable text.
    Skips pages that are clearly JS-rendered with no real content.
    """
    # Skip sites known to return JS blobs or block scrapers
    SKIP_DOMAINS = ["wikipedia.org", "britannica.com", "jpost.com", "timesofisrael.com"]
    if any(d in url for d in SKIP_DOMAINS):
        return ""  # rely on the search snippet instead
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, timeout=8, headers=headers)
        if resp.status_code != 200:
            return ""
        raw = resp.text
        # Remove script/style/nav/footer blocks entirely
        raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
        raw = re.sub(r"<style[^>]*>.*?</style>",   " ", raw, flags=re.DOTALL | re.IGNORECASE)
        raw = re.sub(r"<nav[^>]*>.*?</nav>",        " ", raw, flags=re.DOTALL | re.IGNORECASE)
        raw = re.sub(r"<footer[^>]*>.*?</footer>",  " ", raw, flags=re.DOTALL | re.IGNORECASE)
        # Strip remaining HTML tags
        text = re.sub(r"<[^>]+>", " ", raw)
        # Clean whitespace and JSON-like noise
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r'[{}\[\]\"\\'  + r"']", "", text)
        # Discard if it looks like raw JS (SPA sites)
        if text.count("function(") > 3 or text.count("var ") > 5 or len(text) < 100:
            return ""
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
    """Formats search results into a commanding context block the LLM MUST use."""
    if not results:
        return ""
    block  = "\n\n<<<MANDATORY WEB SEARCH RESULTS — YOU MUST USE THESE>>>\n"
    block += "RULE: Your answer MUST be built entirely from the sources below.\n"
    block += "RULE: You MUST cite every fact with [1], [2], etc.\n"
    block += "RULE: Do NOT say 'I was unable to find' — the results are right here.\n"
    block += "RULE: Do NOT suggest the user check other websites — answer directly.\n"
    block += "=" * 60 + "\n"
    for i, r in enumerate(results, 1):
        block += f"\n[{i}] TITLE: {r['title']}\n"
        block += f"    URL: {r['url']}\n"
        block += f"    CONTENT: {r['snippet']}\n"
        block += "-" * 40 + "\n"
    block += "\n<<<END OF WEB RESULTS — NOW ANSWER USING ONLY THE ABOVE>>>\n"
    return block


# New helper to provide short aggregated web context used in some tabs
def get_web_context(query: str, max_results: int = 4) -> str:
    """Return a short aggregated web-context string for a query.

    This uses the existing chatgpt_style_search pipeline and joins title/snippet/url
    lines for easy consumption by downstream prompts. If the search fails, returns
    an empty string.
    """
    try:
        search_res = chatgpt_style_search(query, max_results_per_query=max_results)
        lines = []
        for i, r in enumerate(search_res.get("results", []), 1):
            title = r.get("title", "No Title")
            snippet = r.get("snippet", "")
            url = r.get("url", "#")
            lines.append(f"[{i}] {title} — {snippet} ({url})")
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"get_web_context failed: {e}")
        return ""


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


def call_groq(user_prompt, model="llama-3.3-70b-versatile", temperature=0.2, style_hint=""):
    if not GROQ_KEY:
        return "Error: Missing GROQ_API_KEY in Streamlit secrets."
    client = Groq(api_key=GROQ_KEY)
    today = datetime.now().strftime("%B %d, %Y")
    system_message = (
        f"You are StudyAI Master, an AI assistant. Today is {today}.\n\n"
        "CRITICAL RULES - FOLLOW EXACTLY:\n"
        "1. When the prompt contains MANDATORY WEB SEARCH RESULTS, read every numbered source "
        "carefully and build your answer from that content.\n"
        "2. CITATIONS: Only cite [1] [2] [3] for sources actually listed and numbered in the "
        "web results. NEVER invent citations that are not in the provided sources. "
        "Hallucinated citations like [1] Iran hostage crisis Wikipedia are strictly forbidden.\n"
        "3. If web snippets are thin or mostly metadata, say: The search found these pages but "
        "content was limited. Based on what was retrieved: ... then summarise what is there, "
        "then add relevant context from training knowledge clearly labelled as "
        "From training knowledge:.\n"
        "4. NEVER say I was unable to find information when sources exist - always extract "
        "something useful from them.\n"
        "5. NEVER list websites for the user to check themselves - YOU answer directly.\n"
        "6. If a query asks about a specific event and web results do not confirm it happened, "
        "say clearly: Based on current web results, this event is not confirmed. Here is what "
        "is known: then give accurate context.\n"
        "7. Only use pure training knowledge if there are truly zero web results.\n\n"
        f"Style: {style_hint}"
        f"and all block math equations in double $$ symbols. Do NOT use \\[ or \\].\n"
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
# TAB 2: PREDICTOR
with tab2:
    st.subheader("2026 Topic Predictor")

    bp_search = st.toggle(
        "Search latest 2026 CBSE syllabus?",
        value=True,
        key="bp_search"
    )

    subject = st.text_input("Subject (e.g. Science):")

    if st.button("Predict High-Weightage Topics"):
        if not subject.strip():
            st.error("Please enter a subject.")
        else:
            with st.spinner("Analyzing..."):
                query = f"Class 10 {subject} 2026 CBSE board exam weightage"

                context = (
                    f"2026 NEWS: {get_web_context(query, 5)}\n\n"
                    if bp_search else ""
                )

                style = st.session_state.get(
                    "response_style",
                    "Balanced"
                )

                style_config = get_response_style_config(style)

                try:
                    res = call_groq(
                        f"{context}Predict 10 high-probability topics for {subject} 2026 CBSE boards.",
                        model="llama-3.3-70b-versatile",
                        temperature=style_config["temperature"],
                        style_hint=style_config["hint"]
                    )

                    st.markdown(
                        f'<div class="answer-box">{res}</div>',
                        unsafe_allow_html=True
                    )

                except Exception as e:
                    st.error(f"Error: {e}")
# TAB 3: PYQ VAULT
with tab3:
    st.subheader("PYQ Vault")
    pyq_sub = st.selectbox("Subject:", ["Math", "Science", "SST", "English"], key="pyq_v")
    chapter = st.text_input("Chapter Name:", key="pyq_c")
    if st.button("Fetch PYQs"):
        with st.spinner("Fetching..."):
            # Get style config
            style_config = get_response_style_config(st.session_state.response_style)
            
            res = call_groq(f"List Last 10 Years PYQs for Class 10 CBSE {pyq_sub}, Chapter: {chapter}.", temperature=style_config["temperature"], style_hint=style_config["hint"])
            st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)

# TAB 4: SAMPLE GEN
with tab4:
    st.subheader("Sample Question Generator")
    sq_sub = st.selectbox("Subject:", ["Math", "Science", "SST", "English"], key="sq_v")
    sq_topic = st.text_input("Topic:", key="sq_t")
    if st.button("Generate Set"):
        with st.spinner("Crafting..."):
            # Get style config
            style_config = get_response_style_config(st.session_state.response_style)
            topic = sq_topic.strip()
            if not topic:
                st.error("Please enter a topic.")
            else:
                try:
                    prompt = (
                        f"Generate 10 sample questions for Class 10 {sq_sub}, Topic: {topic}. "
                        "For each question provide: (1) question text, (2) marks/difficulty level, and "
                        "(3) a brief answer. Number them."
                    )
                    res = call_groq(prompt, temperature=style_config["temperature"], style_hint=style_config["hint"])
                    st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")


# Footer - Created by Nissan Gain in bold
st.markdown("**Created by Nissan Gain**", unsafe_allow_html=True)
