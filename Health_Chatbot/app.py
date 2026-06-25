import os
import time
import re
from html import escape
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
# Load configuration variables from your hidden environment file (.env)
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Stop everything if the API key wasn't found in your folder setup
if not api_key:
    st.error("❌ GEMINI_API_KEY missing in .env file")
    st.stop()

# Initialize the official Google GenAI client module
client = genai.Client(api_key=api_key)
MODEL_NAME = "gemini-2.5-flash"
st.set_page_config(
    page_title="MediBuddy AI",
    page_icon="🩺",
    layout="centered"
)
# Initialize global application memories if they don't exist yet
if "messages" not in st.session_state:
    st.session_state.messages = []  # Keeps track of chat history lists

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None  # Tracks which specific text block is being edited
st.markdown(
"""
<style>
/* Forces the app body layout container to match system dark/light modes */
.stApp { background-color: var(--background-color) !important; }
[data-testid="stHeader"] { background-color: transparent !important; }
div[data-testid="stBottomBlockContainer"] { background-color: transparent !important; }

/* Custom Side-panel adjustments */
[data-testid="stSidebar"] { background-color: var(--secondary-background-color) !important; }
[data-testid="stSidebarCollapseButton"] button { color: var(--text-color) !important; }

/* Main layout wrapper frames for aligning chat responses */
.chat-container {
    width: 100%;
    margin: 0.5rem 0;
    display: flex;
    flex-direction: column;
}
.chat-container.user-align { align-items: flex-end; } /* Pushes User content rightward */
.chat-container.bot-align { align-items: flex-start; }   /* Pushes Bot content leftward */

/* Beautiful structural shapes for conversational elements */
.custom-bubble {
    padding: 0.9rem 1.2rem;
    border-radius: 16px;
    font-size: 0.98rem;
    line-height: 1.5;
    max-width: 80%;
    word-wrap: break-word;
}

/* User Bubble Styles (Permanent Lovely Lavender) */
.custom-bubble.user-bubble {
    background-color: #7c5cd4 !important;
    color: #ffffff !important;
    border-bottom-right-radius: 4px;
    text-align: left;
}

/* Bot Bubble Styles (Adapts its lighting depending on browser configurations) */
.custom-bubble.bot-bubble {
    background-color: var(--secondary-background-color) !important;
    color: var(--text-color) !important;
    border: 1px solid rgba(124, 92, 212, 0.2) !important;
    border-bottom-left-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

/* Inner block text item adjustments */
.custom-bubble p, .custom-bubble li {
    margin: 0.3rem 0 !important;
}
</style>
""",
unsafe_allow_html=True
)
with st.sidebar:
    st.header("🏥 MediBuddy Panel")
    st.info("Ask about:\n- Healthy lifestyle\n- Diet & nutrition\n- Exercise tips\n- Basic health awareness")
    st.warning("⚠️ Not a medical diagnosis tool.")
    
    # Completely clear the chat storage when the user taps this action button
    if st.button("🔄 Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.edit_index = None
        st.rerun()

EMERGENCY_WORDS = ["heart attack", "stroke", "breathing problem", "unconscious", "severe pain"]
SYSTEM_PROMPT = "You are MediBuddy AI. Provide general health advice. Do not diagnose or prescribe medicine. Keep answers friendly."

def is_emergency(user_text):
    """Returns True if any critical keyword matches the conversation text phrase."""
    return any(word in user_text.lower() for word in EMERGENCY_WORDS)

def generate_ai_reply(prompt_content):
    """Communicates directly with Google Gemini servers to safely generate responses."""
    if is_emergency(prompt_content):
        return "🚨 Emergency detected! Please contact emergency services immediately."
    
    full_combined_prompt = f"{SYSTEM_PROMPT}\nUser: {prompt_content}"
    
    with st.spinner("🧠 Thinking..."):
        # Attempt to request answers up to 3 times if server timeouts happen
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME, 
                    contents=full_combined_prompt
                )
                return response.text
            except APIError:
                time.sleep(2 ** attempt)  # Wait slightly longer before trying again
            except Exception:
                break
    return "⚠️ Server busy or unexpected error. Please try again."

def format_text_to_html(raw_markdown_text):
    """Converts common conversational text markers safely into robust standard web markup."""
    # Step A: Clean characters to secure layout structures safely
    secure_html_text = escape(raw_markdown_text)
    
    # Step B: Turn text highlighted with **bold flags** into strong elements
    secure_html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', secure_html_text)
    
    # Step C: Turn list elements marked with dashes "-" into cleanly formatted list lines
    secure_html_text = re.sub(r'(?m)^-\s+(.*)$', r'<li>\1</li>', secure_html_text)
    
    # Step D: Process lines breaks correctly to handle clean block structures without blank lines
    final_html_output = secure_html_text.replace('\n\n', '</p><p>').replace('\n', '<br>')
    return ("<p>{final_html_output}</p>")
    
st.title("🩺 MediBuddy AI")
st.caption("Your friendly AI health assistant")
st.divider()
for current_index, message_item in enumerate(st.session_state.messages):
    if (
        message_item["role"] == "user"
        and st.session_state.edit_index == current_index
    ):
        with st.form(key=f"editing_input_form_{current_index}"):
            updated_text = st.text_input(
                "Edit message:",
                value=message_item["content"]
            )
            resend_column, cancel_column = st.columns(2)
            if resend_column.form_submit_button(
                "Resend 💾",
                use_container_width=True
            ):
                # Remove everything after this message
                st.session_state.messages = st.session_state.messages[:current_index]
                # Save edited message
                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": updated_text,
                    }
                )
                st.session_state.edit_index = None
                
                # Generate fresh reply
                updated_reply = generate_ai_reply(updated_text)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": updated_reply,
                    }
                )
                st.rerun()
            if cancel_column.form_submit_button(
                "Cancel ❌",
                use_container_width=True
            ):
                st.session_state.edit_index = None
                st.rerun()
    else:
        is_user_role = message_item["role"] == "user"
        alignment_class = (
            "user-align" if is_user_role else "bot-align"
        )
        bubble_theme_class = (
            "user-bubble" if is_user_role else "bot-bubble"
        )
        formatted_html_content = format_text_to_html(
            message_item["content"]
        )
        st.markdown(
            f"""
            <div class="chat-container {alignment_class}">
                <div class="custom-bubble {bubble_theme_class}">
                    {formatted_html_content}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if is_user_role:
            spacer_column, edit_column, copy_column = st.columns(
                [7, 1.5, 1.5]
            )
            if edit_column.button(
                "✏️ Edit",
                key=f"edit_btn_{current_index}",
                use_container_width=True,
            ):
                st.session_state.edit_index = current_index
                st.rerun()

            if copy_column.button(
                "📋 Copy",
                key=f"copy_user_btn_{current_index}",
                use_container_width=True,
            ):
                st.code(
                    message_item["content"],
                    language="text",
                )
        else:

            retry_column, copy_column, spacer_column = st.columns(
                [1.5, 1.5, 7]
            )
            if retry_column.button(
                "🔄 Retry",
                key=f"retry_btn_{current_index}",
                use_container_width=True,
            ):
                previous_user_text = st.session_state.messages[
                    current_index - 1
                ]["content"]

                # Remove current assistant response
                st.session_state.messages = (
                    st.session_state.messages[:current_index]
                )
                regenerated_reply = generate_ai_reply(
                    previous_user_text
                )
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": regenerated_reply,
                    }
                )
                st.rerun()
            if copy_column.button(
                "📋 Copy",
                key=f"copy_bot_btn_{current_index}",
                use_container_width=True,
            ):
                st.code(
                    message_item["content"],
                    language="text",
                )
    st.divider()
new_user_input = st.chat_input("Ask your health question...")
if new_user_input:
    st.session_state.messages.append({"role": "user", "content": new_user_input})
    ai_bot_response = generate_ai_reply(new_user_input)
    st.session_state.messages.append({"role": "assistant", "content": ai_bot_response})
    st.rerun()
