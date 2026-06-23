import os
import time 
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import errors
from google.genai.errors import APIError  # Added to catch specific API errors

# ===========================
# 1. LOAD API KEY
# ===========================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("API Key not found in .env file")
    st.stop()

# ===========================
# 2. CONNECT TO GEMINI
# ===========================
client = genai.Client(api_key=api_key)
model_name = "gemini-2.5-flash"

# ===========================
# 3. PAGE SETTINGS (Creative Update)
# ===========================
st.set_page_config(page_title="MediBuddy | Health AI", page_icon="🩺", layout="centered")

# --- SIDEBAR (Creative Add) ---
with st.sidebar:
    st.title("🏥 MediBuddy Info")
    st.write("Welcome to your personal AI health guide.")
    
    # Visual divider line
    st.divider() 
    
    # Safe topics hint box
    st.info("💡 **Good topics to ask:**\n- Healthy diet choices\n- Sleep improvements\n- Home remedies for mild cold\n- General exercise tips")
    
    # Warning box
    st.warning("⚠️ **Note:** This assistant cannot replace real medical advice from a doctor.")

# --- MAIN UI HEADERS ---
st.title("🩺 MediBuddy: Health Assistant")
st.caption("🚀 Powered by Gemini AI | Fast, safe, and helpful information")

# Important safety alert right on top
st.error("🚨 **If you are experiencing a life-threatening emergency, please call your local emergency services immediately.**")
st.divider()

# ===========================
# 4. CHAT HISTORY STORAGE
# ===========================
if "chat" not in st.session_state:
    st.session_state.chat = []

# show previous chat
for msg in st.session_state.chat:
    st.chat_message(msg["role"]).write(msg["text"])

# ===========================
# 5. SIMPLE SAFETY WORDS
# ===========================
danger_words = ["heart attack", "stroke", "breathing problem", "unconscious"]

# ===========================
# 6. SYSTEM RULES (IMPORTANT)
# ===========================
system_prompt = """
You are a health assistant.
- Only give general health information
- Do NOT diagnose diseases
- Do NOT give medicines
- Always suggest doctor if needed
End with a medical disclaimer.
"""

# ===========================
# 7. USER INPUT BOX
# ===========================
user_input = st.chat_input("Type your health or wellness question here...")

if user_input:

    # show user message
    st.chat_message("user").write(user_input)

    # save user message
    st.session_state.chat.append({"role": "user", "text": user_input})

    # ===========================
    # 8. CHECK EMERGENCY
    # ===========================
    emergency = False

    for word in danger_words:
        if word in user_input.lower():
            emergency = True

    if emergency:
        bot_reply = "🚨 **EMERGENCY DETECTED!** \nPlease stop typing and go to the nearest hospital emergency room or call emergency services immediately."

    else:
        # combine prompt
        full_prompt = system_prompt + "\nUser: " + user_input

        # Retry logic configurations
        max_retries = 3
        base_delay = 2
        bot_reply = None

        # ===========================
        # 9. GEMINI RESPONSE WITH RETRY
        # ===========================
        with st.spinner("🧠 MediBuddy is reviewing medical guidelines..."):
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=full_prompt
                    )
                    bot_reply = response.text
                    break  # Success! Break out of the retry loop
                    
                except APIError as e:
                    # Check if error is a 503 Server Unavailable
                    if e.code == 503 and attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))  # Exponential backoff (2s, 4s)
                        continue
                    else:
                        bot_reply = f"❌ **Server Busy:** The AI server is overloaded right now. Please wait a moment and try sending your message again."
                        break
                except Exception as e:
                    bot_reply = f"⚠️ An unexpected error occurred: {str(e)}"
                    break

    # ===========================
    # 10. SHOW BOT RESPONSE
    # ===========================
    st.chat_message("assistant").write(bot_reply)

    # save bot response
    st.session_state.chat.append({"role": "assistant", "text": bot_reply})
