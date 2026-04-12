import streamlit as st
import google.generativeai as genai

# 1. Look for the secret key
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    # This is a backup in case the secret isn't set
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

# 2. Setup the AI if the key exists
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        st.title("🎓 AI Study Assistant")
        
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
                prompt = f"Act as an expert teacher. Based on common board exam patterns, list top 5 high-probability topics for {subject}."
                response = model.generate_content(prompt)
                st.info(response.text)

        elif choice == "Find Study Videos":
            topic = st.text_input("Enter topic for video search:")
            if st.button("Search"):
                st.write(f"Click below to search for lessons on {topic}:")
                # This creates a clickable link for your friends
                st.markdown(f"[Click here to open YouTube Results](https://www.youtube.com/results?search_query={topic}+class+10+educational)")

    except Exception as e:
        st.error(f"Something went wrong: {e}")
else:
    st.warning("Waiting for API Key connection...")
