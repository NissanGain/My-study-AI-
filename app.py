import streamlit as st
from google import genai
from googleapiclient.discovery import build

# 1. API Setup
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY")

# 2. SMART CSS (Adapts to Light/Dark Mode)
st.markdown("""
    <style>
    /* Use 'secondaryBackgroundColor' for cards so they adapt */
    .answer-card {
        background-color: rgba(128, 128, 128, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 20px;
        border-radius: 15px;
        margin-top: 20px;
        border-left: 5px solid #4A90E2;
        transition: 0.3s;
    }
    
    /* Make buttons pop regardless of theme */
    .stButton>button {
        border-radius: 10px;
        background: linear-gradient(45deg, #4A90E2, #63B3ED);
        color: white !important;
        font-weight: 700;
        border: none;
        padding: 10px 20px;
    }

    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
    }

    /* Keep the Tab headers clean */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    /* Style the sidebar for Modern Digital Services */
    [data-testid="stSidebar"] {
        padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Helper Functions
def get_youtube_videos(query):
    if not YOUTUBE_KEY: return None
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_KEY)
    request = youtube.search().list(
        q=query + " class 10 boards ncert",
        part='snippet', maxResults=3, type='video'
    )
    return request.execute()

# 4. App Content
st.title("🎯 StudyAI Master 2026")
st.caption("Custom built for Modern Digital Services")

if GEMINI_KEY:
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        
        tab1, tab2, tab3, tab4 = st.tabs(["💡 Doubts", "📈 Predictions", "📜 PYQs", "🎥 Videos"])

        with tab1:
            user_q = st.text_input("Ask a question:", placeholder="e.g., Difference between mass and weight")
            if st.button("Get Answer"):
                with st.spinner("Thinking..."):
                    resp = client.models.generate_content(model='gemini-2.5-flash', contents=user_q)
                    st.markdown(f'<div class="answer-card">{resp.text}</div>', unsafe_allow_html=True)

        with tab2:
            sub = st.selectbox("Subject", ["Mathematics", "Science", "Social Science (SST)", "English"])
            if st.button("Show Important Topics"):
                prompt = f"Predict the 5 most important topics for Class 10 {sub} for the 2026 exams."
                resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                st.write(resp.text)

        with tab3:
            col1, col2 = st.columns(2)
            with col1: pyq_sub = st.selectbox("Pick Subject", ["Social Science", "Science", "Math"], key="pyq_sub_v2")
            with col2: chap = st.text_input("Enter Chapter", placeholder="Nationalism in India")
            
            if st.button("Analyze Past Papers"):
                prompt = f"List 5 highly important questions for Class 10 {pyq_sub}, Chapter: {chap} based on past 10-year board patterns."
                resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                st.markdown(f'<div class="answer-card">{resp.text}</div>', unsafe_allow_html=True)

        with tab4:
            vid_q = st.text_input("Topic for video:")
            if st.button("Fetch Top Lessons"):
                results = get_youtube_videos(vid_q)
                if results:
                    for item in results['items']:
                        st.video(f"https://www.youtube.com/watch?v={item['id']['videoId']}")

    except Exception as e:
        st.error(f"Connection Error: {e}")

# Sidebar Branding
with st.sidebar:
    st.header("Modern Digital")
    st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=70)
    st.info("Helping Class 10 students in Asansol and beyond master their exams.")
