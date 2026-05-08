from datetime import datetime
import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS
import logging
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- 1. SETUP & SECRETS ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY")

st.set_page_config(page_title="StudyAI Master", page_icon="🎯", layout="wide")

# --- 2. THEME-FRIENDLY STYLING ---
st.markdown("""
    <style>
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
    .source-card {
        background-color: rgba(100, 150, 255, 0.1);
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 4px solid #6496FF;
        font-size: 0.9em;
    }
    .source-title {
        font-weight: bold;
        color: #0066CC;
        word-break: break-word;
    }
    .web-results-header {
        background: linear-gradient(90deg, #4A90E2, #357ABD);
        color: white;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
        font-weight: bold;
    }
    .debug-panel {
        background-color: rgba(255, 193, 7, 0.1);
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #FFC107;
        font-family: monospace;
        font-size: 0.85em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def test_duckduckgo_connection():
    """Test if DuckDuckGo API is working"""
    try:
        logger.info("🧪 Testing DuckDuckGo connection...")
        with DDGS() as ddgs:
            results = list(ddgs.text("python programming", max_results=1))
            if results:
                logger.info(f"✅ Connection test successful! Got result: {results[0]}")
                return True, "✅ Connection successful!"
            else:
                logger.warning("⚠️ Connection test returned empty results")
                return False, "⚠️ No results from test query"
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"❌ Connection test failed: {error_msg}")
        return False, f"❌ {error_msg}"

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_web_search_results(query, max_results=5):
    """Fetch web search results from DuckDuckGo with detailed debugging"""
    try:
        logger.info(f"🔍 Starting web search for: '{query}'")
        print(f"[SEARCH] Query: {query}")
        
        results = []
        with DDGS() as ddgs:
            logger.info("📡 Connecting to DuckDuckGo...")
            for idx, result in enumerate(ddgs.text(query, max_results=max_results)):
                try:
                    logger.debug(f"Result {idx}: {json.dumps(result, default=str)[:200]}")
                    processed = {
                        'title': result.get('title', 'No Title'),
                        'snippet': result.get('body', result.get('snippet', '')),
                        'url': result.get('href', '#'),
                        'source': result.get('source', 'Unknown')
                    }
                    results.append(processed)
                except Exception as e:
                    logger.warning(f"Error processing result {idx}: {e}")
                    continue
        
        logger.info(f"✅ Retrieved {len(results)} results")
        return results if results else None
        
    except ImportError as e:
        error_msg = f"Import Error: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"❌ Web search error: {error_msg}")
        print(f"[ERROR] {error_msg}")
        return None

def format_web_results_for_ai(results):
    """Format web results for AI to use in response"""
    if not results:
        return ""
    
    formatted = "\n\n📰 LIVE WEB SEARCH RESULTS:\n"
    formatted += "="*60 + "\n"
    
    for i, result in enumerate(results, 1):
        formatted += f"\n[Source {i}]\n"
        formatted += f"Title: {result['title']}\n"
        formatted += f"Content: {result['snippet']}\n"
        formatted += f"URL: {result['url']}\n"
        formatted += "-"*60 + "\n"
    
    return formatted

def display_web_results_ui(results):
    """Display web search results in Streamlit UI (ChatGPT style)"""
    if not results:
        st.warning("⚠️ No web results found for this query")
        return
    
    with st.expander(f"📰 Web Search Results ({len(results)} sources)", expanded=False):
        for i, result in enumerate(results, 1):
            st.markdown(f'<div class="source-card">', unsafe_allow_html=True)
            st.markdown(f'<span class="source-title">📌 Source {i}: {result["title"]}</span>', unsafe_allow_html=True)
            st.markdown(f'**Content:** {result["snippet"]}')
            st.markdown(f'🔗 [Read Full Article]({result["url"]})')
            st.markdown('</div>', unsafe_allow_html=True)

def get_response_style_config(style):
    """Returns temperature and style hint based on selected style"""
    styles = {
        "📚 Factual": {
            "temperature": 0.1,
            "hint": "Be precise, data-driven, and focus on facts."
        },
        "⚖️ Balanced": {
            "temperature": 0.5,
            "hint": "Provide balanced, clear explanations with examples."
        },
        "✨ Creative": {
            "temperature": 0.8,
            "hint": "Be creative, use analogies, and make learning engaging."
        },
        "🎨 Poetic": {
            "temperature": 1.0,
            "hint": "Use poetic language, metaphors, and storytelling."
        }
    }
    return styles.get(style, styles["⚖️ Balanced"])

def call_groq(user_prompt, model="llama-3.1-8b-instant", temperature=0.2, style_hint=""):
    """Call Groq API with web context included"""
    if not GROQ_KEY:
        return "Error: Missing API Key in Secrets."
    client = Groq(api_key=GROQ_KEY)
    
    system_message = (
        "You are 'StudyAI Master' created by Nissan Gain. Today is May 8, 2026. "
        "You have access to REAL-TIME web search data provided in the prompt. "
        "Use the web search results to provide accurate, current information. "
        "Cite sources when using web data (e.g., 'According to Source 1...', 'From the latest web data...'). "
        f"{style_hint}"
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Connection Error: {str(e)}"

# --- 4. MAIN INTERFACE ---
st.title("🎯 StudyAI Master")
st.caption("2026 Board Exam Hub | ChatGPT-Style Web Search | Powered by Groq")

# Initialize Chat Memory & Response Style
if "messages" not in st.session_state:
    st.session_state.messages = []
if "response_style" not in st.session_state:
    st.session_state.response_style = "⚖️ Balanced"

# Global Response Style Selector
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

# DEBUG PANEL
with st.expander("🔧 Debug Web Search"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧪 Test Connection"):
            success, msg = test_duckduckgo_connection()
            if success:
                st.success(msg)
            else:
                st.error(msg)
    
    with col2:
        if st.button("🔍 Test Search"):
            st.info("Testing search for 'python programming'...")
            results = get_web_search_results("python programming", max_results=3)
            if results:
                st.success(f"✅ Got {len(results)} results")
                for i, r in enumerate(results, 1):
                    st.write(f"{i}. {r['title'][:50]}...")
            else:
                st.error("❌ Search returned no results")
    
    with col3:
        if st.button("📋 Manual Test"):
            test_query = st.text_input("Enter search query:", "2026 Iran news", key="test_query")
            if test_query:
                st.info(f"Searching for: {test_query}")
                results = get_web_search_results(test_query, max_results=5)
                if results:
                    st.success(f"✅ Found {len(results)} results")
                    display_web_results_ui(results)
                else:
                    st.error("❌ No results found")

tab1, tab2, tab3, tab4 = st.tabs(["🚀 Doubt Solver", "📈 Predictor", "📜 PYQ Vault", "📝 Sample Gen"])

# TAB 1: CONVERSATIONAL DOUBT SOLVER (ChatGPT Style)
with tab1:
    st.subheader("Instant Doubt Solver - ChatGPT Style Search")
    
    col_search, col_num = st.columns([3, 1])
    with col_search:
        ds_search = st.toggle("🌐 Search Web (ChatGPT Style)?", key="ds_search", value=True)
    with col_num:
        num_results = st.slider("Results:", 3, 10, 5, key="ds_results")
    
    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask any doubt... (web search enabled by default)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("🔍 Searching web & thinking..."):
            web_data = ""
            web_results = None
            
            if ds_search:
                # Perform web search
                web_results = get_web_search_results(prompt, max_results=num_results)
                
                if web_results:
                    st.markdown('<div class="web-results-header">✅ Web Search Complete - Using Live Data</div>', unsafe_allow_html=True)
                    display_web_results_ui(web_results)
                    web_data = format_web_results_for_ai(web_results)
                else:
                    st.info("⚠️ Web search returned no results, using knowledge base")
            
            # Build full prompt
            history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
            full_query = f"{web_data}\n\nChat History:\n{history}\n\nCurrent Question: {prompt}"
            
            # Get style config
            style_config = get_response_style_config(st.session_state.response_style)
            
            # Get AI response
            response = call_groq(full_query, temperature=style_config["temperature"], style_hint=style_config["hint"])
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            with st.chat_message("assistant"):
                st.markdown(response)

# TAB 2: PREDICTOR (With Web Search)
with tab2:
    st.subheader("2026 Topic Predictor")
    bp_search = st.toggle("🌐 Search latest CBSE info?", value=True, key="bp_search")
    subject = st.text_input("Subject (e.g. Science):")
    
    if st.button("Predict High-Weightage Topics", use_container_width=True):
        with st.spinner("🔍 Analyzing with web data..."):
            query = f"Class 10 {subject} 2026 CBSE board exam high weightage topics"
            web_data = ""
            
            if bp_search:
                web_results = get_web_search_results(query, max_results=5)
                if web_results:
                    st.markdown('<div class="web-results-header">📰 Using Latest CBSE Data</div>', unsafe_allow_html=True)
                    display_web_results_ui(web_results)
                    web_data = format_web_results_for_ai(web_results)
            
            style_config = get_response_style_config(st.session_state.response_style)
            
            res = call_groq(
                f"{web_data}\n\nPredicting 10 high-probability topics for Class 10 CBSE {subject} 2026.",
                model="llama-3.3-70b-versatile",
                temperature=style_config["temperature"],
                style_hint=style_config["hint"]
            )
            st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)

# TAB 3: PYQ VAULT
with tab3:
    st.subheader("PYQ Vault")
    pyq_sub = st.selectbox("Subject:", ["Math", "Science", "SST", "English"], key="pyq_v")
    chapter = st.text_input("Chapter Name:", key="pyq_c")
    
    if st.button("Fetch PYQs", use_container_width=True):
        with st.spinner("Fetching..."):
            style_config = get_response_style_config(st.session_state.response_style)
            
            res = call_groq(
                f"List Last 10 Years PYQs for Class 10 CBSE {pyq_sub}, Chapter: {chapter}.",
                temperature=style_config["temperature"],
                style_hint=style_config["hint"]
            )
            st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)

# TAB 4: SAMPLE GEN
with tab4:
    st.subheader("Sample Question Generator")
    sq_sub = st.selectbox("Subject:", ["Math", "Science", "SST", "English"], key="sq_v")
    sq_topic = st.text_input("Topic:", key="sq_t")
    
    if st.button("Generate Set", use_container_width=True):
        with st.spinner("Crafting..."):
            style_config = get_response_style_config(st.session_state.response_style)
            
            res = call_groq(
                f"Generate 20 NCERT-style practice questions based on CBSE class 10 for {sq_sub} on {sq_topic}.",
                model="llama-3.3-70b-versatile",
                temperature=style_config["temperature"],
                style_hint=style_config["hint"]
            )
            st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)

# --- 5. FOOTER ---
st.divider()
st.markdown('<div class="footer">Created by <b>Nissan Gain</b> | ChatGPT-Style Web Search | 2026 Edition</div>', unsafe_allow_html=True)
