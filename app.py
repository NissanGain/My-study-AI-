import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS

# --- 1. SETUP & SECRETS ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY")

st.set_page_config(page_title="StudyAI Master", page_icon="🎯", layout="wide")

# --- 2. IMPROVED STYLING (Light/Dark Mode Friendly) ---
st.markdown("""
    <style>
    /* This allows the app to adapt to Light/Dark mode automatically */
    .answer-box {
        background-color: rgba(128, 128, 128, 0.1); /* Transparent gray */
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #4A90E2;
        margin-bottom: 20px;
        color: inherit; /* Takes text color from the theme */
    }
    .stButton>button {
        border-radius: 10px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def get_web_context(query, max_results=3):
    try:
        with DDGS() as ddgs:
            # max_results is now dynamic based on your toggle
            results = [r['body'] for r in ddgs.text(query, max_results=max_results)]
            return "\n".join(results)
    except Exception:
        return "No live web data found."

def call_groq(prompt, model="llama-3.1-8b-instant"):
    client = Groq(api_key=GROQ_KEY)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# --- 4. MAIN INTERFACE ---
st.title("🎯 StudyAI Master")
st.caption("2026 Board Exam Prep | Powered by Groq Unlimited")

# Sidebar for Status
with st.sidebar:
    st.header("⚡ System Status")
    if GROQ_KEY: 
        st.success("Groq AI: 14,400 RPD Active")
    else:
        st.error("Missing GROQ_API_KEY")
    st.divider()
    st.write("📍 Asansol Study Hub")
    st.info("Tip: Light/Dark mode can be changed in your browser or Streamlit settings (top right menu).")

# Tabs
tab1, tab2, tab3 = st.tabs(["🚀 Doubt Solver", "📈 Board Predictor", "📜 PYQ Vault"])

with tab1:
    st.subheader("Instant Doubt Solver")
    
    # NEW: Search Web Toggle
    deep_search = st.toggle("Deep Search Mode (Read 10 Articles)", value=False)
    
    user_q = st.text_input("Ask any doubt:", placeholder="e.g. Explain photosynthesis in detail")
    
    if st.button("Solve Now"):
        if not GROQ_KEY:
            st.error("Add your API Key to secrets!")
        else:
            # Set results based on toggle
            res_limit = 10 if deep_search else 3
            
            with st.spinner(f"Reading {res_limit} web sources..."):
                web_info = get_web_context(user_q, max_results=res_limit)
                
                full_prompt = f"Context from Web:\n{web_info}\n\nQuestion: {user_q}\n\nAnswer like an expert teacher:"
                answer = call_groq(full_prompt)
                
                st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)
                st.caption(f"🔍 Sources: Live Web Search ({res_limit} articles) | Model: Llama 3.1")

with tab2:
    st.subheader("Deep Logic Board Predictor")
    st.write("Using High-Reasoning Groq for exam patterns.")
    predict_q = st.text_input("Enter subject for 2026 prediction (e.g., Science):")
    
    if st.button("Analyze Patterns"):
        with st.spinner("Analyzing 2026 Board trends..."):
            # Using llama-3.3-70b-versatile for "Expert" predictions if you have it, 
            # otherwise llama-3.1-8b-instant works great too!
            prediction_prompt = f"Analyze Class 10 Board exam patterns and predict high-weightage topics for 2026: {predict_q}"
            prediction = call_groq(prediction_prompt, model="llama-3.3-70b-versatile")
            
            st.markdown(f'<div class="answer-box">{prediction}</div>', unsafe_allow_html=True)
            st.caption("🧠 Intelligence: Llama 3.3 Versatile (Groq)")

with tab3:
    st.subheader("PYQ Vault")
    subject = st.selectbox("Select Subject", ["Science", "Math", "SST", "English"])
    if st.button("Get Important PYQs"):
        with st.spinner("Fetching questions..."):
            pyq_prompt = f"List 10 most repeated Class 10 {subject} Previous Year Questions for Board Exams."
            pyqs = call_groq(pyq_prompt)
            st.markdown(f'<div class="answer-box">{pyqs}</div>', unsafe_allow_html=True)
            
