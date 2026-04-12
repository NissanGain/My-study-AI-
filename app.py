import streamlit as st
from google import genai
from googleapiclient.discovery import build

# 1. API Setup (using Secrets)
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY")

# 2. THE CSS BLOCK - This is the "Magic" part
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #1e1e2f 0%, #121212 100%);
        color: #ffffff;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(255, 255, 255, 0.05);
        padding: 10px;
        border-radius: 15px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 10px;
        color: #888;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4A90E2 !important;
        color: white !important;
    }

    /* Professional "Card" for AI Answers */
    .answer-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        margin-top: 20px;
        border-left: 6px solid #4A90E2;
    }

    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        border: none;
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        color: #000;
        font-weight: 800;
        padding: 15px;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0, 201, 255, 0.4);
        color: #fff;
    }

    /* Sidebar Branding */
    [data-testid="stSidebar"] {
        background-color: #161625;
        border-right: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Helper Functions
def get_youtube_videos(query):
    if not YOUTUBE_KEY: return None
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_KEY)
    request = youtube.search().list(
        q=query + " class 10 boards ncert explanation",
        part='snippet', maxResults=3, type='video'
    )
    return request.execute()

# 4. App Content
st.title("⚡ StudyAI Master: Class 10 Prep")
st.markdown("🚀 *Crafted by Modern Digital Services*")
st.divider()

if GEMINI_KEY:
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        
        # Dashboard Tabs
        t1, t2, t3, t4 = st.tabs(["💡 Doubt Solver", "📈 Topic Predictor", "📜 PYQ Vault", "🎥 Video Lessons"])

        with t1:
            st.subheader("What's on your mind?")
            user_q = st.text_input("Ask a question (e.g., Explain Newton's 3rd Law)", key="doubt")
            if st.button("Get Expert Answer"):
                with st.spinner("AI is analyzing..."):
                    resp = client.models.generate_content(model='gemini-2.5-flash', contents=user_q)
                    st.markdown(f'<div class="answer-card">{resp.text}</div>', unsafe_allow_html=True)

        with t2:
            st.subheader("Pattern Analysis")
            sub = st.selectbox("Subject", ["Mathematics", "Science", "Social Science (SST)", "English"])
            if st.button("Run Prediction"):
                prompt = f"Act as a Class 10 Board Examiner. Predict the 5 most important topics for {sub} based on 10-year patterns."
                resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                st.info(resp.text)

        with t3:
            st.subheader("PYQ Generator")
            col1, col2 = st.columns(2)
            with col1: pyq_sub = st.selectbox("Pick Subject", ["Social Science", "Science", "Math"], key="sub_pyq")
            with col2: chap = st.text_input("Chapter Name")
            
            if st.button("Generate Important Questions"):
                prompt = f"List 5 high-frequency PYQs for Class 10 {pyq_sub}, Chapter: {chap}. Include the year they appeared if possible."
                resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                st.markdown(f'<div class="answer-card">{resp.text}</div>', unsafe_allow_html=True)

        with t4:
            st.subheader("Visual Learning Hub")
            vid_q = st.text_input("Search for a concept video:")
            if st.button("Fetch Best Lessons"):
                results = get_youtube_videos(vid_q)
                if results:
                    for item in results['items']:
                        st.video(f"https://www.youtube.com/watch?v={item['id']['videoId']}")
                        st.divider()

    except Exception as e:
        st.error(f"Error: {e}")

# Sidebar Info
with st.sidebar:
    st.header("Modern Digital")
    st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=80)
    st.markdown("---")
    st.success("Target: 95% in Boards 2026")
    st.write("Using this tool helps you focus on high-yield topics instead of studying blindly.")
