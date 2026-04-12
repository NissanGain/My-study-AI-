import streamlit as st
from google import genai
from googleapiclient.discovery import build

# 1. API Setup
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY")

# 2. THEME-AWARE CSS
st.markdown("""
    <style>
    .answer-card {
        background-color: rgba(128, 128, 128, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 20px;
        border-radius: 15px;
        margin-top: 20px;
        border-left: 5px solid #4A90E2;
    }
    .stButton>button {
        border-radius: 10px;
        background: linear-gradient(45deg, #4A90E2, #63B3ED);
        color: white !important;
        font-weight: 700;
        border: none;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. YouTube Helper
def get_youtube_videos(query):
    if not YOUTUBE_KEY: return None
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_KEY)
    request = youtube.search().list(
        q=query + " class 10 boards ncert explanation",
        part='snippet', maxResults=3, type='video'
    )
    return request.execute()

# 4. App Content
st.title("🎯 StudyAI Master")
st.caption("Your All-in-One AI Board Exam Companion")

if GEMINI_KEY:
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        
        tab1, tab2, tab3, tab4 = st.tabs(["💡 Doubts", "📈 Predictions", "📜 PYQs", "🎥 Videos"])

        with tab1:
            st.subheader("Instant Doubt Solver")
            user_q = st.text_input("Ask any syllabus question:", placeholder="e.g., Explain the process of photosynthesis")
            if st.button("Solve Now"):
                with st.spinner("Analyzing..."):
                    resp = client.models.generate_content(model='gemini-2.5-flash', contents=user_q)
                    st.markdown(f'<div class="answer-card">{resp.text}</div>', unsafe_allow_html=True)

        with tab2:
            st.subheader("Topic Predictor")
            sub = st.selectbox("Subject", ["Mathematics", "Science", "Social Science (SST)", "English"])
            if st.button("Predict High-Weightage Topics"):
                prompt = f"Predict the 5 most important topics for Class 10 {sub} for the 2026 exams based on 10-year patterns."
                resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                st.write(resp.text)

        with tab3:
            st.subheader("PYQ Generation")
            col1, col2 = st.columns(2)
            with col1: pyq_sub = st.selectbox("Pick Subject", ["Social Science", "Science", "Math"], key="pyq_v3")
            with col2: chap = st.text_input("Enter Chapter", placeholder="Nationalism in India")
            
            if st.button("Generate Important PYQs"):
                prompt = f"List 5 highly important questions for Class 10 {pyq_sub}, Chapter: {chap} based on past 10-year patterns."
                resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                st.markdown(f'<div class="answer-card">{resp.text}</div>', unsafe_allow_html=True)

        with tab4:
            st.subheader("Video Library")
            vid_q = st.text_input("Topic for video search:")
            if st.button("Find Lessons"):
                results = get_youtube_
