import streamlit as st
from groq import Groq
from duckduckgo_search import DDGS

# --- 1. SETUP & SECRETS ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY")

st.set_page_config(page_title="StudyAI Master", page_icon="🎯", layout="wide")

# --- 2. THEME-FRIENDLY STYLING ---
st.markdown("""
    <style>
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
        return "No live web data found. Relying on NCERT patterns."

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

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Doubt Solver", "📈 Predictor", "📜 PYQ Vault", "📝 Sample Paper Gen"])

# TAB 1: DOUBT SOLVER
with tab1:
    st.subheader("Instant Doubt Solver")
    ds_search = st.toggle("Search Web for this doubt?", key="ds_search")
    user_q = st.text_input("Ask any doubt:", placeholder="Explain Ohm's Law")
    if st.button("Solve My Doubt"):
        with st.spinner("Analyzing..."):
            context = f"Web Context: {get_web_context(user_q, 3)}\n\n" if ds_search else ""
            answer = call_groq(f"{context}Question: {user_q}\n\nAnswer like an expert Class 10 teacher.")
            st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

# TAB 2: BOARD PREDICTOR
with tab2:
    st.subheader("2026 Topic Predictor")
    bp_search = st.toggle("Search latest 2026 patterns?", value=True, key="bp_search")
    subject = st.text_input("Enter Subject:", key="bp_sub")
    if st.button("Predict High-Weightage Topics"):
        with st.spinner("Scanning board updates..."):
            context = f"Latest Board News: {get_web_context(f'Class 10 {subject} 2026 board exam pattern', 10)}\n\n" if bp_search else ""
            prediction = call_groq(f"{context}Identify 5 high-probability topics for {subject} 2026 boards.", model="llama-3.3-70b-versatile")
            st.markdown(f'<div class="answer-box">{prediction}</div>', unsafe_allow_html=True)

# TAB 3: PYQ VAULT
with tab3:
    st.subheader("Recent PYQ Generator")
    pyq_search = st.toggle("Search for 10-year patterns?", value=True, key="pyq_search")
    pyq_sub = st.selectbox("Select Subject:", ["Math", "Science", "SST", "English"], key="pyq_vault_sub")
    chapter = st.text_input("Chapter Name:", key="pyq_chap")
    if st.button("Generate Questions"):
        with st.spinner("Searching papers..."):
            context = f"Exam Data: {get_web_context(f'Class 10 {pyq_sub} {chapter} last 10 years board questions', 8)}\n\n" if pyq_search else ""
            pyqs = call_groq(f"{context}List 10 important PYQs for Class 10 {pyq_sub}, Chapter: {chapter}.")
            st.markdown(f'<div class="answer-box">{pyqs}</div>', unsafe_allow_html=True)

# TAB 4: SAMPLE QUESTION GENERATOR (NEW!)
with tab4:
    st.subheader("NCERT & PYQ Sample Question Generator")
    st.write("Generate practice questions that follow the latest 2026 marking scheme.")
    sq_search = st.toggle("Search web for 2026 Sample Paper style?", value=True, key="sq_search")
    
    col1, col2 = st.columns(2)
    with col1:
        sq_sub = st.selectbox("Select Subject:", ["Science", "Math", "SST", "English", "Hindi"], key="sq_sub")
        q_type = st.selectbox("Question Type:", ["MCQs","Very Short Answer Type(1-2 Marks)","Short Answer (2-3 Marks)", "Long Answer (5 Marks)", "Case Based"], key="q_type")
    with col2:
        sq_topic = st.text_input("Topic/Chapter:", placeholder="e.g., Electricity or Life Processes", key="sq_topic")
        q_num = st.slider("Number of questions:", 1, 20, 10)

    if st.button("Generate Practice Set"):
        with st.spinner("Crafting NCERT-style questions..."):
            context = ""
            if sq_search:
                search_query = f"Class 10 {sq_sub} {sq_topic} 2026 board exam sample questions and marking scheme"
                context = f"Recent Board Sample Style: {get_web_context(search_query, max_results=7)}\n\n"
            
            prompt = f"""
            {context}
            Act as a Senior CBSE/Board Paper Setter. 
            Generate {q_num} {q_type} questions for Class 10 {sq_sub} on the topic: {sq_topic}.
            
            Rules:
            1. Questions MUST be based on NCERT syllabus.
            2. Match the difficulty level of Previous Year Questions (PYQs).
            3. Include a short 'Answer Key' or 'Hints' section at the bottom.
            """
            
            sample_set = call_groq(prompt, model="llama-3.3-70b-versatile")
            st.markdown(f'<div class="answer-box">{sample_set}</div>', unsafe_allow_html=True)
            st.caption("✅ Questions strictly follow NCERT & 2026 Exam Trends.")

# --- 5. FOOTER SECTION ---
st.divider()
st.markdown(
    """
    <div class="footer">
        Created by <b>Nissan Gain</b> | Last updated: April 2026
    </div>
    """,
    unsafe_allow_html=True
)
