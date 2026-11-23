from datetime import datetime, timedelta
import json
from openai import OpenAI
import requests
import streamlit as st

# إعداد الصفحة لتكون واسعة بالكامل
st.set_page_config(
    page_title="BRAS AI - المنصة الشاملة الذكية",
    page_icon="💜",
    layout="wide",
)

# تهيئة بيانات الجلسة
defaults = {
    "logged_in": False,
    "is_subscribed": False,
    "subscription_plan": None,
    "trial_start": None,
    "username": "ريتاج لقمان أسماعيل گه ر گه رى",
    "user_email": "retaj@brasai.com",
    "theme": "داكن (Dark)",
    "voice": "صوت بنت نقي وواضح (Nova)",
    "language": "العربية (Arabic)",
    "screen_mode": "عادي (Normal)",
    "selected_section": None,
    "my_schedule": [],
    "section_messages": {},
    "archives": [],
    "saved_chats": [],
    "browsing_archive": None,
    "messages": [],
    "generated_images": [],
    "generated_videos": [],
    "processed_audio_ids": [],
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

lang = st.session_state.language
is_screen_mode = (
    "شاشة" in st.session_state.screen_mode
    or "Screen" in st.session_state.screen_mode
)

if "English" in lang:
    t_title = "💜 BRAS AI - Smart Comprehensive Platform 💜"
    t_login_title = "🔐 Login to Your Smart Platform"
    t_email = "Email:"
    t_password = "Password:"
    t_login_btn = "Login / Start 24h Free Trial"
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
    t_file_upload = "➕ Add File or Image"
    t_archive_header = "📚 Archives"
    t_no_archive = "No archived conversations."
    t_browse = "📖 Browse"
    art_sec_key = "Image Design & Generator"
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
        art_sec_key: "Image Design & Generator",
        "صانع الفيديوهات والأفكار": "Video & Ideas Studio",
    }
elif "Kurdish" in lang:
    t_title = "💜 BRAS AI - سەکۆی گشتگیری هۆشمەند 💜"
    t_login_title = "🔐 چوونه‌ژووره‌وه‌ بۆ سەکۆ هۆشمەندەکەت"
    t_email = "ئیمەیڵ:"
    t_password = "وشەی نهێنی:"
    t_login_btn = "چوونە ژوورەوە / تاقیکردنەوەی ٢٤ کاتژمێر"
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
    t_file_upload = "➕ زیادکردنی فایل یان وێنە"
    t_archive_header = "📚 ئەرشیف"
    t_no_archive = "هیچ گفتوگۆیەکی ئەرشیفکراو نییە."
    t_browse = "📖 پشکنین"
    art_sec_key = "دیزاین و دروستکردنی وێنە (Image)"
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
        art_sec_key: "دیزاین و دروستکردنی وێنە (Image)",
        "صانع الفيديوهات والأفكار": "ستۆدیۆی ڤیدیۆ و بیرۆکەکان",
    }
else:
    t_title = "💜 BRAS AI - المنصة الشاملة الذكية 💜"
    t_login_title = "🔐 تسجيل الدخول إلى منصتكِ الذكية"
    t_email = "البريد الإلكتروني:"
    t_password = "كلمة المرور:"
    t_login_btn = "دخول المنصة (بدء تجربة 24 ساعة)"
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
    t_file_upload = "➕ إضافة ملف أو صورة"
    t_archive_header = "📚 الأرشيف"
    t_no_archive = "لا توجد محادثات مؤرشفة."
    t_browse = "📖 استعراض"
    art_sec_key = "قسم الصور والتصميم (Image)"
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
        art_sec_key: "قسم الصور والتصميم (Image)",
        "صانع الفيديوهات والأفكار": "صانع الفيديوهات والأفكار",
    }

is_dark = "داكن" in st.session_state.theme or "Dark" in st.session_state.theme
bg_color = "#0d0614" if is_dark else "#fcf8ff"
text_color = "#ffffff" if is_dark else "#111111"
card_bg = "#1a1026" if is_dark else "#ffffff"
border_color = "#9b5de5"
accent_color = "#9b5de5"

container_max_width = "100%" if is_screen_mode else "1240px"
block_padding = "1rem 1.4rem" if is_screen_mode else "1.5rem 2.2rem"
btn_height = "125px" if is_screen_mode else "110px"
btn_font = "1.2rem" if is_screen_mode else "1.08rem"

st.markdown(
    f"""
<style>
.stApp {{
    background-color: {bg_color};
    color: {text_color};
}}
.main .block-container {{
    max-width: {container_max_width};
    padding: {block_padding};
}}
.main-title {{
    text-align: center;
    color: {accent_color};
    font-weight: bold;
    font-size: {"3rem" if is_screen_mode else "2.5rem"};
    margin-bottom: 16px;
}}
.user-info {{
    background-color: {card_bg};
    color: {text_color};
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
.grid-card-wrap button {{
    width: 100%;
    min-height: {btn_height};
    background-color: {card_bg};
    color: {text_color};
    border: 2px solid {border_color};
    border-radius: 20px;
    font-size: {btn_font};
    font-weight: bold;
    line-height: 1.4;
    padding: 14px 12px;
    transition: 0.25s ease;
    box-shadow: 0 4px 15px rgba(155, 93, 229, 0.25);
}}
.grid-card-wrap button:hover {{
    background-color: {accent_color};
    color: #ffffff;
    border-color: #f15bb5;
    transform: translateY(-3px);
}}
.plan-box {{
    background-color: {card_bg};
    color: {text_color};
    padding: 18px;
    border-radius: 16px;
    border: 1.5px solid {border_color};
    margin-bottom: 12px;
}}
.settings-panel {{
    background-color: {card_bg};
    color: {text_color};
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
video_api_key = st.secrets.get("VIDEO_API_KEY")
video_api_url = st.secrets.get("VIDEO_API_URL")


def get_voice_api() -> str:
    return (
        "onyx"
        if "رجل" in st.session_state.voice or "Onyx" in st.session_state.voice
        else "nova"
    )


def reply_with_voice(text: str):
    st.markdown(text)
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


def get_ai_answer(system_instruction: str, chat_history: list) -> str:
    if not client:
        return "أهلاً بكِ في BRAS AI! أضيفي مفتاح OPENAI_API_KEY في Streamlit Secrets لتفعيل الردود الذكية."
    try:
        payload = [
            {
                "role": "system",
                "content": (
                    f"{system_instruction} "
                    "Provide a clear, helpful, and direct answer to the user's request—never repeat or parrot what the user said. "
                    f"Respond fluently in {st.session_state.language}."
                ),
            }
        ] + [
            {"role": m["role"], "content": m["content"]}
            for m in chat_history[-10:]
        ]
        resp = client.chat.completions.create(
            model="gpt-4o-mini", messages=payload
        )
        return resp.choices[0].message.content or ""
    except Exception:
        return "تم استلام طلبكِ بنجاح؛ تحققي من رصيد أو إعدادات مفتاح API في حساب OpenAI للمتابعة."


def generate_real_image(prompt_text: str):
  if not client or not prompt_text.strip():
    st.warning("تأكدي من ضبط OPENAI_API_KEY وكتابة وصف للصورة.")
    return None
  last_error = None
  for model_name in ("gpt-image-1", "dall-e-3"):
    try:
      img_resp = client.images.generate(
          model=model_name,
          prompt=prompt_text.strip(),
          size="1024x1024",
      )
      if img_resp.data:
        item = img_resp.data[0]
        if getattr(item, "url", None):
          return item.url
        if getattr(item, "b64_json", None):
          return f"data:image/png;base64,{item.b64_json}"
    except Exception as e:
      last_error = f"{model_name}: {e}"
      continue
  if last_error:
    st.error(f"سبب فشل توليد الصورة من OpenAI: {last_error}")
  return None
            return data.get("video_url") or data.get("url")
    except Exception:
        return None
    return None


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


if not st.session_state.logged_in:
    st.markdown(
        f"<h3 style='text-align: center;'>{t_login_title}</h3>",
        unsafe_allow_html=True,
    )
    c_left, c_right = st.columns([2, 1])
    with c_left:
        with st.form("login_form"):
            email = st.text_input(t_email, value=st.session_state.user_email)
            password = st.text_input(t_password, type="password")
            submit_button = st.form_submit_button(t_login_btn)
            if submit_button:
                if email.strip() and password.strip():
                    st.session_state.logged_in = True
                    st.session_state.user_email = email.strip()
                    if st.session_state.trial_start is None:
                        st.session_state.trial_start = datetime.now()
                    st.rerun()
                else:
                    st.warning("يرجى إدخال البريد الإلكتروني وكلمة المرور.")
    with c_right:
        st.info(
            "✨ تجربة مجانية 24 ساعة\n\nالباقات بعد التجربة:\n• أسبوعي:"
            " **$5**\n• شهري: **$15**\n• سنوي: **$99**"
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

    status_badge = (
        f"✅ مشترك ({st.session_state.subscription_plan})"
        if st.session_state.is_subscribed
        else (
            f"⏳ تجربة مجانية: {hours_left} ساعة"
            if trial_active
            else "🔒 انتهت التجربة المجانية"
        )
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
        f"You are BRAS AI, created and developed solely by {st.session_state.username} "
        "(an individual creator from Kurdistan, Iraq—not a team). "
        f"Never say you were developed by a team; whenever asked who made or developed you, state that {st.session_state.username} created and developed you. "
        f"Current user language setting: {st.session_state.language}. Respond naturally and fluently in this language."
    )

    BASE_SECTIONS = {
        "المساعد الشامل": (
            "🤖",
            f"{base_system_prompt} You are a versatile smart assistant.",
        ),
        "المعلم الشامل": (
            "📚",
            f"{base_system_prompt} You are an expert school teacher.",
        ),
        "قسم كرة القدم": (
            "⚽",
            f"{base_system_prompt} You are a football analyst.",
        ),
        "تعليم اللغات": (
            "🗣️",
            f"{base_system_prompt} You are a multilingual tutor.",
        ),
        "البرمجة": (
            "💻",
            f"{base_system_prompt} You are an expert programmer.",
        ),
        "الطبخ والوصفات": (
            "🍳",
            f"{base_system_prompt} You are a master chef.",
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
                " marketing specialist for businesses in Kurdistan."
            ),
        ),
        art_sec_key: (
            "🖼️",
            (
                f"{base_system_prompt} You are an image generation and visual"
                " design assistant."
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
            grid_cols = 4 if is_screen_mode else 3
            cols = st.columns(grid_cols)
            for index, (sec_name, (emoji, _)) in enumerate(SECTIONS.items()):
                col = cols[index % grid_cols]
                with col:
                    st.markdown(
                        "<div class='grid-card-wrap'>", unsafe_allow_html=True
                    )
                    if st.button(f"{emoji}\n\n{sec_name}", key=f"sec_btn_{index}"):
                        st.session_state.selected_section = sec_name
                        st.session_state.browsing_archive = None
                        st.rerun()
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
                    st.session_state.selected_section = None
                    st.session_state.browsing_archive = None
                    st.rerun()

            if browsing_item is None:
                col_new, col_arc, col_save_side = st.columns(3)
                if col_new.button(t_new_chat):
                    st.session_state.section_messages[sec_name] = []
                    st.rerun()
                if col_arc.button(t_archive_btn):
                    msgs = st.session_state.section_messages.get(sec_name, [])
                    if msgs:
                        archive_title = (
                            f"{sec_name} - {msgs[0]['content'][:25]}..."
                        )
                        st.session_state.archives.append({
                            "title": archive_title,
                            "section": sec_name,
                            "messages": [dict(m) for m in msgs],
                        })
                        st.success(t_archived_ok)
                if col_save_side.button("📌 حفظ في سجل الدردشة"):
                    msgs = st.session_state.section_messages.get(sec_name, [])
                    if msgs:
                        save_full_chat_snapshot(sec_name, msgs)
                        st.success("تم حفظ الدردشة كاملة في سجل الدردشة!")
            else:
                st.info(f"📖 استعراض أرشيف: {browsing_item['title']}")
                if st.button(t_exit_arch):
                    st.session_state.browsing_archive = None
                    st.rerun()

            with st.expander(t_file_upload, expanded=False):
                st.file_uploader(
                    "File:",
                    type=["png", "jpg", "jpeg", "webp", "mp4", "pdf"],
                    key=f"up_{sec_name}",
                )

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
                    if ad_store.strip() and ad_offer.strip():
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
                        )
                        st.session_state.section_messages.setdefault(
                            sec_name, []
                        ).append({"role": "assistant", "content": ad_out})
                        st.rerun()
                    else:
                        st.info("اكتبي اسم المتجر ووصف العرض أولاً.")
                st.markdown("---")

            is_img_section = any(
                w in sec_name for w in ["الصور", "Image", "وێنە"]
            )
            if is_img_section and browsing_item is None:
                st.markdown("### 🖼️ توليد الصور الذكية مباشرة")
                img_idea = st.text_input(
                    "اكتبي وصف الصورة التي تريدين توليدها:",
                    key="real_img_prompt",
                )
                if st.button(
                    "✨ توليد الصورة الآن",
                    type="primary",
                    key="gen_real_img_btn",
                ):
                    if img_idea.strip():
                        with st.spinner("جاري توليد الصورة..."):
                            img_url = generate_real_image(img_idea)
                        if img_url:
                            st.session_state.generated_images.insert(
                                0, {"prompt": img_idea.strip(), "url": img_url}
                            )
                            st.rerun()
                        else:
                            st.info(
                                "تم تسجيل الفكرة بنجاح؛ تأكدي من تفعيل صلاحية"
                                " توليد الصور في حساب OpenAI الخاص بكِ لعرض"
                                " الصورة مباشرة."
                            )
                    else:
                        st.info("اكتبي وصف الصورة أولاً.")

                for item in st.session_state.generated_images[:4]:
                    st.image(
                        item["url"],
                        caption=item["prompt"],
                        use_container_width=True,
                    )
                st.markdown("---")

            is_vid_section = any(
                w in sec_name for w in ["الفيديوهات", "Video", "ڤیدیۆ"]
            )
            if is_vid_section and browsing_item is None:
                st.markdown("### 🎬 استوديو الفيديوهات والأفكار")
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
                    if vid_idea.strip():
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
                            )
                            preview_img = generate_real_image(
                                f"{vid_style} video keyframe scene: {vid_idea.strip()}"
                            )
                            video_url = generate_real_video(
                                vid_idea.strip(), vid_style
                            )
                        st.session_state.generated_videos.insert(
                            0,
                            {
                                "idea": vid_idea.strip(),
                                "style": vid_style,
                                "script": vid_plan,
                                "preview_img": preview_img,
                                "video_url": video_url,
                            },
                        )
                        st.rerun()
                    else:
                        st.info("اكتبي فكرة الفيديو أولاً.")

                for v in st.session_state.generated_videos[:3]:
                    st.markdown(f"**{v['style']}:** {v['idea']}")
                    if v.get("video_url"):
                        st.video(v["video_url"])
                    elif v.get("preview_img"):
                        st.image(
                            v["preview_img"],
                            caption="لقطة مشهد مرجعية للفيديو",
                            use_container_width=True,
                        )
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
                    st.markdown(message["content"])

            if browsing_item is None:
                user_spoken_text = None
                audio_val = st.audio_input(
                    "🎙️ تحدثِ هنا للرد الفوري:", key=f"mic_sec_{sec_name}"
                )
                user_spoken_text = transcribe_once(audio_val, f"sec_{sec_name}")

                typed_prompt = st.chat_input("اكتبي رسالتكِ هنا...")
                final_prompt = user_spoken_text if user_spoken_text else typed_prompt

                if final_prompt:
                    st.session_state.section_messages[sec_name].append(
                        {"role": "user", "content": final_prompt}
                    )
                    with st.chat_message("user"):
                        st.markdown(final_prompt)

                    with st.chat_message("assistant"):
                        full_response = get_ai_answer(
                            system_prompt,
                            st.session_state.section_messages[sec_name],
                        )
                        reply_with_voice(full_response)
                        st.session_state.section_messages[sec_name].append(
                            {"role": "assistant", "content": full_response}
                        )

    elif nav_mode == t_sec_schedule:
        st.header(t_schedule_title)
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
                        role_label = "أنتِ" if m["role"] == "user" else "BRAS AI"
                        st.markdown(f"**{role_label}:** {m['content']}")
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
                "<div class='plan-box'><h3>أسبوعي</h3><h2>$5</h2><p>صلاحية 7"
                " أيام</p></div>",
                unsafe_allow_html=True,
            )
            if st.button("اشتراك أسبوعي ($5)", key="plan_w"):
                st.session_state.is_subscribed = True
                st.session_state.subscription_plan = "أسبوعي - $5"
                st.success("تم تفعيل الباقة الأسبوعية ($5)!")
                st.rerun()
        with p2:
            st.markdown(
                "<div class='plan-box'><h3>شهري</h3><h2>$15</h2><p>صلاحية 30"
                " يوماً</p></div>",
                unsafe_allow_html=True,
            )
            if st.button("اشتراك شهري ($15)", key="plan_m"):
                st.session_state.is_subscribed = True
                st.session_state.subscription_plan = "شهري - $15"
                st.success("تم تفعيل الباقة الشهرية ($15)!")
                st.rerun()
        with p3:
            st.markdown(
                "<div class='plan-box'><h3>سنوي</h3><h2>$99</h2><p>صلاحية 365"
                " يوماً</p></div>",
                unsafe_allow_html=True,
            )
            if st.button("اشتراك سنوي ($99)", key="plan_y"):
                st.session_state.is_subscribed = True
                st.session_state.subscription_plan = "سنوي - $99"
                st.success("تم تفعيل الباقة السنوية ($99)!")
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
                st.session_state.username = new_name
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
