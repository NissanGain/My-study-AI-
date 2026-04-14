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
    }
    .stButton>button { border-radius: 10px; width: 100%; font-weight: bold; }
    .footer { text-align: center; padding: 20px; font-size: 1.1em; opacity: 0.8; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def get_web_context(query, max_results=3):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=max_results)]
            return "\n".join(results)
    except Exception:
        return "No live web data found."

def call_groq(prompt, model="llama-3.1-8b-instant"):
    if not GROQ_KEY: return "Error: Missing API Key."
    client = Groq(api_key=GROQ_KEY)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# --- 4. MAIN INTERFACE ---
st.title("🎯 StudyAI Master")
st.caption("2026 Board Exam Hub | Powered by Groq Unlimited")

# Initialize Chat Memory for Doubt Solver
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Doubt Solver", "📈 Predictor", "📜 PYQ Vault", "📝 Sample Gen"])

# TAB 1: CONVERSATIONAL DOUBT SOLVER
with tab1:
    st.subheader("Instant Doubt Solver")
    
    # Search Toggle
    ds_search = st.toggle("Search Web for latest info?", key="ds_search")
    
    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input for Main Question & Follow-ups
    if prompt := st.chat_input("Ask your doubt or a follow-up question..."):
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Response
        with st.spinner("Teacher is thinking..."):
            context = ""
            if ds_search:
                context = f"Web Research: {get_web_context(prompt, 3)}\n\n"
            
            # Create a history string so the AI remembers the conversation
            history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
            
            full_query = f"{context}Conversation History:\n{history}\n\nTask: Answer the latest user question based on history and context. Act as a Class 10 teacher."
            
            response = call_groq(full_query)
            
            # Add assistant message to state
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

    if st.button("Clear Chat Conversation"):
        st.session_state.messages = []
        st.rerun()

# --- (Other tabs remain the same as your previous working version) ---
# TAB 2: PREDICTOR
with tab2:
    st.subheader("2026 Topic Predictor")
    bp_search = st.toggle("Search latest 2026 patterns?", value=True, key="bp_search")
    subject = st.text_input("Enter Subject:", key="bp_sub")
    if st.button("Predict Topics"):
        with st.spinner("Analyzing..."):
            context = f"News: {get_web_context(f'Class 10 {subject} 2026 board exam pattern', 5)}\n\n" if bp_search else ""
            prediction = call_groq(f"{context}Identify 5 high-probability topics for {subject} 2026 boards.", model="llama-3.3-70b-versatile")
            st.markdown(f'<div class="answer-box">{prediction}</div>', unsafe_allow_html=True)

# TAB 3: PYQ VAULT
with tab3:
    st.subheader("PYQ Vault")
    pyq_sub = st.selectbox("Select Subject:", ["Math", "Science", "SST", "English"], key="pyq_v")
    chapter = st.text_input("Chapter:", key="pyq_c")
    if st.button("Get PYQs"):
        with st.spinner("Searching..."):
            res = call_groq(f"List 10 important PYQs for Class 10 {pyq_sub}, Chapter: {chapter}.")
            st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)

# TAB 4: SAMPLE GEN
with tab4:
    st.subheader("Sample Question Generator")
    sq_sub = st.selectbox("Select Subject:", ["Science", "Math", "SST", "English"], key="sq_s")
    sq_topic = st.text_input("Topic:", key="sq_t")
    if st.button("Generate Set"):
        with st.spinner("Crafting..."):
            res = call_groq(f"Generate 5 NCERT-style questions for {sq_sub} on {sq_topic}.", model="llama-3.3-70b-versatile")
            st.markdown(f'<div class="answer-box">{res}</div>', unsafe_allow_html=True)

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
