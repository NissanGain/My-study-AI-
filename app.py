import streamlit as st
import google.generativeai as genai

# Page Config
st.set_page_config(page_title="Smart Study Assistant", page_icon="📚")

# Sidebar for API Key
st.sidebar.title("Settings")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🎓 AI Study Assistant")
    st.write("Ask questions, get board exam predictions, or find study sources.")

    menu = ["Ask a Question", "Predict Important Topics", "Find Study Videos"]
    choice = st.selectbox("What do you want to do?", menu)

    if choice == "Ask a Question":
        user_query = st.text_area("Type your question here:")
        if st.button("Get Answer"):
            response = model.generate_content(f"Explain this clearly for a student: {user_query}")
            st.success(response.text)

    elif choice == "Predict Important Topics":
        subject = st.text_input("Enter Subject (e.g., Science, Math):")
        if st.button("Analyze Predictability"):
            prompt = f"Act as an expert teacher. List top 5 most likely topics to appear in board exams for {subject} and why."
            response = model.generate_content(prompt)
            st.info(response.text)

    elif choice == "Find Study Videos":
        topic = st.text_input("Enter topic for video recommendations:")
        if st.button("Search"):
            # This generates a direct link to YouTube educational searches
            st.write(f"Click here for top-rated videos on {topic}:")
            st.video(f"https://www.youtube.com/results?search_query={topic}+educational+lesson")

else:
    st.warning("Please enter your API Key in the sidebar to start!")
