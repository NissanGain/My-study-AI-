import streamlit as st
from google import genai
from googleapiclient.discovery import build

# 1. API Setup
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY")

# 2. Custom CSS for "Fancy" UI
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background-color: #4A90E2;
        color: white;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #357ABD;
        transform: scale(1.02);
    }
    .answer-box {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #333;
        border-left: 5px solid #4A90E2;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Helper Functions
def get_youtube_videos(query):
    if not YOUTUBE_KEY: return None
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_KEY)
    request = youtube.search().list(
        q=query + " class 10 boards educational ncert",
        part='snippet', maxResults=3, type='video'
    )
    return request.execute()

# 4. App Content
st.title("🚀 StudyAI Master:")
st.caption("Powered by Modern Digital Services")

if GEMINI_KEY:
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        
        # Using Tabs instead of Sidebar for a modern feel
        tab1, tab2, tab3 = st.tabs(["💡 Smart Doubt Solver", "🔥 Board Predictor", "🎥 Video Lessons"])

        with tab1:
            st.subheader("Ask anything about your syllabus")
            user_query = st.text_input("e.g., Why is the sky blue?", placeholder="Type your doubt here...")
            if st.button("Generate Answer"):
                with st.spinner("Thinking..."):
                    response = client.models.generate_content(
                        model='gemini-2.5-flash', 
                        contents=user_query
                    )
                    st.markdown(f'<div class="answer-box">{response.text}</div>', unsafe_allow_html=True)

        with tab2:
            st.subheader("Predict High-Yield Topics")
            subject = st.selectbox("Select Subject", ["Physics", "Chemistry", "Biology", "Maths", "English"])
            if st.button("Run AI Analysis"):
                with st.spinner("Analyzing past patterns..."):
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"Predict 5 high-probability topics for Class 10 {subject} board exam with brief reasons."
                    )
                    st.success("AI Prediction Complete!")
                    st.write(response.text)

        with tab3:
            st.subheader("Best Video Lessons")
            topic = st.text_input("What topic are you studying?", placeholder="e.g., Trigonometry")
            if st.button("Find Videos"):
                results = get_youtube_videos(topic)
                if results:
                    for item in results['items']:
                        v_id = item['id']['videoId']
                        st.video(f"https://www.youtube.com/watch?v={v_id}")
                        st.divider()

    except Exception as e:
        st.error(f"Error connecting to AI: {e}")
else:
    st.warning("Setup Required: Please add your API Keys in the Streamlit Dashboard.")

# Sidebar Branding
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=100)
    st.title("Settings")
    st.info("This tool is designed to help Class 10 students master their board exams with AI-assisted learning.")
