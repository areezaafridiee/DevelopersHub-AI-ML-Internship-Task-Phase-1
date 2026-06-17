import os
import time 
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError  

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("API Key not found in .env file")
    st.stop()

client = genai.Client(api_key=api_key)
model_name = "gemini-2.5-flash"

st.set_page_config(page_title="MediBuddy | Health AI", page_icon="🩺", layout="centered")

with st.sidebar:
    st.title("🏥 MediBuddy Info")
    st.write("Welcome to your personal AI health guide.")

    st.divider() 

    st.info("💡 **Good topics to ask:**\n- Healthy diet choices\n- Sleep improvements\n- Home remedies for mild cold\n- General exercise tips")

    st.warning("⚠️ **Note:** This assistant cannot replace real medical advice from a doctor.")

st.title("🩺 MediBuddy: Health Assistant")
st.caption("🚀 Powered by Gemini AI | Fast, safe, and helpful information")

st.error("🚨 **If you are experiencing a life-threatening emergency, please call your local emergency services immediately.**")
st.divider()

if "chat" not in st.session_state:
    st.session_state.chat = []

for msg in st.session_state.chat:
    st.chat_message(msg["role"]).write(msg["text"])

danger_words = ["heart attack", "stroke", "breathing problem", "unconscious"]

system_prompt = """
You are a health assistant.
- Only give general health information
- Do NOT diagnose diseases
- Do NOT give medicines
- Always suggest doctor if needed
End with a medical disclaimer.
"""

user_input = st.chat_input("Type your health or wellness question here...")

if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.chat.append({"role": "user", "text": user_input})

    emergency = False

    for word in danger_words:
        if word in user_input.lower():
            emergency = True

    if emergency:
        bot_reply = "🚨 **EMERGENCY DETECTED!** \nPlease stop typing and go to the nearest hospital emergency room or call emergency services immediately."

    else:
        full_prompt = system_prompt + "\nUser: " + user_input

        max_retries = 3
        base_delay = 2
        bot_reply = None

        with st.spinner("🧠 MediBuddy is reviewing medical guidelines..."):
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=full_prompt
                    )
                    bot_reply = response.text
                    break 
                    
                except APIError as e:
                   
                    if e.code == 503 and attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))  
                        continue
                    else:
                        bot_reply = f"❌ **Server Busy:** The AI server is overloaded right now. Please wait a moment and try sending your message again."
                        break
                except Exception as e:
                    bot_reply = f"⚠️ An unexpected error occurred: {str(e)}"
                    break
    st.chat_message("assistant").write(bot_reply)
    st.session_state.chat.append({"role": "assistant", "text": bot_reply})
