import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Bras AI", page_icon="🟣", layout="centered")

LANGUAGES = [
    "العربية", "English", "Kurdish (Sorani)", "Kurdish (Kurmanji)", "Türkçe", "فارسی", "Español", "Français", "Deutsch", "Italiano",
    "Português", "Русский", "中文 (Mandarin)", "日本語", "한국어", "हिन्दी", "اردو", "বাংলা", "ਪੰਜਾਬੀ", "ગુજરાતી",
    "मराठी", "தமிழ்", "తెలుగు", "ಕನ್ನಡ", "മലയാളം", "ไทย", "Tiếng Việt", "Bahasa Indonesia", "Bahasa Melayu",
    "Filipino", "עברית", "Ελληνικά", "Nederlands", "Svenska", "Norsk", "Dansk", "Suomi", "Polski", "Čeština",
    "Slovenčina", "Magyar", "Română", "Български", "Українська", "Српски", "Hrvatski", "Bosanski", "Shqip", "ქართული",
    "Հայերեն", "Azərbaycan dili", "Қазақша", "Uzbek", "Kiswahili", "Amharic", "Afrikaans", "বাংলা (Bangladesh)",
    "Nepali", "Pashto", "Oʻzbekcha", "Català", "Irish"
]


# Secrets: OPENAI_API_KEY and Google OIDC configuration belong in .streamlit/secrets.toml.
api_key = st.secrets.get("OPENAI_API_KEY", "")

st.title("🟣 Bras AI")
st.caption("مساعد صوتي متعدد اللغات — نسخة تجريبية")

# Google login via Streamlit's built-in OIDC flow; configure secrets before enabling.
if st.button("🔐 تسجيل الدخول بحساب Google", use_container_width=True):
    try:
        st.login("google")
    except Exception:
        st.info("كمّلي إعداد Google OAuth في ملف secrets.toml أولاً، وبعدها فعّلي تسجيل الدخول.")

if st.user.is_logged_in:
    st.success(f"تم تسجيل الدخول: {st.user.get('name', 'Google user')}")
    if st.button("تسجيل خروج"):
        st.logout()

lang = st.selectbox("لغة Bras AI", LANGUAGES, index=0)
st.markdown("### 💬 احچي أو اكتبي إلى Bras")
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

client = OpenAI(api_key=api_key) if api_key else None
text_prompt = st.chat_input("اكتبي رسالتج...")
voice_file = st.audio_input("أو سجّلي صوتج")

if text_prompt or voice_file:
    if not client:
        st.error("ضيفي OPENAI_API_KEY إلى secrets.toml حتى يشتغل Bras AI.")
    else:
        user_text = text_prompt or ""
        if voice_file:
            try:
                transcript = client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",
                    file=(voice_file.name or "voice.wav", voice_file.getvalue(), voice_file.type or "audio/wav")
                )
                user_text = transcript.text
                st.caption(f"فهمت: {user_text}")
            except Exception as e:
                st.error(f"ما قدرت أحوّل الصوت لنص: {e}")
                user_text = ""
        if user_text.strip():
            st.session_state.messages.append({"role": "user", "content": user_text})
            with st.chat_message("user"):
                st.write(user_text)
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": f"You are Bras AI, a friendly multilingual voice assistant. Reply in {lang} unless the user asks otherwise. Keep replies conversational and clear."},
                        *st.session_state.messages[-20:]
                    ]
                )
                answer = response.choices[0].message.content or ""
                st.session_state.messages.append({"role": "assistant", "content": answer})
                with st.chat_message("assistant"):
                    st.write(answer)
                try:
                    speech = client.audio.speech.create(model="gpt-4o-mini-tts", voice="alloy", input=answer)
                    st.audio(speech.content, format="audio/mp3")
                except Exception:
                    st.caption("الرد النصي جاهز؛ تعذّر توليد الصوت في هالمحاولة.")
            except Exception as e:
                st.error(f"صار خطأ بالرد: {e}")

st.divider()
st.subheader("🔔 الإشعارات — جاهزة للمرحلة القادمة")
st.info("هذي النسخة تعرض واجهة الإعداد فقط. قراءة إشعارات واتساب/سناب/تيك توك فعلياً تحتاج تطبيق مرافق وصلاحيات الجهاز؛ ما تشتغل من Streamlit وحده.")
if st.checkbox("عرض لوحة إعداد الإشعارات (تجريبية)"):
    st.write("مصادر الإشعارات المخطط دعمها: WhatsApp · Snapchat · TikTok · Telegram · SMS")
    st.caption("هذه الخيارات حالياً شكلية، ولا تقرأ إشعارات حقيقية أو ترسل ردود.")
