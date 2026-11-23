import base64
from datetime import datetime, timedelta
import json
import re
from openai import OpenAI
import streamlit as st

st.set_page_config(
    page_title="BRAS AI - المنصة الشاملة الذكية",
    page_icon="💜",
    layout="wide",
)

TODAY_STR = datetime.now().strftime("%Y-%m-%d")

AUTHORIZED_ACCOUNTS = {
    "retaj@brasai.com": {
        "password": "Retaj@2026",
        "username": "ريتاج لقمان أسماعيل",
    },
    "user1@brasai.com": {
        "password": "BrasUser#1",
        "username": "مستخدم 1",
    },
    "user2@brasai.com": {
        "password": "BrasUser#2",
        "username": "مستخدم 2",
    },
}

defaults = {
    "logged_in": False,
    "is_subscribed": False,
    "subscription_plan": None,
    "trial_start": None,
    "username": "",
    "user_email": "",
    "theme": "داكن (Dark)",
    "voice": "صوت بنت نقي وواضح (Nova)",
    "language": "العربية (Arabic)",
    "screen_mode": "عادي (Normal)",
    "selected_section": None,
    "my_schedule": [],
    "section_messages": {},
    "section_memory": {},
    "archives": [],
    "saved_chats": [],
    "browsing_archive": None,
    "messages": [],
    "generated_videos": [],
    "processed_audio_ids": [],
    "processed_upload_ids": [],
    "pending_image_b64": None,
    "pending_image_mime": None,
    "pending_image_name": None,
    "free_messages_used": 0,
    "free_allowed_sections": [],
    "free_daily_date": TODAY_STR,
    "free_daily_images_used": 0,
    "free_daily_videos_used": 0,
    "latest_voice_text": None,
}

FREE_MSG_LIMIT = 25
FREE_SECTION_LIMIT = 2
FREE_DAILY_IMAGE_LIMIT = 4
FREE_DAILY_VIDEO_LIMIT = 1
FREE_DAILY_TASK_LIMIT = 1
FREE_WEEKLY_TASK_LIMIT = 3

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

if st.session_state.free_daily_date != TODAY_STR:
    st.session_state.free_daily_date = TODAY_STR
    st.session_state.free_daily_images_used = 0
    st.session_state.free_daily_videos_used = 0


def is_valid_email(email_str: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email_str.strip()))


lang = st.session_state.language
is_screen_mode = (
    "شاشة" in st.session_state.screen_mode
    or "Screen" in st.session_state.screen_mode
)

if "English" in lang:
    t_title = "💜 BRAS AI - Smart Comprehensive Platform 💜"
    t_login_title = "🔐 Sign In with Your Existing Password"
    t_email = "Email:"
    t_password = "Password:"
    t_login_btn = "Sign In"
    t_logout_btn = "Logout"
    t_nav = "Navigate Your Platform:"
    t_sec_main = "🏠 Main Grid (Sections)"
    t_sec_schedule = "📅 Schedule & Reminders"
    t_sec_chats = "💬 Saved Chats"
    t_sec_pricing = "💳 Plans & Pricing"
    t_sec_archive = "📚 Saved Archives"
    t_sec_settings = "⚙️ BRAS AI & Account Settings"
    t_account = "Account"
    t_lang_label = "App Language"
    t_theme = "Theme"
    t_voice = "Voice"
    t_screen_mode = "Screen Mode"
    t_settings_header = "⚙️ Settings"
    t_username = "Username:"
    t_save = "Save Settings & Apply Changes"
    t_saved_ok = "Settings saved and language applied successfully!"
    t_schedule_title = "📅 Your Schedule & Smart Reminders"
    t_task_input = "Enter task (e.g., Math exam or family visit):"
    t_day_label = "Select Day:"
    t_time_label = "Time (e.g., 4:00 PM):"
    t_add_task_btn = "Add Task to Schedule"
    t_task_added = "Task added to your schedule!"
    t_schedule_list = "📌 Your Schedule & Recorded Tasks:"
    t_choose_sec = "Choose the right section to start creating:"
    t_back_grid = "⬅️ Back to Grid"
    t_new_chat = "✨ New Chat"
    t_archive_btn = "💾 Save & Archive"
    t_archived_ok = "Conversation archived successfully!"
    t_exit_arch = "↩️ Exit Archive View"
    t_file_upload = "➕ Add Image or File"
    t_archive_header = "📚 Archives"
    t_no_archive = "No archived conversations."
    t_browse = "📖 Browse"
    ads_sec_key = "Ads & Stores Studio"
    SECTIONS_NAMES = {
        "المساعد الشامل": "Comprehensive Assistant",
        "المعلم الشامل": "School Teacher",
        "قسم كرة القدم": "Football (FC Barcelona)",
        "تعليم اللغات": "Languages Tutor",
        "البرمجة": "Programming",
        "الطبخ والوصفات": "Cooking & Recipes",
        "مكياج وسكين كير": "Makeup & Skincare",
        "ديزاين وملابس وشوبينغ": "Fashion & Shopping",
        "أفكار دول وسفرات": "Travel & Trip Planner",
        "قسم التاريخ": "History Expert",
        "الصحة، الدايت والجيم": "Fitness & Health",
        "نصائح وتطوير الذات": "Life Advisor",
        ads_sec_key: "Ads & Stores Studio",
        "صانع الفيديوهات والأفكار": "Video & Ideas Studio",
    }
elif "Kurdish" in lang:
    t_title = "💜 BRAS AI - سەکۆی گشتگیری هۆشمەند 💜"
    t_login_title = "🔐 چوونەژوورەوە بە وشەی نهێنی هەژمارەکەت"
    t_email = "ئیمەیڵ:"
    t_password = "وشەی نهێنی:"
    t_login_btn = "چوونە ژوورەوە"
    t_logout_btn = "چوونە دەرەوە"
    t_nav = "گه‌شت بكه‌ له‌ سەکۆکەت:"
    t_sec_main = "🏠 تۆڕی سەرەکی (بەشەکان)"
    t_sec_schedule = "📅 خشتە و بیرخەرەوەکان"
    t_sec_chats = "💬 گفتوگۆ پاشەکەوتکراوەکان"
    t_sec_pricing = "💳 پاکێج و نرخەکان"
    t_sec_archive = "📚 ئەرشیفی گفتوگۆکان"
    t_sec_settings = "⚙️ ڕێکخستنەکانی BRAS AI"
    t_account = "هەژمار"
    t_lang_label = "زمانی بەرنامە"
    t_theme = "ڕوکار"
    t_voice = "دەنگ"
    t_screen_mode = "دۆخی شاشە (Screen Mode)"
    t_settings_header = "⚙️ ڕێکخستنەکان"
    t_username = "ناوی بەکارهێنەر:"
    t_save = "پاشەکەوتکردنی ڕێکخستنەکان"
    t_saved_ok = "ڕێکخستنەکان بە سەرکەوتوویی پاشەکەوت کران!"
    t_schedule_title = "📅 خشتەی ئەرکەکان و بیرخەرەوە"
    t_task_input = "ئەرکێک بنووسە:"
    t_day_label = "ڕۆژ هەڵبژێرە:"
    t_time_label = "کات:"
    t_add_task_btn = "زیادکردنی ئەرک بۆ خشتە"
    t_task_added = "ئەرکەکە زیادکرا!"
    t_schedule_list = "📌 خشتەی ئەرکە تۆمارکراوەکانت:"
    t_choose_sec = "بەشی گونجاو هەڵبژێرە بۆ دەستپێکردن:"
    t_back_grid = "⬅️ گەڕانەوە بۆ تۆڕ"
    t_new_chat = "✨ گفتوگۆی نوێ"
    t_archive_btn = "💾 پاشەکەوت و ئەرشیف"
    t_archived_ok = "گفتوگۆکە ئەرشیف کرا!"
    t_exit_arch = "↩️ دەرچوون لە ئەرشیف"
    t_file_upload = "➕ زیادکردنی وێنە یان فایل"
    t_archive_header = "📚 ئەرشیف"
    t_no_archive = "هیچ گفتوگۆیەکی ئەرشیفکراو نییە."
    t_browse = "📖 پشکنین"
    ads_sec_key = "ستۆدیۆی ڕیکلام و بازاڕەکان"
    SECTIONS_NAMES = {
        "المساعد الشامل": "یاریدەدەری گشتی",
        "المعلم الشامل": "مامۆستای قوتابخانە",
        "قسم كرة القدم": "تۆپی پێ (بارسێلۆنا)",
        "تعليم اللغات": "فێربوونی زمانەکان",
        "البرمجة": "بەرمەسازی",
        "الطبخ والوصفات": "چێشتلێنان",
        "مكياج وسكين كير": "مکیاژ و چاودێری پێست",
        "ديزاين وملابس وشوبينغ": "فاشیۆن و بازاڕکردن",
        "أفكار دول وسفرات": "پلانی گەشتکردن",
        "قسم التاريخ": "مێژوونووس",
        "الصحة، الدايت والجيم": "تەندروستی و لەشجوانی",
        "نصائح وتطوير الذات": "پەرەپێدانی خۆی",
        ads_sec_key: "ستۆدیۆی ڕیکلام و بازاڕەکان",
        "صانع الفيديوهات والأفكار": "ستۆدیۆی ڤیدیۆ و بیرۆکەکان",
    }
else:
    t_title = "💜 BRAS AI - المنصة الشاملة الذكية 💜"
    t_login_title = "🔐 تسجيل الدخول بكلمة سر الحساب"
    t_email = "البريد الإلكتروني:"
    t_password = "كلمة السر:"
    t_login_btn = "دخول المنصة"
    t_logout_btn = "تسجيل الخروج"
    t_nav = "📍 تنقلي في منصتكِ:"
    t_sec_main = "🏠 الشبكة الرئيسية (الأقسام)"
    t_sec_schedule = "📅 الجدول والتذكير"
    t_sec_chats = "💬 سجل الدردشة الكاملة"
    t_sec_pricing = "💳 الباقات والاشتراك"
    t_sec_archive = "📚 أرشيف المحادثات المحفوظة"
    t_sec_settings = "⚙️ إعدادات BRAS AI والحساب"
    t_account = "الحساب"
    t_lang_label = "🌐 لغة التطبيق وتفضيل المحادثة (أكثر من 40 لغة):"
    t_theme = "المظهر:"
    t_voice = "الصوت:"
    t_screen_mode = "🖥️ وضع الشاشة (Screen Mode):"
    t_settings_header = "🎛️ الإعدادات"
    t_username = "اسم المستخدم:"
    t_save = "💾 حفظ الإعدادات وتطبيق التغييرات"
    t_saved_ok = "تم حفظ الإعدادات وتطبيق اللغة بنجاح!"
    t_schedule_title = "📅 جدول المواعيد والمهمات والتذكير"
    t_task_input = "اكتبي المهمة أو الموعد (مثلاً: امتحان رياضيات أو موعد طبيب):"
    t_day_label = "اختر اليوم:"
    t_time_label = "الساعة:"
    t_add_task_btn = "إضافة إلى الجدول"
    t_task_added = "تمت إضافة الموعد إلى جدولكِ!"
    t_schedule_list = "📌 جدول مواعيدكِ ومهامكِ المسجلة:"
    t_choose_sec = "اخترِ القسم المناسب لبدء الإبداع:"
    t_back_grid = "⬅️ العودة للشبكة"
    t_new_chat = "✨ محادثة جديدة"
    t_archive_btn = "💾 حفظ وأرشفة"
    t_archived_ok = "تمت أرشفة المحادثة بنجاح!"
    t_exit_arch = "↩️ الخروج من الأرشيف"
    t_file_upload = "➕ إضافة صورة أو ملف"
    t_archive_header = "📚 الأرشيف"
    t_no_archive = "لا توجد محادثات مؤرشفة."
    t_browse = "📖 استعراض"
    ads_sec_key = "قسم الإعلانات والمتاجر"
    SECTIONS_NAMES = {
        "المساعد الشامل": "المساعد الشامل",
        "المعلم الشامل": "المعلم الشامل",
        "قسم كرة القدم": "قسم كرة القدم",
        "تعليم اللغات": "تعليم اللغات",
        "البرمجة": "البرمجة",
        "الطبخ والوصفات": "الطبخ والوصفات",
        "مكياج وسكين كير": "مكياج وسكين كير",
        "ديزاين وملابس وشوبينغ": "ديزاين وملابس وشوبينغ",
        "أفكار دول وسفرات": "أفكار دول وسفرات",
        "قسم التاريخ": "قسم التاريخ",
        "الصحة، الدايت والجيم": "الصحة، الدايت والجيم",
        "نصائح وتطوير الذات": "نصائح وتطوير الذات",
        ads_sec_key: "قسم الإعلانات والمتاجر",
        "صانع الفيديوهات والأفكار": "صانع الفيديوهات والأفكار",
    }

is_dark = "داكن" in st.session_state.theme or "Dark" in st.session_state.theme
bg_color = "#0b0b0d" if is_dark else "#ffffff"
text_color = "#ffffff" if is_dark else "#111111"
muted_text = "#e5e5ea" if is_dark else "#222222"
card_bg = "#17171c" if is_dark else "#f5f5f7"
input_bg = "#1f1f26" if is_dark else "#ffffff"
border_color = "#9b5de5"
accent_color = "#c084fc" if is_dark else "#6b21a8"

container_max_width = "100%" if is_screen_mode else "1240px"
block_padding = "1rem 1.4rem" if is_screen_mode else "1.5rem 2.2rem"
btn_height = "125px" if is_screen_mode else "110px"
btn_font = "1.18rem" if is_screen_mode else "1.06rem"

st.markdown(
    f"""
<style>
.stApp, [data-testid="stAppViewContainer"] {{
    background-color: {bg_color} !important;
    color: {text_color} !important;
}}
[data-testid="stHeader"] {{
    background-color: transparent !important;
}}
[data-testid="stSidebar"] {{
    background-color: {card_bg} !important;
    color: {text_color} !important;
}}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
label, .stRadio label, .stCheckbox label, .stSelectbox label,
.stTextInput label, .stTextArea label,
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] span, [data-testid="stChatMessage"] div {{
    color: {text_color} !important;
    opacity: 1 !important;
}}
.stCaption, [data-testid="stCaptionContainer"] {{
    color: {muted_text} !important;
    opacity: 1 !important;
}}
.stTextInput input, .stTextArea textarea,
[data-baseweb="select"] > div,
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {{
    background-color: {input_bg} !important;
    color: {text_color} !important;
    border-color: {border_color} !important;
}}
[data-testid="stChatInput"] button,
[data-testid="stChatInput"] svg {{
    color: {text_color} !important;
    fill: {text_color} !important;
}}
[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] input::placeholder,
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {{
    color: {muted_text} !important;
    opacity: 0.85 !important;
}}
.stButton > button {{
    background-color: {card_bg} !important;
    color: {text_color} !important;
    border: 1.5px solid {border_color} !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
}}
.stButton > button:hover {{
    background-color: #9333ea !important;
    color: #ffffff !important;
    border-color: #f472b6 !important;
}}
.main .block-container {{
    max-width: {container_max_width};
    padding: {block_padding};
}}
.main-title {{
    text-align: center;
    color: {accent_color} !important;
    font-weight: bold;
    font-size: {"2.8rem" if is_screen_mode else "2.35rem"};
    margin-bottom: 16px;
}}
.user-info {{
    background-color: {card_bg};
    color: {text_color} !important;
    padding: 14px 18px;
    border-radius: 15px;
    border: 1.5px solid {border_color};
    margin-bottom: 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}}
.grid-card-wrap .stButton > button {{
    width: 100%;
    min-height: {btn_height};
    background-color: {card_bg} !important;
    color: {text_color} !important;
    border: 2px solid {border_color} !important;
    border-radius: 20px !important;
    font-size: {btn_font};
    font-weight: bold;
    line-height: 1.4;
    padding: 14px 12px;
    transition: 0.25s ease;
    box-shadow: 0 4px 15px rgba(155, 93, 229, 0.22);
}}
.grid-card-wrap .stButton > button:hover {{
    background-color: #9333ea !important;
    color: #ffffff !important;
    border-color: #f472b6 !important;
    transform: translateY(-2px);
}}
.plan-box {{
    background-color: {card_bg};
    color: {text_color} !important;
    padding: 18px;
    border-radius: 16px;
    border: 1.5px solid {border_color};
    margin-bottom: 12px;
}}
.settings-panel {{
    background-color: {card_bg};
    color: {text_color} !important;
    padding: 20px;
    border-radius: 20px;
    border: 2px solid {border_color};
    margin-top: 16px;
}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(f"<h1 class='main-title'>{t_title}</h1>", unsafe_allow_html=True)

api_key = st.secrets.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


def get_voice_api() -> str:
    return (
        "onyx"
        if "رجل" in st.session_state.voice or "Onyx" in st.session_state.voice
        else "nova"
    )


def play_voice_only(text: str):
    if client and text:
        try:
            audio_resp = client.audio.speech.create(
                model="tts-1",
                voice=get_voice_api(),
                input=text[:1500],
            )
            st.audio(audio_resp.read(), format="audio/mp3", autoplay=True)
        except Exception:
            pass


def reply_with_voice(text: str):
    st.markdown(text)
    play_voice_only(text)


def transcribe_once(audio_file, scope_name: str):
    if audio_file is None or not client:
        return None
    raw = audio_file.getvalue()
    sig = f"{scope_name}:{len(raw)}:{hash(raw[:128])}"
    if sig in st.session_state.processed_audio_ids:
        return None
    st.session_state.processed_audio_ids.append(sig)
    try:
        audio_file.seek(0)
        tr = client.audio.transcriptions.create(
            model="whisper-1",
            file=("voice.wav", audio_file, "audio/wav"),
        )
        spoken = (tr.text or "").strip()
        return spoken if spoken else None
    except Exception:
        return None


def record_subscriber_lesson_memory(sec_name: str, msgs: list):
    if not st.session_state.is_subscribed or not msgs:
        return
    st.session_state.section_memory.setdefault(sec_name, [])
    snippets = []
    for m in msgs[-6:]:
        who = "المستخدم" if m["role"] == "user" else "المساعد"
        raw_content = m.get("content", "")
        if isinstance(raw_content, list):
            txt_parts = [
                p.get("text", "") for p in raw_content if p.get("type") == "text"
            ]
            clean_txt = " ".join(" ".join(txt_parts).split())[:160]
        else:
            clean_txt = " ".join(str(raw_content).split())[:160]
        snippets.append(f"{who}: {clean_txt}")
    lesson_entry = f"[{TODAY_STR}] " + " | ".join(snippets)
    if (
        not st.session_state.section_memory[sec_name]
        or st.session_state.section_memory[sec_name][-1] != lesson_entry
    ):
        st.session_state.section_memory[sec_name].append(lesson_entry)
        st.session_state.section_memory[sec_name] = (
            st.session_state.section_memory[sec_name][-12:]
        )


def build_subscriber_memory_context(sec_name: str) -> str:
    if not st.session_state.is_subscribed:
        return ""
    past_items = list(st.session_state.section_memory.get(sec_name, []))
    for arch in st.session_state.archives:
        if arch.get("section") == sec_name and arch.get("messages"):
            first_c = arch["messages"][0].get("content", "")
            first_q = (
                first_c
                if isinstance(first_c, str)
                else " ".join(
                    p.get("text", "") for p in first_c if p.get("type") == "text"
                )
            )[:120]
            past_items.append(f"[أرشيف {arch.get('title', '')}] {first_q}")
    if not past_items:
        return ""
    joined = "\n- ".join(past_items[-10:])
    return (
        " Subscriber Previous Lessons & Conversations Memory in this section"
        f" ('{sec_name}'): remember what was previously covered across days/lessons"
        " and build naturally on past lessons without forgetting prior topics:\n-"
        f" {joined}"
    )


def format_history_for_api(chat_history: list) -> list:
    formatted = []
    for m in chat_history[-10:]:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            parts = []
            for p in content:
                if p.get("type") == "text":
                    parts.append({"type": "text", "text": p.get("text", "")})
                elif p.get("type") == "image_url":
                    parts.append(
                        {"type": "image_url", "image_url": p.get("image_url")}
                    )
            formatted.append({"role": role, "content": parts})
        else:
            formatted.append({"role": role, "content": str(content)})
    return formatted


def has_image_in_history(chat_history: list) -> bool:
    for m in chat_history[-6:]:
        c = m.get("content")
        if isinstance(c, list) and any(
            p.get("type") == "image_url" for p in c
        ):
            return True
    return False


def get_ai_answer(
    system_instruction: str, chat_history: list, sec_name: str = ""
) -> str:
    if not client:
        return "أهلاً بكِ في BRAS AI! أضيفي مفتاح OPENAI_API_KEY في Streamlit Secrets لتفعيل الردود الذكية."
    memory_note = (
        build_subscriber_memory_context(sec_name) if sec_name else ""
    )
    sys_full = (
        f"{system_instruction}{memory_note}\n"
        f"Current date: {TODAY_STR}. "
        "When the user attaches an image, examine the image directly and answer accurately based on what is visible in the image (such as ingredients, dishes, notes, or questions about the photo). "
        "Use live web search whenever needed for up-to-date match schedules, scores, trending TikTok creators, and current news. "
        "Provide a clear, helpful, and direct answer—never repeat or parrot what the user said. "
        f"Respond fluently in {st.session_state.language}."
    )
    recent_msgs = format_history_for_api(chat_history)

    if not has_image_in_history(chat_history):
        try:
            resp_web = client.responses.create(
                model="gpt-4o-mini",
                tools=[{"type": "web_search_preview"}],
                instructions=sys_full,
                input=recent_msgs,
            )
            if getattr(resp_web, "output_text", None):
                return resp_web.output_text
        except Exception:
            pass

    try:
        payload = [{"role": "system", "content": sys_full}] + recent_msgs
        resp = client.chat.completions.create(
            model="gpt-4o-mini", messages=payload
        )
        return resp.choices[0].message.content or ""
    except Exception:
        return "تم استلام طلبكِ بنجاح؛ تحققي من رصيد أو إعدادات مفتاح API في حساب OpenAI للمتابعة."


def can_send_free_message() -> bool:
    if st.session_state.is_subscribed:
        return True
    return st.session_state.free_messages_used < FREE_MSG_LIMIT


def record_free_message():
    if not st.session_state.is_subscribed:
        st.session_state.free_messages_used += 1


def can_use_free_section(sec_name: str) -> bool:
    if st.session_state.is_subscribed:
        return True
    allowed = st.session_state.free_allowed_sections
    if sec_name in allowed:
        return True
    return len(allowed) < FREE_SECTION_LIMIT


def register_free_section(sec_name: str):
    if not st.session_state.is_subscribed:
        if sec_name not in st.session_state.free_allowed_sections and (
            len(st.session_state.free_allowed_sections) < FREE_SECTION_LIMIT
        ):
            st.session_state.free_allowed_sections.append(sec_name)


def can_upload_free_media(is_video: bool) -> bool:
    if st.session_state.is_subscribed:
        return True
    if is_video:
        return st.session_state.free_daily_videos_used < FREE_DAILY_VIDEO_LIMIT
    return st.session_state.free_daily_images_used < FREE_DAILY_IMAGE_LIMIT


def record_free_media_upload(is_video: bool):
    if not st.session_state.is_subscribed:
        if is_video:
            st.session_state.free_daily_videos_used += 1
        else:
            st.session_state.free_daily_images_used += 1


def can_generate_free_video() -> bool:
    if st.session_state.is_subscribed:
        return True
    return st.session_state.free_daily_videos_used < FREE_DAILY_VIDEO_LIMIT


def record_free_video_generation():
    if not st.session_state.is_subscribed:
        st.session_state.free_daily_videos_used += 1


def count_free_tasks_on_day(day_name: str) -> int:
    return sum(1 for item in st.session_state.my_schedule if item["day"] == day_name)


def save_full_chat_snapshot(label: str, msgs: list):
    if not msgs:
        return
    entry = {
        "id": len(st.session_state.saved_chats) + 1,
        "title": f"{label} — {datetime.now().strftime('%H:%M')}",
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "messages": [dict(m) for m in msgs],
    }
    st.session_state.saved_chats.insert(0, entry)


def render_chat_message(message: dict):
    content = message.get("content", "")
    if isinstance(content, list):
        for part in content:
            if part.get("type") == "text" and part.get("text"):
                st.markdown(part["text"])
            elif part.get("type") == "image_url":
                url = part.get("image_url", {}).get("url", "")
                if url.startswith("data:image/") and "," in url:
                    mime_part, b64_part = url.split(",", 1)
                    mime_type = mime_part.split(";")[0].replace("data:", "")
                    try:
                        st.image(
                            base64.b64decode(b64_part),
                            caption=f"صورة ({mime_type})",
                            use_container_width=True,
                        )
                    except Exception:
                        pass
    else:
        st.markdown(str(content))


if not st.session_state.logged_in:
    st.markdown(
        f"<h3 style='text-align: center;'>{t_login_title}</h3>",
        unsafe_allow_html=True,
    )
    c_left, c_right = st.columns([2, 1])
    with c_left:
        with st.form("login_form"):
            email = st.text_input(
                t_email,
                value=st.session_state.user_email,
                placeholder="name@example.com",
            )
            password = st.text_input(
                t_password,
                type="password",
                placeholder="أدخل كلمة السر الخاصة بحسابك",
            )
            submit_button = st.form_submit_button(t_login_btn)
            if submit_button:
                clean_email = (email or "").strip().lower()
                clean_password = (password or "").strip()
                account_data = AUTHORIZED_ACCOUNTS.get(clean_email)
                if not is_valid_email(clean_email):
                    st.error("يرجى إدخال بريد إلكتروني صحيح.")
                elif not clean_password:
                    st.error("يرجى إدخال كلمة السر.")
                elif account_data is None:
                    st.error("هذا البريد الإلكتروني غير موجود في الحسابات المعتمدة.")
                elif account_data["password"] != clean_password:
                    st.error("كلمة السر غير صحيحة لهذا الحساب.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_email = clean_email
                    st.session_state.username = account_data["username"]
                    if st.session_state.trial_start is None:
                        st.session_state.trial_start = datetime.now()
                    st.rerun()
    with c_right:
        st.info(
            "✨ تسجيل الدخول بحسابكِ وكلمة سركِ\n\n• تجربة مجانية 24 ساعة\n•"
            " الباقات بعد التجربة:\n  - أسبوعي: **$2**\n  - شهري: **$10**\n "
            " - سنوي: **$50**"
        )
else:
    trial_active = False
    hours_left = 0
    if st.session_state.trial_start is not None:
        elapsed_time = datetime.now() - st.session_state.trial_start
        remaining = timedelta(hours=24) - elapsed_time
        if remaining.total_seconds() > 0:
            trial_active = True
            hours_left = max(1, int(remaining.total_seconds() // 3600))

    has_access = st.session_state.is_subscribed or trial_active

    if st.session_state.is_subscribed:
        status_badge = (
            f"✅ مشترك ({st.session_state.subscription_plan}) | 🧠 ذاكرة"
            " الدروس مفعّلة"
        )
    else:
        rem_msgs = max(0, FREE_MSG_LIMIT - st.session_state.free_messages_used)
        rem_secs = max(
            0, FREE_SECTION_LIMIT - len(st.session_state.free_allowed_sections)
        )
        rem_day_imgs = max(
            0, FREE_DAILY_IMAGE_LIMIT - st.session_state.free_daily_images_used
        )
        rem_day_vids = max(
            0, FREE_DAILY_VIDEO_LIMIT - st.session_state.free_daily_videos_used
        )
        trial_txt = f"⏳ {hours_left}س" if trial_active else "🔒 انتهت التجربة"
        status_badge = (
            f"{trial_txt} | 💬 {rem_msgs}/25 | 📷 {rem_day_imgs}/4 صور/يوم |"
            f" 🎬 {rem_day_vids}/1 فيديو/يوم | 📂 {rem_secs}/2 قسم"
        )

    st.markdown(
        f"""
        <div class='user-info'>
            <span>👤 {t_account}: <b>{st.session_state.username}</b> ({st.session_state.user_email}) | 🌐 {st.session_state.language}</span>
            <span>{status_badge} | 🖥️ {st.session_state.screen_mode} | 🎙️ {st.session_state.voice}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    screen_toggle = st.sidebar.toggle(
        "🖥️ وضع الشاشة الكاملة (Screen Mode)", value=is_screen_mode
    )
    new_screen_val = (
        "شاشة كاملة (Screen Mode)" if screen_toggle else "عادي (Normal)"
    )
    if new_screen_val != st.session_state.screen_mode:
        st.session_state.screen_mode = new_screen_val
        st.rerun()

    nav_mode = st.sidebar.radio(
        t_nav,
        (
            t_sec_main,
            t_sec_schedule,
            t_sec_chats,
            t_sec_pricing,
            t_sec_archive,
            t_sec_settings,
        ),
    )

    st.sidebar.divider()
    if st.sidebar.button(t_logout_btn):
        st.session_state.logged_in = False
        st.rerun()

    if not has_access and nav_mode not in (t_sec_pricing, t_sec_settings):
        st.warning(
            "🔒 انتهت فترة الـ 24 ساعة المجانية. يرجى اختيار باقة اشتراك لمتابعة استخدام الأقسام."
        )
        nav_mode = t_sec_pricing

    base_system_prompt = (
        f"You are BRAS AI, a smart assistant platform that can view and analyze uploaded images directly. "
        f"Current user language setting: {st.session_state.language}. Respond naturally and fluently in this language."
    )

    BASE_SECTIONS = {
        "المساعد الشامل": (
            "🤖",
            f"{base_system_prompt} You are a versatile smart assistant with live web search access and image vision.",
        ),
        "المعلم الشامل": (
            "📚",
            f"{base_system_prompt} You are an expert school teacher who can read and explain images.",
        ),
        "قسم كرة القدم": (
            "⚽",
            f"{base_system_prompt} You are a football analyst covering FC Barcelona, La Liga, Champions League, live match schedules, and football news.",
        ),
        "تعليم اللغات": (
            "🗣️",
            (
                f"{base_system_prompt} You are a multilingual tutor who tracks"
                " previous lessons, vocabulary, grammar, and past sessions"
                " when teaching new lessons and reading images."
            ),
        ),
        "البرمجة": (
            "💻",
            f"{base_system_prompt} You are an expert programmer.",
        ),
        "الطبخ والوصفات": (
            "🍳",
            f"{base_system_prompt} You are a master chef who can see uploaded food/ingredient images and suggest recipes and cooking tips.",
        ),
        "مكياج وسكين كير": (
            "💄",
            f"{base_system_prompt} You are a makeup and skincare specialist.",
        ),
        "ديزاين وملابس وشوبينغ": (
            "🛍️",
            f"{base_system_prompt} You are a fashion and shopping advisor.",
        ),
        "أفكار دول وسفرات": (
            "✈️",
            f"{base_system_prompt} You are a travel planner.",
        ),
        "قسم التاريخ": (
            "📜",
            f"{base_system_prompt} You are a history expert.",
        ),
        "الصحة، الدايت والجيم": (
            "💪",
            f"{base_system_prompt} You are a fitness and health coach.",
        ),
        "نصائح وتطوير الذات": (
            "💡",
            f"{base_system_prompt} You are a self-development advisor.",
        ),
        ads_sec_key: (
            "📢",
            (
                f"{base_system_prompt} You are an advertising and store"
                " marketing specialist for businesses."
            ),
        ),
        "صانع الفيديوهات والأفكار": (
            "🎬",
            (
                f"{base_system_prompt} You are a video ideas, scenes, prompts,"
                " and production assistant."
            ),
        ),
    }

    SECTIONS = {SECTIONS_NAMES.get(k, k): v for k, v in BASE_SECTIONS.items()}

    if (
        st.session_state.selected_section is not None
        and st.session_state.selected_section not in SECTIONS
    ):
        st.session_state.selected_section = None

    if nav_mode == t_sec_main:
        if st.session_state.selected_section is None:
            st.markdown(
                f"<h3 style='text-align: center;'>{t_choose_sec}</h3>",
                unsafe_allow_html=True,
            )
            if not st.session_state.is_subscribed:
                used_secs = ", ".join(st.session_state.free_allowed_sections) or "لا يوجد بعد"
                st.info(
                    "🔒 لغير المشتركين: **قسمين فقط** (المختارة حالياً:"
                    f" {used_secs})، حد **25 رسالة**، و**4 صور + 1 فيديو"
                    " يومياً**."
                )
            grid_cols = 4 if is_screen_mode else 3
            cols = st.columns(grid_cols)
            for index, (sec_name, (emoji, _)) in enumerate(SECTIONS.items()):
                col = cols[index % grid_cols]
                with col:
                    st.markdown(
                        "<div class='grid-card-wrap'>", unsafe_allow_html=True
                    )
                    if st.button(f"{emoji}\n\n{sec_name}", key=f"sec_btn_{index}"):
                        if can_use_free_section(sec_name):
                            register_free_section(sec_name)
                            st.session_state.selected_section = sec_name
                            st.session_state.browsing_archive = None
                            st.session_state.latest_voice_text = None
                            st.rerun()
                        else:
                            st.warning(
                                "🔒 وصلتِ للحد المسموح لغير المشتركين (قسمين فقط)."
                                " اشتركي لفتح جميع الأقسام."
                            )
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            sec_name = st.session_state.selected_section
            emoji, system_prompt = SECTIONS.get(
                sec_name, ("🤖", f"{base_system_prompt}")
            )
            browsing_item = st.session_state.browsing_archive

            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(f"{sec_name} {emoji}")
            with col2:
                if st.button(t_back_grid):
                    record_subscriber_lesson_memory(
                        sec_name,
                        st.session_state.section_messages.get(sec_name, []),
                    )
                    st.session_state.selected_section = None
                    st.session_state.browsing_archive = None
                    st.session_state.latest_voice_text = None
                    st.rerun()

            if st.session_state.is_subscribed and browsing_item is None:
                mem_count = len(st.session_state.section_memory.get(sec_name, []))
                if mem_count > 0:
                    st.caption(
                        f"🧠 يتذكر BRAS AI دروسكِ ومحادثاتكِ السابقة في هذا القسم ({mem_count} سجل درس سابق)."
                    )

            if st.session_state.latest_voice_text:
                play_voice_only(st.session_state.latest_voice_text)
                st.session_state.latest_voice_text = None

            if browsing_item is None:
                col_new, col_arc, col_save_side = st.columns(3)
                if col_new.button(t_new_chat):
                    record_subscriber_lesson_memory(
                        sec_name,
                        st.session_state.section_messages.get(sec_name, []),
                    )
                    st.session_state.section_messages[sec_name] = []
                    st.session_state.pending_image_b64 = None
                    st.session_state.pending_image_mime = None
                    st.session_state.pending_image_name = None
                    st.session_state.latest_voice_text = None
                    st.rerun()
                if col_arc.button(t_archive_btn):
                    msgs = st.session_state.section_messages.get(sec_name, [])
                    if msgs:
                        record_subscriber_lesson_memory(sec_name, msgs)
                        archive_title = f"{sec_name} - {datetime.now().strftime('%H:%M')}"
                        st.session_state.archives.append({
                            "title": archive_title,
                            "section": sec_name,
                            "messages": [dict(m) for m in msgs],
                        })
                        st.success(t_archived_ok)
                if col_save_side.button("📌 حفظ في سجل الدردشة"):
                    msgs = st.session_state.section_messages.get(sec_name, [])
                    if msgs:
                        record_subscriber_lesson_memory(sec_name, msgs)
                        save_full_chat_snapshot(sec_name, msgs)
                        st.success("تم حفظ الدردشة كاملة في سجل الدردشة!")
            else:
                st.info(f"📖 استعراض أرشيف: {browsing_item['title']}")
                if st.button(t_exit_arch):
                    st.session_state.browsing_archive = None
                    st.rerun()

            with st.expander(t_file_upload, expanded=False):
                uploaded_media = st.file_uploader(
                    "File:",
                    type=["png", "jpg", "jpeg", "webp", "mp4", "pdf"],
                    key=f"up_{sec_name}",
                )
                if uploaded_media is not None:
                    raw_m = uploaded_media.getvalue()
                    up_sig = f"{TODAY_STR}:{sec_name}:{uploaded_media.name}:{len(raw_m)}:{hash(raw_m[:128])}"
                    lower_name = uploaded_media.name.lower()
                    is_vid_file = lower_name.endswith(".mp4")
                    is_img_file = lower_name.endswith(
                        (".png", ".jpg", ".jpeg", ".webp")
                    )

                    if up_sig not in st.session_state.processed_upload_ids:
                        if (is_vid_file or is_img_file) and not st.session_state.is_subscribed:
                            if not can_upload_free_media(is_vid_file):
                                if is_vid_file:
                                    st.warning(
                                        "🔒 يُسمح بإرسال **فيديو واحد فقط في"
                                        " اليوم** لغير المشتركين."
                                    )
                                else:
                                    st.warning(
                                        "🔒 يُسمح بإرسال **4 صور فقط في"
                                        " اليوم** لغير المشتركين."
                                    )
                            else:
                                st.session_state.processed_upload_ids.append(
                                    up_sig
                                )
                                record_free_media_upload(is_vid_file)
                        else:
                            st.session_state.processed_upload_ids.append(
                                up_sig
                            )

                    if is_img_file:
                        ext = lower_name.rsplit(".", 1)[-1]
                        mime_type = (
                            "image/jpeg" if ext == "jpg" else f"image/{ext}"
                        )
                        b64_img = base64.b64encode(raw_m).decode("utf-8")
                        st.session_state.pending_image_b64 = b64_img
                        st.session_state.pending_image_mime = mime_type
                        st.session_state.pending_image_name = uploaded_media.name
                        st.image(
                            raw_m,
                            caption=f"جاهزة للرؤية والتحليل: {uploaded_media.name}",
                            use_container_width=True,
                        )
                    elif is_vid_file:
                        st.video(raw_m)
                    else:
                        st.success(f"تم إرفاق الملف: {uploaded_media.name}")

            if st.session_state.pending_image_b64 and browsing_item is None:
                st.info(
                    f"🖼️ صورة مرفقة جاهزة للرؤية: **{st.session_state.pending_image_name}** — اكتبي سؤالكِ أو اضغطي «شاهد الصورة وأجب»."
                )
                if st.button("👁️ شاهد الصورة وأجب", key=f"see_img_{sec_name}"):
                    if not can_send_free_message():
                        st.warning(
                            "🔒 وصلتِ للحد الأقصى (25 رسالة فقط) لغير"
                            " المشتركين."
                        )
                    else:
                        record_free_message()
                        img_msg = [
                            {
                                "type": "text",
                                "text": (
                                    "انظر إلى هذه الصورة واشرح محتواها وأجب"
                                    " بما يفيد في هذا القسم."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": (
                                        f"data:{st.session_state.pending_image_mime};base64,{st.session_state.pending_image_b64}"
                                    )
                                },
                            },
                        ]
                        st.session_state.section_messages.setdefault(
                            sec_name, []
                        ).append({"role": "user", "content": img_msg})
                        st.session_state.pending_image_b64 = None
                        st.session_state.pending_image_mime = None
                        st.session_state.pending_image_name = None
                        full_response = get_ai_answer(
                            system_prompt,
                            st.session_state.section_messages[sec_name],
                            sec_name=sec_name,
                        )
                        st.session_state.section_messages[sec_name].append(
                            {"role": "assistant", "content": full_response}
                        )
                        record_subscriber_lesson_memory(
                            sec_name, st.session_state.section_messages[sec_name]
                        )
                        st.session_state.latest_voice_text = full_response
                        st.rerun()

            is_ads_section = any(
                w in sec_name for w in ["إعلانات", "Ads", "ڕیکلام"]
            )
            if is_ads_section and browsing_item is None:
                st.markdown("### 📢 مولد إعلانات المتاجر والمشاريع")
                ad_store = st.text_input(
                    "اسم المتجر أو النشاط التجاري", key="ad_store_name"
                )
                ad_offer = st.text_area(
                    "تفاصيل المنتج أو العرض أو الخدمة", key="ad_offer_desc"
                )
                ad_channel = st.selectbox(
                    "منصة الإعلان",
                    ["Instagram", "TikTok", "Facebook", "Snapchat"],
                    key="ad_channel_box",
                )
                if st.button(
                    "توليد نص الإعلان الآن", type="primary", key="gen_ad_btn"
                ):
                    if not can_send_free_message():
                        st.warning(
                            "🔒 انتهى حد الـ 25 رسالة لغير المشتركين. اشتركي"
                            " للمتابعة."
                        )
                    elif ad_store.strip() and ad_offer.strip():
                        record_free_message()
                        ad_out = get_ai_answer(
                            (
                                f"{system_prompt} Create a persuasive ad for"
                                f" {ad_channel} for store '{ad_store}'"
                                f" offering: {ad_offer}."
                            ),
                            [
                                {
                                    "role": "user",
                                    "content": (
                                        f"Store: {ad_store}\nOffer: {ad_offer}"
                                    ),
                                }
                            ],
                            sec_name=sec_name,
                        )
                        st.session_state.section_messages.setdefault(
                            sec_name, []
                        ).append({"role": "assistant", "content": ad_out})
                        record_subscriber_lesson_memory(
                            sec_name, st.session_state.section_messages[sec_name]
                        )
                        st.session_state.latest_voice_text = ad_out
                        st.rerun()
                    else:
                        st.info("اكتبي اسم المتجر ووصف العرض أولاً.")
                st.markdown("---")

            is_vid_section = any(
                w in sec_name for w in ["الفيديوهات", "Video", "ڤیدیۆ"]
            )
            if is_vid_section and browsing_item is None:
                st.markdown("### 🎬 استوديو الفيديوهات والأفكار")
                if not st.session_state.is_subscribed:
                    st.caption(
                        "المتبقي من الفيديوهات اليوم:"
                        f" {max(0, FREE_DAILY_VIDEO_LIMIT - st.session_state.free_daily_videos_used)}/{FREE_DAILY_VIDEO_LIMIT}"
                    )
                vid_idea = st.text_area(
                    "اكتبي فكرة الفيديو أو المشهد:", key="vid_studio_idea"
                )
                vid_style = st.selectbox(
                    "نمط الفيديو",
                    [
                        "سينمائي",
                        "إعلان تجاري",
                        "سوشيال ميديا / Reels",
                        "أنيميشن",
                    ],
                    key="vid_studio_style",
                )
                if st.button(
                    "🎬 توليد سيناريو ومشاهد الفيديو",
                    type="primary",
                    key="gen_vid_btn",
                ):
                    if not can_generate_free_video():
                        st.warning(
                            "🔒 وصلتِ للحد اليومي لغير المشتركين (**1 فيديو في"
                            " اليوم**)."
                        )
                    elif not can_send_free_message():
                        st.warning(
                            "🔒 انتهى حد الـ 25 رسالة لغير المشتركين. اشتركي"
                            " للمتابعة."
                        )
                    elif vid_idea.strip():
                        record_free_video_generation()
                        record_free_message()
                        with st.spinner("جاري تجهيز السيناريو والمشاهد..."):
                            vid_plan = get_ai_answer(
                                (
                                    f"{system_prompt} Create a complete video"
                                    " concept, scene-by-scene storyboard, camera"
                                    " angles, voiceover script, and video prompt"
                                    f" in style '{vid_style}' for:"
                                    f" {vid_idea}."
                                ),
                                [{"role": "user", "content": vid_idea.strip()}],
                                sec_name=sec_name,
                            )
                        st.session_state.generated_videos.insert(
                            0,
                            {
                                "idea": vid_idea.strip(),
                                "style": vid_style,
                                "script": vid_plan,
                            },
                        )
                        record_subscriber_lesson_memory(
                            sec_name,
                            st.session_state.section_messages.get(
                                sec_name, []
                            ),
                        )
                        st.session_state.latest_voice_text = vid_plan
                        st.rerun()
                    else:
                        st.info("اكتبي فكرة الفيديو أولاً.")

                for v in st.session_state.generated_videos[:3]:
                    st.markdown(f"**{v['style']}:** {v['idea']}")
                    st.markdown(v["script"])
                    st.divider()
                st.markdown("---")

            if browsing_item is not None:
                active_messages = browsing_item.get("messages", [])
            else:
                st.session_state.section_messages.setdefault(sec_name, [])
                active_messages = st.session_state.section_messages[sec_name]

            for message in active_messages:
                with st.chat_message(message["role"]):
                    render_chat_message(message)

            if browsing_item is None:
                user_spoken_text = None
                audio_val = st.audio_input(
                    "🎙️ تحدثِ هنا للرد الفوري:", key=f"mic_sec_{sec_name}"
                )
                user_spoken_text = transcribe_once(audio_val, f"sec_{sec_name}")

                typed_prompt = st.chat_input("اكتبي رسالتكِ هنا...")
                final_prompt = user_spoken_text if user_spoken_text else typed_prompt

                if final_prompt:
                    if not can_send_free_message():
                        st.warning(
                            "🔒 وصلتِ للحد الأقصى (25 رسالة فقط) لغير"
                            " المشتركين. اختاري باقة اشتراك للمتابعة."
                        )
                    else:
                        record_free_message()
                        if st.session_state.pending_image_b64:
                            user_payload = [
                                {"type": "text", "text": final_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": (
                                            f"data:{st.session_state.pending_image_mime};base64,{st.session_state.pending_image_b64}"
                                        )
                                    },
                                },
                            ]
                            st.session_state.pending_image_b64 = None
                            st.session_state.pending_image_mime = None
                            st.session_state.pending_image_name = None
                        else:
                            user_payload = final_prompt

                        st.session_state.section_messages[sec_name].append(
                            {"role": "user", "content": user_payload}
                        )
                        with st.chat_message("user"):
                            render_chat_message(
                                {"role": "user", "content": user_payload}
                            )

                        with st.chat_message("assistant"):
                            full_response = get_ai_answer(
                                system_prompt,
                                st.session_state.section_messages[sec_name],
                                sec_name=sec_name,
                            )
                            reply_with_voice(full_response)
                            st.session_state.section_messages[sec_name].append(
                                {
                                    "role": "assistant",
                                    "content": full_response,
                                }
                            )
                            record_subscriber_lesson_memory(
                                sec_name,
                                st.session_state.section_messages[sec_name],
                            )

    elif nav_mode == t_sec_schedule:
        st.header(t_schedule_title)
        if not st.session_state.is_subscribed:
            st.info(
                "🔒 لغير المشتركين: يُسمح بمهمة واحدة في اليوم (**1/يوم**) و3"
                " مهام في الأسبوع (**3/أسبوع**)."
            )
        with st.form("sch_form"):
            task_desc = st.text_input(t_task_input)
            col_d, col_t = st.columns(2)
            with col_d:
                task_day = st.selectbox(
                    t_day_label,
                    [
                        "السبت",
                        "الأحد",
                        "الإثنين",
                        "الثلاثاء",
                        "الأربعاء",
                        "الخميس",
                        "الجمعة",
                    ],
                )
            with col_t:
                task_time = st.text_input(t_time_label, value="12:00")

            if st.form_submit_button(t_add_task_btn) and task_desc.strip():
                if not st.session_state.is_subscribed:
                    if len(st.session_state.my_schedule) >= FREE_WEEKLY_TASK_LIMIT:
                        st.warning(
                            "🔒 وصلتِ للحد الأسبوعي (3 مهام في الأسبوع) لغير"
                            " المشتركين."
                        )
                    elif count_free_tasks_on_day(task_day) >= FREE_DAILY_TASK_LIMIT:
                        st.warning(
                            f"🔒 يُسمح بمهمة واحدة فقط في يوم {task_day} لغير"
                            " المشتركين."
                        )
                    else:
                        st.session_state.my_schedule.append({
                            "day": task_day,
                            "time": task_time.strip() or "12:00",
                            "task": task_desc.strip(),
                        })
                        st.success(t_task_added)
                else:
                    st.session_state.my_schedule.append({
                        "day": task_day,
                        "time": task_time.strip() or "12:00",
                        "task": task_desc.strip(),
                    })
                    st.success(t_task_added)

        if st.session_state.my_schedule:
            st.subheader(t_schedule_list)
            for idx, item in enumerate(st.session_state.my_schedule):
                c_txt, c_del = st.columns([5, 1])
                with c_txt:
                    st.info(
                        f"⏰ **تذكير:** {item['day']} الساعة **{item['time']}**"
                        f" — {item['task']}"
                    )
                with c_del:
                    if st.button("حذف", key=f"del_sch_{idx}"):
                        st.session_state.my_schedule.pop(idx)
                        st.rerun()
        else:
            st.info("لا توجد مواعيد مضافة في جدولكِ حالياً.")

    elif nav_mode == t_sec_chats:
        st.header("💬 سجل الدردشة الكاملة")
        if not st.session_state.saved_chats:
            st.info(
                "لم يتم حفظ أي دردشة كاملة بعد. اضغطي على «حفظ في سجل الدردشة»"
                " داخل أي قسم لحفظها هنا."
            )
        else:
            for idx, chat_item in enumerate(st.session_state.saved_chats):
                with st.expander(
                    f"🗂️ {chat_item['title']} ({chat_item['saved_at']})",
                    expanded=(idx == 0),
                ):
                    for m in chat_item["messages"]:
                        role_label = "المستخدم" if m["role"] == "user" else "BRAS AI"
                        st.markdown(f"**{role_label}:**")
                        render_chat_message(m)
                    st.download_button(
                        label="⬇️ تحميل الدردشة (JSON)",
                        data=json.dumps(chat_item, ensure_ascii=False, indent=2),
                        file_name=f"bras_ai_chat_{chat_item['id']}.json",
                        mime="application/json",
                        key=f"dl_chat_{idx}",
                    )

    elif nav_mode == t_sec_pricing:
        st.header("💳 الباقات والاشتراك (BRAS AI)")
        st.write("اختاري الباقة المناسبة لفتح الوصول الكامل غير المحدود:")
        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown(
                "<div class='plan-box'><h3>أسبوعي</h3><h2>$2</h2><p>صلاحية 7"
                " أيام</p></div>",
                unsafe_allow_html=True,
            )
            if st.button("اشتراك أسبوعي ($2)", key="plan_w"):
                st.session_state.is_subscribed = True
                st.session_state.subscription_plan = "أسبوعي - $2"
                st.success("تم تفعيل الباقة الأسبوعية ($2)!")
                st.rerun()
        with p2:
            st.markdown(
                "<div class='plan-box'><h3>شهري</h3><h2>$10</h2><p>صلاحية 30"
                " يوماً</p></div>",
                unsafe_allow_html=True,
            )
            if st.button("اشتراك شهري ($10)", key="plan_m"):
                st.session_state.is_subscribed = True
                st.session_state.subscription_plan = "شهري - $10"
                st.success("تم تفعيل الباقة الشهرية ($10)!")
                st.rerun()
        with p3:
            st.markdown(
                "<div class='plan-box'><h3>سنوي</h3><h2>$50</h2><p>صلاحية 365"
                " يوماً</p></div>",
                unsafe_allow_html=True,
            )
            if st.button("اشتراك سنوي ($50)", key="plan_y"):
                st.session_state.is_subscribed = True
                st.session_state.subscription_plan = "سنوي - $50"
                st.success("تم تفعيل الباقة السنوية ($50)!")
                st.rerun()

        st.radio(
            "طريقة الدفع:",
            ["Visa / Mastercard", "K-Net / QiCard / زين كاش"],
        )

    elif nav_mode == t_sec_archive:
        st.markdown(
            f"<h2 style='text-align: center; color: #9b5de5;'>{t_archive_header}</h2>",
            unsafe_allow_html=True,
        )
        if not st.session_state.archives:
            st.info(t_no_archive)
        else:
            for idx, arch in enumerate(st.session_state.archives):
                with st.expander(f"📁 {arch['title']}", expanded=True):
                    if st.button(t_browse, key=f"arch_{idx}"):
                        st.session_state.selected_section = arch["section"]
                        st.session_state.browsing_archive = arch
                        st.rerun()

    elif nav_mode == t_sec_settings:
        st.markdown(
            f"<h2 style='text-align: center;'>{t_settings_header}</h2>",
            unsafe_allow_html=True,
        )
        with st.container():
            st.markdown("<div class='settings-panel'>", unsafe_allow_html=True)
            new_name = st.text_input(
                t_username, value=st.session_state.username
            )
            new_theme = st.radio(
                t_theme,
                ("داكن (Dark)", "فاتح (Light)"),
                index=(
                    0
                    if "داكن" in st.session_state.theme
                    or "Dark" in st.session_state.theme
                    else 1
                ),
            )
            new_voice = st.radio(
                t_voice,
                ("صوت بنت نقي وواضح (Nova)", "صوت رجل نقي وواضح (Onyx)"),
                index=(
                    0
                    if "بنت" in st.session_state.voice
                    or "Nova" in st.session_state.voice
                    else 1
                ),
            )
            new_screen = st.radio(
                t_screen_mode,
                ("عادي (Normal)", "شاشة كاملة (Screen Mode)"),
                index=1 if is_screen_mode else 0,
            )

            languages_40 = [
                "العربية (Arabic)",
                "الإنجليزية (English)",
                "الكوردية (Kurdish Badini)",
                "التركية (Türkçe)",
                "الفرنسية (Français)",
                "الألمانية (Deutsch)",
                "الإسبانية (Español)",
                "الإيطالية (Italiano)",
                "الروسية (Русский)",
                "الصينية المبسطة (中文)",
                "اليابانية (日本語)",
                "الكورية (한국어)",
                "الفارسية (فارسی)",
                "الأوردو (اردو)",
                "الهندية (हिन्दी)",
                "البرتغالية (Português)",
                "البنغالية (বাংলা)",
                "البنجابية (ਪੰਜਾਬੀ)",
                "الإندونيسية (Bahasa Indonesia)",
                "الماليزية (Bahasa Melayu)",
                "الفيتنامية (Tiếng Việt)",
                "التايلاندية (ไทย)",
                "الهولندية (Nederlands)",
                "البولندية (Polski)",
                "الأوكرانية (Українська)",
                "اليونانية (Ελληνικά)",
                "السويدية (Svenska)",
                "النرويجية (Norsk)",
                "الدنماركية (Dansk)",
                "الفنلندية (Suomi)",
                "المجرية (Magyar)",
                "التشيكية (Čeština)",
                "الرومانية (Română)",
                "البلغارية (Български)",
                "السلوفاكية (Slovenčina)",
                "الكرواتية (Hrvatski)",
                "العبرية (עברית)",
                "الفلبينية (Tagalog)",
                "السواحلية (Kiswahili)",
                "الأمهرية (አማርኛ)",
            ]

            current_lang_idx = (
                languages_40.index(st.session_state.language)
                if st.session_state.language in languages_40
                else 0
            )
            new_lang = st.selectbox(
                t_lang_label, languages_40, index=current_lang_idx
            )

            st.markdown("---")
            st.checkbox("Enable notifications on app open", value=True)

            if st.button(t_save):
                lang_changed = new_lang != st.session_state.language
                st.session_state.username = new_name.strip() or st.session_state.username
                st.session_state.theme = new_theme
                st.session_state.voice = new_voice
                st.session_state.screen_mode = new_screen
                st.session_state.language = new_lang
                if lang_changed:
                    st.session_state.selected_section = None
                    st.session_state.browsing_archive = None
                st.success(t_saved_ok)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
