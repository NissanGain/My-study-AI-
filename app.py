import streamlit as st
from google import genai
from googleapiclient.discovery import build

# 1. Setup API Keys from Secrets
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
YOUTUBE_KEY = st.secrets.get("YOUTUBE_API_KEY")

# 2. Function to search YouTube
def get_youtube_videos(query):
    if not YOUTUBE_KEY:
        return None
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_KEY)
    request = youtube.search().list(
        q=query + " class 10 boards educational ncert",
        part='snippet',
        maxResults=3,
        type='video'
    )
    return request.execute()

# 3. Page Setup
st.set_page_config(page_title="AI Study Master 2026", page_icon="🎓")
st.title("🎓 AI Study Master 2026")

if GEMINI_KEY:
    try:
        # Initializing the new 2026 Client
        client = genai.Client(api_key=GEMINI_KEY)
        
        menu = ["Ask a Question", "Predict Board Topics", "Recommended Videos"]
        choice = st.sidebar.selectbox("Choose a Feature", menu)

        if choice == "Ask a Question":
            user_query = st.text_input("What is your doubt? (e.g. Concave vs Convex lens)")
            if st.button("Get Expert Answer"):
                # Using the newest Gemini 2.5 Flash model
                response = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=f"Explain this clearly for a Class 10 student: {user_query}"
                )
                st.write("### 🤖 AI Tutor says:")
                st.info(response.text)

        elif choice == "Predict Board Topics":
            subject = st.text_input("Enter Subject (e.g. Science, Math):")
            if st.button("Analyze Patterns"):
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"Predict the 5 most important topics for {subject} in Class 10 board exams based on recent patterns."
                )
                st.success(response.text)

        elif choice == "Recommended Videos":
            topic = st.text_input("Enter topic for video lessons:")
            if st.button("Find Videos"):
                results = get_youtube_videos(topic)
                if results:
                    for item in results['items']:
                        title = item['snippet']['title']
                        v_id = item['id']['videoId']
                        st.write(f"📺 **{title}**")
                        st.video(f"https://www.youtube.com/watch?v={v_id}")
                        st.divider()
                else:
                    st.error("Please add your YOUTUBE_API_KEY to Secrets first!")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.warning("Please add your GEMINI_API_KEY to Streamlit Secrets!")
