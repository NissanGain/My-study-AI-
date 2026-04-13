import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS
from google import genai

# --- 1. SETUP & SECRETS ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY")
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")

st.set_page_config(page_title="StudyAI Master", page_icon="🎯", layout="wide")

# --- 2. STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .answer-box {
        background-color: #1E2130;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #4A90E2;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def get_web_context(query):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results)
    except Exception:
        return "No live web data found."

# --- 4. MAIN INTERFACE ---
st.title("🎯 StudyAI Master")
st.caption("2026 Board Exam Prep | Powered by Groq & Gemini")

# Sidebar for Status
with st.sidebar:
    st.header("⚡ System Status")
    if GROQ_KEY: st.success("Groq: 14,400 RPD Active")
    if GEMINI_KEY: st.info("Gemini: 20 RPD Backup Active")
    st.divider()
    st.write("📍 Location: Asansol/Durgapur Hub")
    st.write("🎓 Target: 95%+ in Class 10 Boards")

# Tabs for Different Features
tab1, tab2, tab3 = st.tabs(["🚀 Doubt Solver (Unlimited)", "📈 Board Predictor", "📜 PYQ Vault"])

with tab1:
    st.subheader("Instant Doubt Solver with Web Search")
    user_q = st.text_input("Ask any question (e.g., 'Latest CBSE 2026 syllabus update'):")
    
    if st.button("Solve Now"):
        if not GROQ_KEY:
            st.error("Please add GROQ_API_KEY to your Streamlit Secrets.")
        else:
            with st.spinner("Searching the web & generating answer..."):
                # Call Groq + Web Search
                client = Groq(api_key=GROQ_KEY)
                web_info = get_web_context(user_q)
                
                full_prompt = f"Context from Web:\n{web_info}\n\nQuestion: {user_q}\n\nAnswer like an expert Class 10 teacher:"
                
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": full_prompt}]
                )
                
                st.markdown(f'<div class="answer-box">{response.choices[0].message.content}</div>', unsafe_allow_html=True)
                st.caption("🔍 Sources: Live DuckDuckGo Search | Model: Llama 3.1 (Groq)")

with tab2:
    st.subheader("Deep Logic Board Predictor")
    st.write("Using Gemini's advanced reasoning for exam patterns.")
    predict_q = st.text_input("Enter subject for 2026 prediction:")
    
    if st.button("Analyze Patterns"):
        if not GEMINI_KEY:
            st.error("Please add GEMINI_API_KEY to your Streamlit Secrets.")
        else:
            with st.spinner("Gemini is analyzing 10 years of data..."):
                client = genai.Client(api_key=GEMINI_KEY)
                resp = client.models.generate_content(
                    model='gemini-2.5-flash-lite', 
                    contents=f"Predict high-weightage topics for 2026 Boards: {predict_q}"
                )
                st.markdown(f'<div class="answer-box">{resp.text}</div>', unsafe_allow_html=True)
                st.caption("🧠 Intelligence: Gemini 2.5 Flash Lite")

with tab3:
    st.subheader("PYQ Vault")
    subject = st.selectbox("Select Subject", ["Science", "Math", "SST", "English"])
    if st.button("Get Important PYQs"):
        client = Groq(api_key=GROQ_KEY)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f"List 10 most repeated Class 10 {subject} PYQs for Board Exams."}]
        )
        st.write(response.choices[0].message.content)

