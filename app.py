import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS

# --- 1. SETUP & SECRETS ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY")

st.set_page_config(page_title="StudyAI Master", page_icon="🎯", layout="wide")

# --- 2. THEME-FRIENDLY STYLING ---
st.markdown("""
    <style>
    /* Fixed styling for light/dark mode compatibility */
    .answer-box {
        background-color: rgba(128, 128, 128, 0.1); 
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #4A90E2;
        margin-bottom: 20px;
        color: inherit;
    }
    .stButton>button {
        border-radius: 10px;
        width: 100%;
        font-weight: bold;
    }
    .footer {
        text-align: center;
        padding: 20px;
        font-size: 1.2em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def get_web_context(query, max_results=3):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=max_results)]
            return "\n".join(results)
    except Exception:
        return "No live web data found. Relying on internal knowledge."

def call_groq(prompt, model="llama-3.1-8b-instant"):
    if not GROQ_KEY:
        return "Error: Please add your GROQ_API_KEY in Streamlit Secrets."
    client = Groq(api_key=GROQ_KEY)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# --- 4. MAIN INTERFACE ---
st.title("🎯 StudyAI Master")
st.caption("2026 Board Exam Hub | Powered by Groq Unlimited")

# Sidebar
with st.sidebar:
    st.header("⚡ System Status")
    if GROQ_KEY:
        st.success("Groq AI Active (14.4k RPD)")
    st.divider()
    st.write("📍 Asansol/Durgapur Hub")
    st.info("💡 Change Theme: Go to Settings > Theme in the top-right menu.")

# Tabs
tab1, tab2, tab3 = st.tabs(["🚀 Doubt Solver", "📈 Board Predictor", "📜 PYQ Vault"])

# TAB 1: DOUBT SOLVER
with tab1:
    st.subheader("Instant Doubt Solver")
    ds_search = st.toggle("Search Web for this doubt?", key="ds_search")
    user_q = st.text_input("Ask any doubt:", placeholder="e.g. Explain refraction of light")
    
    if st.button("Solve My Doubt"):
        with st.spinner("AI is thinking..."):
            context = ""
            if ds_search:
                context = f"Web Context: {get_web_context(user_q, max_results=5)}\n\n"
            prompt = f"{context}Question: {user_q}\n\nAnswer as an expert Class 10 teacher."
            answer = call_groq(prompt)
            st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

# TAB 2: BOARD PREDICTOR
with tab2:
    st.subheader("2026 Topic Predictor")
    bp_search = st.toggle("Search latest 2026 syllabus & most probable questions?", value=True, key="bp_search")
    subject = st.text_input("Enter Subject:", placeholder="e.g. Science or SST")
    
    if st.button("Predict High-Weightage Topics"):
        with st.spinner("Scanning board updates..."):
            context = ""
            if bp_search:
                search_query = f"Class 10 {subject} 2026 board exam pattern and most probable questions"
                context = f"Latest Board News: {get_web_context(search_query, max_results=10)}\n\n"
            
            prompt = f"{context}Based on the above info, identify 5 high-probability topics for {subject} 2026 boards."
            # Using smarter model for predictions
            prediction = call_groq(prompt, model="llama-3.3-70b-versatile")
            st.markdown(f'<div class="answer-box">{prediction}</div>', unsafe_allow_html=True)

# TAB 3: PYQ VAULT
with tab3:
    st.subheader("Recent PYQ Generator")
    pyq_search = st.toggle("Search for 10 year PYQs including 2025-26 papers?", value=True, key="pyq_search")
    pyq_sub = st.selectbox("Select Subject:", ["Math", "Science", "SST", "English"], key="pyq_sub_sel")
    chapter = st.text_input("Chapter Name:", placeholder="e.g. Nationalism in India")
    
    if st.button("Generate Questions"):
        with st.spinner("Searching papers..."):
            context = ""
            if pyq_search:
                search_query = f"Class 10 {pyq_sub} {chapter} last 10 years board questions including 2025 2026"
                context = f"Exam Data: {get_web_context(search_query, max_results=10)}\n\n"
            
            # FIXED LOGIC HERE:
            prompt = f"{context}List 10 important PYQs for Class 10 {pyq_sub}, Chapter: {chapter}. Include questions from the last 10 years and trends for 2025-26."
            pyqs = call_groq(prompt)
            st.markdown(f'<div class="answer-box">{pyqs}</div>', unsafe_allow_html=True)

# --- 5. FOOTER SECTION ---
st.divider()
st.markdown(
    """
    <div class="footer">
        Created by <b>Nissan Gain</b>
    </div>
    """,
    unsafe_allow_html=True
    )
            
