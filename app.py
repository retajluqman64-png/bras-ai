
import streamlit as st
import os

# =====================================
# BRAS AI - Multilingual AI Assistant
# =====================================

st.set_page_config(
    page_title="BRAS AI",
    page_icon="💜",
    layout="wide"
)

# Premium design
st.markdown("""
<style>
.stApp {
    background: #090812;
    color: white;
}
section[data-testid="stSidebar"] {
    background: #151020;
}
h1, h2, h3 {
    color: #c7a5ff;
}
.stChatMessage {
    background: #171326;
    border: 1px solid #49336a;
    border-radius: 15px;
}
.stButton button {
    background: #7543b5;
    color: white;
    border-radius: 12px;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# Language selection
LANGUAGES = {
    "العربية": "Arabic",
    "الكردية البادينية": "Kurdish Badini / Kurmanji",
    "English": "English",
    "Türkçe": "Turkish"
}

st.sidebar.title("💜 BRAS AI")

language = st.sidebar.selectbox(
    "Choose your language",
    list(LANGUAGES.keys())
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Knowledge Center")

topics = [
    "Mathematics",
    "Geography",
    "Science",
    "History",
    "Technology",
    "Programming",
    "Languages",
    "General Knowledge"
]

st.sidebar.write("\n".join("• " + x for x in topics))

st.title("💜 BRAS AI")
st.caption("Your Own AI. Your Own Identity.")

st.markdown(
    "Welcome to Bras AI. Ask me about anything!"
)

# API configuration
api_key = st.secrets.get(
    "GEMINI_API_KEY",
    os.getenv("GEMINI_API_KEY", "")
)

# Conversation memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# AI instructions
SYSTEM_PROMPT = """
You are BRAS AI, a helpful multilingual AI assistant.

Supported languages:
1. Arabic
2. Kurdish Badini / Kurmanji
3. English
4. Turkish

Rules:
- Respond in the user's selected language.
- Understand questions in all supported languages.
- Explain mathematics step by step.
- Help with geography, science, history,
  programming, technology and education.
- Give accurate and clear answers.
- Never invent facts or sources.
- Admit when you do not know an answer.
- Protect user privacy.
- Do not reveal API keys or secrets.
- Be friendly, respectful and educational.
- Distinguish established facts from uncertainty.
- Do not claim to know every fact on Earth.
"""

# Show previous conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_input = st.chat_input("Ask Bras AI anything...")

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        if not api_key:
            answer = (
                "Welcome to Bras AI! 💜\n\n"
                "The AI engine is not connected yet. "
                "Please configure GEMINI_API_KEY "
                "in Streamlit Secrets."
            )
            st.markdown(answer)

        else:
            try:
                from google import genai

                client = genai.Client(api_key=api_key)

                history = []
                for msg in st.session_state.messages[-21:]:
                    history.append({
                        "role": (
                            "user" if msg["role"] == "user"
                            else "model"
                        ),
                        "parts": [{"text": msg["content"]}]
                    })

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=history,
                    config={
                        "system_instruction": (
                            SYSTEM_PROMPT
                            + "\nSelected language: "
                            + LANGUAGES[language]
                        )
                    }
                )

                answer = response.text
                st.markdown(answer)

            except Exception:
                answer = (
                    "Sorry, I couldn't complete that request. "
                    "Please check the AI configuration."
                )
                st.error(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

# Clear chat
if st.sidebar.button("New Conversation"):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("BRAS AI © Your Own AI Project")
