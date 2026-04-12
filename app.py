import streamlit as st
import google.generativeai as genai
from googleapiclient.discovery import build

# 1. Setup API Keys from Secrets
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY")

def get_youtube_videos(query):
    if not YOUTUBE_KEY:
        return None
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_KEY)
    request = youtube.search().list(
        q=query + " class 10 boards educational",
        part='snippet',
        maxResults=3,
        type='video'
    )
    return request.execute()

# 2. Page Setup
st.set_page_config(page_title="AI Study Assistant", page_icon="🎓")
st.title("🎓 AI Study Master 2026")

if GEMINI_KEY:
    try:
        # Fixed model naming to avoid 404
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        menu = ["Ask a Question", "Predict Board Topics", "Recommended Videos"]
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Ask a Question":
            user_query = st.text_input("What do you want to learn today?")
            if st.button("Get Expert Answer"):
                response = model.generate_content(user_query)
                st.write("### 🤖 Answer:")
                st.info(response.text)

        elif choice == "Predict Board Topics":
            subject = st.text_input("Enter Subject (e.g. Physics, Science):")
            if st.button("Predict"):
                response = model.generate_content(f"Predict 5 high-yield topics for Class 10 {subject} board exams.")
                st.success(response.text)

        elif choice == "Recommended Videos":
            topic = st.text_input("What topic do you need a video for?")
            if st.button("Find Best Videos"):
                results = get_youtube_videos(topic)
                if results:
                    for item in results['items']:
                        title = item['snippet']['title']
                        thumb = item['snippet']['thumbnails']['high']['url']
                        v_id = item['id']['videoId']
                        st.write(f"### {title}")
                        st.image(thumb)
                        st.write(f"https://www.youtube.com/watch?v={v_id}")
                        st.divider()
                else:
                    st.error("YouTube API Key not found in Secrets!")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.warning("Please add your GEMINI_API_KEY to Streamlit Secrets!")
