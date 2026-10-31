
import streamlit as st
from google import genai
from ddgs import DDGS
import os

# ==========================================
# 💜 BRAS AI
# Created & Developed by BRAS AI Team
# ==========================================

st.set_page_config(
    page_title="BRAS AI",
    page_icon="💜",
    layout="wide"
)

# -------- PREMIUM DESIGN --------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#080711,#151020);
    color: white;
}
section[data-testid="stSidebar"] {
    background: #100c1b;
}
h1,h2,h3 {
    color: #c7a1ff !important;
}
.stChatMessage {
    background: #1b1428;
    border: 1px solid #65418c;
    border-radius: 15px;
}
.stButton button {
    background: #7543b5;
    color: white;
    border-radius: 12px;
    border: 1px solid #a77bdb;
}
</style>
""", unsafe_allow_html=True)

# -------- LANGUAGES --------

LANGUAGES = {
    "العربية": "Arabic",
    "الكردية البادينية": "Kurdish Badini / Kurmanji",
    "English": "English",
    "Türkçe": "Turkish"
}

# -------- SIDEBAR --------

st.sidebar.title("💜 BRAS AI")

language = st.sidebar.selectbox(
    "🌍 Language / اللغة",
    list(LANGUAGES.keys())
)

st.sidebar.markdown("---")
st.sidebar.subheader("📚 Knowledge Center")

topics = [
    "Mathematics",
    "Geography",
    "Science",
    "History",
    "Physics",
    "Chemistry",
    "Biology",
    "Programming",
    "Technology",
    "Artificial Intelligence",
    "Languages",
    "Space",
    "General Knowledge"
]

for topic in topics:
    st.sidebar.write("• " + topic)

st.sidebar.markdown("---")

web_enabled = st.sidebar.checkbox(
    "🌐 Enable Internet Search",
    value=True
)

if st.sidebar.button("🗑️ New Conversation"):
    st.session_state.messages = []
    st.rerun()

# -------- HEADER --------

st.title("💜 BRAS AI")
st.caption("Your Own AI. Your Own Identity.")

st.markdown(
    "### Welcome to Bras AI"
)

# -------- API KEY --------

def get_api_key():
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return os.getenv("GEMINI_API_KEY", "")

api_key = get_api_key()

# -------- SESSION MEMORY --------

if "messages" not in st.session_state:
    st.session_state.messages = []

# -------- AI INSTRUCTIONS --------

SYSTEM_PROMPT = """
You are BRAS AI, an educational and multilingual AI assistant.

SUPPORTED LANGUAGES:
1. Arabic
2. Kurdish Badini / Kurmanji
3. English
4. Turkish

MAIN KNOWLEDGE AREAS:
- Mathematics and algebra
- Geometry and statistics
- Geography and countries
- History and civilizations
- Physics and chemistry
- Biology and environment
- Space and astronomy
- Programming and computers
- Artificial intelligence
- Languages and translation
- Education and general knowledge

IMPORTANT RULES:
1. Answer in the language selected by the user.
2. Understand all four supported languages.
3. Explain difficult subjects step by step.
4. Give examples when helpful.
5. Never invent facts, references or sources.
6. Clearly state when information is uncertain.
7. Use provided web search results when relevant.
8. Distinguish current information from older knowledge.
9. Protect user privacy.
10. Do not reveal API keys or private information.
11. For health questions, provide general educational
    information, not personal diagnosis.
12. Be friendly, respectful and clear.
13. Do not claim to know everything.
"""

# -------- INTERNET SEARCH --------

def search_web(query):
    results = []

    try:
        with DDGS() as search:
            found = search.text(
                query,
                max_results=5
            )

            for item in found:
                results.append({
                    "title": item.get("title", ""),
                    "body": item.get("body", ""),
                    "url": item.get("href", "")
                })

    except Exception:
        return []

    return results


# -------- CHAT DISPLAY --------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -------- USER INPUT --------

question = st.chat_input(
    "Ask Bras AI anything... 💜"
)

if question:

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):

        if not api_key:

            answer = (
                "💜 Welcome to Bras AI!\n\n"
                "The AI engine is not connected yet.\n"
                "Please configure the Gemini API key "
                "in Streamlit Secrets."
            )

            st.warning(answer)

        else:

            try:
                client = genai.Client(
                    api_key=api_key
                )

                web_results = []

                # Search when current information
                # or additional sources are useful.
                if web_enabled:
                    with st.spinner(
                        "🌐 Searching for information..."
                    ):
                        web_results = search_web(question)

                search_context = ""

                if web_results:
                    search_context = (
                        "\n\nWEB SEARCH RESULTS:\n"
                    )

                    for index, item in enumerate(
                        web_results, 1
                    ):
                        search_context += (
                            f"\nSource {index}: "
                            f"{item['title']}\n"
                            f"Information: {item['body']}\n"
                            f"URL: {item['url']}\n"
                        )

                contents = []

                for msg in st.session_state.messages[-20:]:
                    contents.append({
                        "role": (
                            "user"
                            if msg["role"] == "user"
                            else "model"
                        ),
                        "parts": [{
                            "text": msg["content"]
                        }]
                    })

                contents[-1]["parts"][0]["text"] += (
                    "\n\nSelected response language: "
                    + LANGUAGES[language]
                    + search_context
                    + "\nUse sources carefully. "
                    "Do not pretend to have verified "
                    "information that you cannot verify."
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config={
                        "system_instruction": SYSTEM_PROMPT
                    }
                )

                answer = (
                    response.text
                    or "I couldn't generate an answer."
                )

                st.markdown(answer)

                if web_results:
                    with st.expander(
                        "🌐 Information sources"
                    ):
                        for item in web_results:
                            st.markdown(
                                f"- [{item['title']}]"
                                f"({item['url']})"
                            )

            except Exception as error:
                answer = (
                    "Sorry, an error occurred. "
                    "Please check the API configuration "
                    "and try again."
                )

                st.error(answer)

                # Do not expose secrets or internal
                # exception details to users.

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

# -------- FOOTER --------

st.sidebar.markdown("---")
st.sidebar.caption("💜 BRAS AI")
st.sidebar.caption("Independent AI Assistant")
