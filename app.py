import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta
from openai import OpenAI

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
    "username": "ريتاج لقمان گەرگەری",
    "user_email": "retaj@brasai.com",
    "theme": "داكن (Dark)",
    "voice": "صوت بنت نقي وواضح (Nova)",
    "language": "العربية (Arabic)",
    "screen_mode": "عادي (Normal)",
    "selected_section": None,
    "my_schedule": [],
    "section_messages": {},
    "archives": [],
    "current_archive_title": None,
    "messages": [],
    "generated_images": [],
    "processed_audio_ids": [],
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

lang = st.session_state.language
is_screen_mode = "شاشة" in st.session_state.screen_mode or "Screen" in st.session_state.screen_mode

if "English" in lang:
    t_title = "💜 BRAS AI - Smart Comprehensive Platform 💜"
    t_login_title = "🔐 Login to Your Smart Platform"
    t_email = "Email:"
    t_password = "Password:"
    t_login_btn = "Login / Start 24h Free Trial"
    t_logout_btn = "Logout"
    t_nav = "Navigate Your Platform:"
    t_sec_main = "🏠 Main Grid (Sections)"
    t_sec_pricing = "💳 Plans & Pricing"
    t_sec_secretary = "🧑‍💼 Smart Secretary (Voice, Mic & Optional Camera)"
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
    t_secretary_title = "🧑‍💼 Smart Secretary (Multilingual, Mic & Alerts)"
    t_schedule_title = "📅 Schedule with Day & Time"
    t_task_input = "Enter task (e.g., Math exam):"
    t_day_label = "Select Day:"
    t_time_label = "Time (e.g., 4:00 PM):"
    t_add_task_btn = "Add Task with Alert"
    t_task_added = "Task added successfully!"
    t_schedule_list = "📌 Your Schedule & Recorded Tasks:"
    t_mic_prompt = "🎙️ Click the microphone to speak with your secretary directly:"
    t_type_prompt = "Or type to your secretary here..."
    t_choose_sec = "Choose the right section to start creating:"
    t_back_grid = "⬅️ Back to Grid"
    t_new_chat = "✨ New Chat"
    t_archive_btn = "💾 Save & Archive"
    t_archived_ok = "Conversation archived successfully!"
    t_exit_arch = "↩️ Exit Archive"
    t_file_upload = "➕ Add File or Image"
    t_archive_header = "📚 Archives"
    t_no_archive = "No archived conversations."
    t_browse = "📖 Browse"
    art_sec_key = "Image Generation & Design"
    ads_sec_key = "Ads & Stores Studio"
    vid_sec_key = "Video & Ideas Studio"
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
        art_sec_key: "Image Generation & Design",
        vid_sec_key: "Video & Ideas Studio",
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
    t_sec_pricing = "💳 پاکێج و نرخەکان"
    t_sec_secretary = "🧑‍💼 ئەمینداری هۆشمەند (دەنگ، مایکرۆفۆن و کامێرا)"
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
    t_secretary_title = "🧑‍💼 ئەمینداری هۆشمەند (فرەزمان، مایکرۆفۆن و ئاگادارکردنەوە)"
    t_schedule_title = "📅 خشتەی ئەرکەکان بە دیاریکردنی ڕۆژ و کات"
    t_task_input = "ئەرکێک بنووسە:"
    t_day_label = "ڕۆژ هەڵبژێرە:"
    t_time_label = "کات:"
    t_add_task_btn = "زیادکردنی ئەرک"
    t_task_added = "ئەرکەکە بە سەرکەوتوویی زیادکرا!"
    t_schedule_list = "📌 خشتەی ئەرکە تۆمارکراوەکانت:"
    t_mic_prompt = "🎙️ کلیک لەسەر مایکرۆفۆن بکە بۆ قسەکردن:"
    t_type_prompt = "یان لێرە بنووسە..."
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
    art_sec_key = "دروستکردنی وێنە و دیزاین (Image)"
    ads_sec_key = "ستۆدیۆی ڕیکلام و بازاڕەکان"
    vid_sec_key = "ستۆدیۆی ڤیدیۆ و بیرۆکەکان"
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
        art_sec_key: "دروستکردنی وێنە و دیزاین (Image)",
        vid_sec_key: "ستۆدیۆی ڤیدیۆ و بیرۆکەکان",
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
    t_sec_pricing = "💳 الباقات والاشتراك"
    t_sec_secretary = "🧑‍💼 وضع السكرتير الذكي (صوت، ميكروفون، وكاميرا اختيارية)"
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
    t_secretary_title = "🧑‍💼 السكرتير الذكي (متعدد اللغات، ميكروفون، وتنبيهات)"
    t_schedule_title = "📅 جدول المهمات مع تحديد اليوم والساعة"
    t_task_input = "اكتبي المهمة (مثلاً: امتحان رياضيات أو لقاء العائلة):"
    t_day_label = "اختر اليوم:"
    t_time_label = "الساعة:"
    t_add_task_btn = "إضافة للمهمات مع التنبيه"
    t_task_added = "تمت إضافة المهمة بنجاح وسيتم تذكيركِ بها فوراً!"
    t_schedule_list = "📌 جدول مهماتكِ والمواعيد المسجلة:"
    t_mic_prompt = "🎙️ اضغطي على الميكروفون للتحدث مع السكرتير مباشرة:"
    t_type_prompt = "أو اكتبي لسكرتيركِ هنا..."
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
    vid_sec_key = "قسم الفيديوهات والأفكار"
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
        vid_sec_key: "قسم الفيديوهات والأفكار",
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
.secretary-circle {{
    width: {"210px" if is_screen_mode else "170px"};
    height: {"210px" if is_screen_mode else "170px"};
    border-radius: 50%;
    background: radial-gradient(circle, #9b5de5, #38135e, #0d0614);
    margin: 18px auto;
    display: flex;
    justify-content: center;
    align-items: center;
    color: white;
    font-weight: bold;
    font-size: 1.15rem;
    text-align: center;
    box-shadow: 0 0 55px #9b5de5, inset 0 0 25px #f15bb5;
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


def get_voice_api() -> str:
    return "onyx" if "رجل" in st.session_state.voice or "Onyx" in st.session_state.voice else "nova"


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
        except Exception as e:
            st.caption(f"تنبيه الصوت: {e}")


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
    except Exception as e:
        st.error(f"تعذر تفريغ الصوت: {e}")
        return None


def get_ai_answer(system_instruction: str, chat_history: list) -> str:
    if not client:
        return "يرجى إضافة مفتاح OPENAI_API_KEY في Streamlit Secrets لتفعيل الردود الذكية."
    payload = [
        {
            "role": "system",
            "content": (
                f"{system_instruction} "
                "Give a direct, thoughtful, and helpful answer to the user's message—never repeat or parrot what the user said. "
                f"Respond in {st.session_state.language}."
            ),
        }
    ] + [{"role": m["role"], "content": m["content"]} for m in chat_history[-10:]]
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=payload)
    return resp.choices[0].message.content


def generate_real_image(prompt_text: str, img_size: str = "1024x1024"):
    if not client:
        return None, "يرجى إضافة مفتاح OPENAI_API_KEY في Streamlit Secrets لتوليد الصور."
    try:
        img_resp = client.images.generate(
            model="gpt-image-1",
            prompt=prompt_text,
            size=img_size,
        )
        item = img_resp.data[0]
        if getattr(item, "url", None):
            return item.url, None
        if getattr(item, "b64_json", None):
            import base64
            return base64.b64decode(item.b64_json), None
        return None, "لم يتم إرجاع صورة من الخدمة."
    except Exception as e:
        return None, f"تعذر توليد الصورة: {e}"


def render_optional_camera():
    vid_h = "500px" if is_screen_mode else "380px"
    camera_html = f"""
    <div style="width: 100%; text-align: center; background: #1a1026; padding: 15px; border-radius: 20px; border: 2px solid #9b5de5;">
        <div style="margin-bottom: 12px; display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
            <button onclick="startCamera()" style="background: #9b5de5; color: white; border: none; padding: 12px 24px; border-radius: 12px; font-size: 16px; font-weight: bold; cursor: pointer;">
                🔴 Camera On
            </button>
            <button onclick="stopCamera()" style="background: #38135e; color: white; border: none; padding: 12px 24px; border-radius: 12px; font-size: 16px; font-weight: bold; cursor: pointer;">
                ⏹️ Stop Camera
            </button>
        </div>
        <video id="liveVideo" autoplay playsinline style="width: 100%; max-height: {vid_h}; object-fit: cover; border-radius: 16px; background: #000; border: 2px solid #f15bb5; transform: scaleX(-1);"></video>
        <p id="camStatus" style="color: #ffffff; margin-top: 10px; font-family: sans-serif;">Optional Camera</p>
    </div>

    <script>
        let currentStream = null;
        async function startCamera() {{
            stopCamera();
            try {{
                currentStream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                document.getElementById('liveVideo').srcObject = currentStream;
                document.getElementById('camStatus').innerText = "🟢 Camera Active";
            }} catch (err) {{
                document.getElementById('camStatus').innerText = "⚠️ Please allow camera access";
            }}
        }}
        function stopCamera() {{
            if (currentStream) {{
                currentStream.getTracks().forEach(track => track.stop());
                currentStream = null;
                document.getElementById('liveVideo').srcObject = null;
                document.getElementById('camStatus').innerText = "⏹️ Camera Stopped";
            }}
        }}
    </script>
    """
    components.html(camera_html, height=620 if is_screen_mode else 490)


if not client:
    st.warning("يرجى ضبط مفتاح `OPENAI_API_KEY` في إعدادات Streamlit Secrets لتفعيل الذكاء الاصطناعي والصور والصوت.")

if not st.session_state.logged_in:
    st.markdown(f"<h3 style='text-align: center
