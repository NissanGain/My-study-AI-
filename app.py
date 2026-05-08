from datetime import datetime
import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS
import logging

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
    .success-box {
        background-color: rgba(76, 175, 80, 0.1);
        padding: 10px;
        border-left: 5px solid #4CAF50;
        border-radius: 8px;
        color: #4CAF50;
        font-size: 0.9em;
    }
    .error-box {
        background-color: rgba(255, 100, 100, 0.1);
        padding: 10px;
        border-left: 5px solid #FF6464;
        border-radius: 8px;
        color: #FF6464;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
@st.cache_data(ttl=300)  # Cache results for 5 minutes
def get_web_context(query, max_results=3):
    """Fetch web search results with detailed error reporting"""
    try:
        search_query = f"{query} 2026"
        logger.info(f"🔍 Web Search Started: '{search_query}'")
        
        with DDGS() as ddgs:
            # Use text search with timeout
            results = list(ddgs.text(search_query, max_results=max_results, timeout=10))
            
            logger.info(f"✅ DuckDuckGo returned {len(results)} raw results")
            
            if not results:
                logger.warning(f"⚠️ No results from DuckDuckGo for: {search_query}")
                return None
            
            # Extract text content from results
            extracted_results = []
            for r in results:
                try:
                    body = r.get('body', '') or r.get('snippet', '')
                    if body:
                        extracted_results.append(body)
                except Exception as e:
                    logger.warning(f"Could not extract result: {e}")
                    continue
            
            if extracted_results:
                combined = "\n".join(extracted_results)
                logger.info(f"✅ Successfully extracted {len(extracted_results)} results ({len(combined)} chars)")
                return combined
            else:
                logger.warning("⚠️ Results found but no body/snippet content")
                return None
                
    except ImportError as e:
        logger.error(f"❌ ImportError: duckduckgo_search not installed - {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Web search error: {type(e).__name__} - {str(e)}")
        return None

def display_web_search_status(query, web_data):
    """Display web search status in the UI"""
    if web_data is None:
        st.warning(f"⚠️ Web search returned no results for: '{query}'")
    elif web_data == "":
        st.warning(f"⚠️ Web search found results but no content for: '{query}'")
    else:
        st.success(f"✅ Web search successful - {len(web_data)} characters of data retrieved")

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
    if not GROQ_KEY:
        return "Error: Missing API Key in Secrets."
    client = Groq(api_key=GROQ_KEY)
    
    system_message = (
        "You are 'StudyAI Master' created by Nissan Gain. Today is May 8, 2026. "
        "You have access to REAL-TIME web data provided in the prompt. "
        "NEVER mention 2023 or knowledge cutoffs. "
        "If web data is provided, use it to give a factual 2026 update. "
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
st.caption("2026 Board Exam Hub | Live Web Access | Powered by Groq")

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

tab1, tab2, tab3, tab4 = st.tabs(["🚀 Doubt Solver", "📈 Predictor", "📜 PYQ Vault", "📝 Sample Gen"])

# TAB 1: CONVERSATIONAL DOUBT SOLVER
with tab1:
    st.subheader("Instant Doubt Solver")
    ds_search = st.toggle("Search Web for latest news/info?", key="ds_search")
    
    # Display History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a doubt or follow-up..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Searching & Thinking..."):
            context = ""
            if ds_search:
                web_data = get_web_context(prompt, 5)
                display_web_search_status(prompt, web_data)
                if web_data:
                    context = f"LATEST 2026 WEB DATA:\n{web_data}\n\n"
                    logger.info(f"📝 Web context added to prompt ({len(context)} chars)")
                else:
                    logger.info("📝 No web data, using knowledge base only")
            
            history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
            full_query = f"{context}History:\n{history}\n\nQuestion: {prompt}"
            
            # Get style config
            style_config = get_response_style_config(st.session_state.response_style)
            
            response = call_groq(full_query, temperature=style_config["temperature"], style_hint=style_config["hint"])
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

# TAB 2: PREDICTOR
with tab2:
    st.subheader("2026 Topic Predictor")
    bp_search = st.toggle("Search latest 2026 CBSE syllabus?", value=True, key="bp_search")
    subject = st.text_input("Subject (e.g. Science):")
    if st.button("Predict High-Weightage Topics"):
        with st.spinner("Analyzing..."):
            query = f"Class 10 {subject} 2026 CBSE board exam weightage"
            context = ""
            if bp_search:
                web_data = get_web_context(query, 5)
                display_web_search_status(query, web_data)
                if web_data:
                    context = f"2026 NEWS:\n{web_data}\n\n"
            
            style_config = get_response_style_config(st.session_state.response_style)
            
            res = call_groq(f"{context}Predict 10 high-probability topics for {subject} 2026 CBSE boards.", model="llama-3.3-70b-versatile", temperature=style_config["temperature"], style_hint=style_config["hint"])
            st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)

# TAB 3: PYQ VAULT
with tab3:
    st.subheader("PYQ Vault")
    pyq_sub = st.selectbox("Subject:", ["Math", "Science", "SST", "English"], key="pyq_v")
    chapter = st.text_input("Chapter Name:", key="pyq_c")
    if st.button("Fetch PYQs"):
        with st.spinner("Fetching..."):
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
            style_config = get_response_style_config(st.session_state.response_style)
            
            res = call_groq(f"Generate 20 NCERT-style practice questions based on CBSE class 10 for {sq_sub} on {sq_topic}.", model="llama-3.3-70b-versatile", temperature=style_config["temperature"], style_hint=style_config["hint"])
            st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)

# --- 5. FOOTER ---
st.divider()
st.markdown('<div class="footer">Created by <b>Nissan Gain</b> | 2026 Edition</div>', unsafe_allow_html=True)
