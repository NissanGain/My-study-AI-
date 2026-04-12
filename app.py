import streamlit as st
from google import genai
from googleapiclient.discovery import build

# 1. API Setup
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY")

# 2. Modern CSS Styling
st.markdown("""
    <style>
    .main { background: #f0f2f6; }
    .stButton>button {
        border-radius: 12px;
        background: linear-gradient(90deg, #4A90E2, #50C878);
        color: white;
        height: 3em;
        font-weight: bold;
    }
    .question-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 8px solid #50C878;
        margin-bottom: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. YouTube Helper
def get_youtube_videos(query):
    if not YOUTUBE_KEY: return None
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_KEY)
    request = youtube.search().list(
        q=query + " class 10 boards one shot ",
        part='snippet', maxResults=6, type='video'
    )
    return request.execute()

# 4. App Logic
st.title("🎯 BoardMaster AI: Class 10 Edition")
st.write(f"Logged in as: **{st.secrets.get('USER_NAME', 'Student')}**")

if GEMINI_KEY:
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        
        # New Tab Layout including PYQ Section
        tab1, tab2, tab3, tab4 = st.tabs(["💬 Doubt Solver", "📈 Topic Predictor", "📝 PYQ & Questions", "📺 Videos"])

        with tab1:
            st.subheader("Instant Doubt Clearing")
            q = st.text_input("Ask any concept question...")
            if st.button("Solve My Doubt"):
                resp = client.models.generate_content(model='gemini-2.5-flash', contents=q)
                st.markdown(f'<div class="question-card">{resp.text}</div>', unsafe_allow_html=True)

        with tab2:
            st.subheader("Topic Predictor")
            sub = st.selectbox("Select Subject", ["Maths", "Physics", "Chemistry", "Biology", "Social Science (SST)", "English"])
            if st.button("Predict High-Weightage Topics"):
                prompt = f"Act as a board examiner. Identify 5 high-yield topics for Class 10 {sub} for the 2026 exams. Focus on patterns from the last 10 years."
                resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                st.info(resp.text)

        with tab3:
            st.subheader("📜 PYQ & Most Important Questions")
            st.write("Generate questions based on past 10-year patterns.")
            
            col1, col2 = st.columns(2)
            with col1:
                pyq_sub = st.selectbox("Subject", ["Social Science", "Science", "Mathematics", "English"], key="pyq_sub")
            with col2:
                q_type = st.selectbox("Question Type", ["Short Answer (2m)", "Long Answer (5m)", "Case-Based", "MCQs", "Competency-Based Questions"])
            
            chapter = st.text_input("Enter Chapter Name (e.g., Nationalism in Europe, Electricity)")
            
            if st.button("Generate Important Questions"):
                with st.spinner("Analyzing past papers..."):
                    prompt = f"Generate 5 most important {q_type} questions for Class 10 {pyq_sub}, Chapter: {chapter}. Base these on the frequency they appeared in past 10-year board papers. Include a tiny 'Hint' for each answer."
                    resp = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    st.markdown(f'<div class="question-card">{resp.text}</div>', unsafe_allow_html=True)

        with tab4:
            st.subheader("Visual Learning")
            vid_q = st.text_input("Search for specific topic videos:")
            if st.button("Fetch Lessons"):
                results = get_youtube_videos(vid_q)
                if results:
                    for item in results['items']:
                        st.video(f"https://www.youtube.com/watch?v={item['id']['videoId']}")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.warning("Connect your API keys in Settings to start!")
