from datetime import datetime # Add this to your imports at the very top

def call_groq(user_prompt, model="llama-3.1-8b-instant"):
    if not GROQ_KEY:
        return "Error: Missing API Key."
    
    client = Groq(api_key=GROQ_KEY)
    
    # This line automatically gets today's date (e.g., April 15, 2026)
    today = datetime.now().strftime("%B %d, %Y")
    
    system_instruction = (
        f"You are 'StudyAI Master' created by Nissan Gain. "
        f"Today's date is {today}. " # The AI now always knows the real date!
        "You have access to REAL-TIME web data provided in the prompt. "
        "NEVER mention 2023 or knowledge cutoffs. "
        "Use the web data to provide factual, current updates."
    )
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content
    
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
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #4A90E2;
        margin-bottom: 10px;
        color: inherit;
    }
    .stButton>button { border-radius: 10px; width: 100%; font-weight: bold; }
    .footer { text-align: center; padding: 20px; font-size: 1.1em; opacity: 0.8; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def get_web_context(query, max_results=3):
    try:
        with DDGS() as ddgs:
            # We add 2026 to the search to ensure fresh results
            results = [r['body'] for r in ddgs.text(f"{query} 2026", max_results=max_results)]
            return "\n".join(results)
    except Exception:
        return "No live web data found. Using internal knowledge."

def call_groq(user_prompt, model="llama-3.1-8b-instant"):
    if not GROQ_KEY:
        return "Error: Missing API Key in Secrets."
    client = Groq(api_key=GROQ_KEY)
    
    # This instruction forces the AI to accept it is 2026
    system_message = (
        "You are 'StudyAI Master' created by Nissan Gain. Today is April 15, 2026. "
        "You have access to REAL-TIME web data provided in the prompt. "
        "NEVER mention 2023 or knowledge cutoffs. "
        "If web data is provided, use it to give a factual 2026 update."
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2 # Keeps the AI focused on facts
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Connection Error: {str(e)}"

# --- 4. MAIN INTERFACE ---
st.title("🎯 StudyAI Master")
st.caption("2026 Board Exam Hub | Live Web Access | Powered by Groq")

# Initialize Chat Memory
if "messages" not in st.session_state:
    st.session_state.messages = []

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
            context = f"LATEST 2026 WEB DATA: {get_web_context(prompt, 5)}\n\n" if ds_search else ""
            history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
            full_query = f"{context}History:\n{history}\n\nQuestion: {prompt}"
            
            response = call_groq(full_query)
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
            query = f"Class 10 {subject} 2026 CBSC board exam weightage"
            context = f"2026 NEWS: {get_web_context(query, 5)}\n\n" if bp_search else ""
            res = call_groq(f"{context}Predict 10 high-probability topics for {subject} 2026 CBSE boards.", model="llama-3.3-70b-versatile")
            st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)

# TAB 3: PYQ VAULT
with tab3:
    st.subheader("PYQ Vault")
    pyq_sub = st.selectbox("Subject:", ["Math", "Science", "SST", "English"], key="pyq_v")
    chapter = st.text_input("Chapter Name:", key="pyq_c")
    if st.button("Fetch PYQs"):
        with st.spinner("Fetching..."):
            res = call_groq(f"List Last 10 Years PYQs for Class 10 CBSE {pyq_sub}, Chapter: {chapter}.")
            st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)

# TAB 4: SAMPLE GEN
with tab4:
    st.subheader("Sample Question Generator")
    sq_sub = st.selectbox("Subject:", ["Math", "Science", "SST", "English"], key="sq_v")
    sq_topic = st.text_input("Topic:", key="sq_t")
    if st.button("Generate Set"):
        with st.spinner("Crafting..."):
            res = call_groq(f"Generate 20 NCERT-style practice questions based on CBSE class 10 for {sq_sub} on {sq_topic}.", model="llama-3.3-70b-versatile")
            st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)

# --- 5. FOOTER ---
st.divider()
st.markdown('<div class="footer">Created by <b>Nissan Gain</b> | 2026 Edition</div>', unsafe_allow_html=True)
