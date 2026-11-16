import streamlit as st
import streamlit.components.v1 as components
import base64
from datetime import datetime
from openai import OpenAI

# إعداد الصفحة لتكون واسعة بالكامل
st.set_page_config(
    page_title="BRAS AI - المنصة الشاملة الذكية",
    page_icon="💜",
    layout="wide"
)

# إدارة الحالة لتخزين الذاكرة والجدول
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = "ريتاج لقمان گەرگەری"
    st.session_state.user_email = "retaj@brasai.com"
    st.session_state.theme = "داكن (Dark)"
    st.session_state.voice = "صوت بنت نقي وواضح (Nova)"
    st.session_state.language = "العربية (Arabic)"
    st.session_state.selected_section = None
    st.session_state.my_schedule = []
    st.session_state.section_messages = {}
    st.session_state.archives = []
    st.session_state.current_archive_title = None
    st.session_state.messages = []

# ترجمة نصوص الواجهة والأقسام بالكامل حسب اللغة المختارة
lang = st.session_state.language

if "English" in lang:
    t_title = "💜 BRAS AI - Smart Comprehensive Platform 💜"
    t_login_title = "🔐 Login to Your Smart Platform"
    t_email = "Email:"
    t_password = "Password:"
    t_login_btn = "Login"
    t_nav = "Navigate Your Platform:"
    t_sec_main = "🏠 Main Grid (Sections)"
    t_sec_settings = "⚙️ BRAS AI & Account Settings"
    t_sec_secretary = "🧑‍💼 Smart Secretary (Voice, Mic & Optional Camera)"
    t_sec_archive = "📚 Saved Archives"
    t_account = "Account"
    t_lang_label = "App Language"
    t_theme = "Theme"
    t_voice = "Voice"
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
        "قسم الرسم وتصميم الصور": "Art & Design",
        "صانع الفيديوهات والأفكار": "Video & Ideas Creator (AI Video Engine)"
    }
elif "Kurdish" in lang:
    t_title = "💜 BRAS AI - سەکۆی گشتگیری هۆشمەند 💜"
    t_login_title = "🔐 چوونه‌ژووره‌وه‌ بۆ سەکۆ هۆشمەندەکەت"
    t_email = "ئیمەیڵ:"
    t_password = "وشەی نهێنی:"
    t_login_btn = "چوونه‌ژووره‌وه‌"
    t_nav = "گه‌شت بكه‌ له‌ سەکۆکەت:"
    t_sec_main = "🏠 تۆڕی سەرەکی (بەشەکان)"
    t_sec_settings = "⚙️ ڕێکخستنەکانی BRAS AI"
    t_sec_secretary = "🧑‍💼 ئەمینداری هۆشمەند (دەنگ، مایکرۆفۆن و کامێرا)"
    t_sec_archive = "📚 ئەرشیفی گفتوگۆکان"
    t_account = "هەژمار"
    t_lang_label = "زمانی بەرنامە"
    t_theme = "ڕوکار"
    t_voice = "دەنگ"
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
        "قسم الرسم وتصميم الصور": "هونەر و دیزاین",
        "صانع الفيديوهات والأفكار": "دروستکەری ڤیدیۆ (مۆدێلی AI)"
    }
elif "Türkçe" in lang:
    t_title = "💜 BRAS AI - Akıllı Kapsamlı Platform 💜"
    t_login_title = "🔐 Akıllı Platformunuza Giriş Yapın"
    t_email = "E-posta:"
    t_password = "Şifre:"
    t_login_btn = "Giriş Yap"
    t_nav = "Platformda Gezin:"
    t_sec_main = "🏠 Ana Izgara (Bölümler)"
    t_sec_settings = "⚙️ BRAS AI ve Hesap Ayarları"
    t_sec_secretary = "🧑‍💼 Akıllı Sekreter (Ses, Mikrofon ve Kamera)"
    t_sec_archive = "📚 Kayıtlı Arşivler"
    t_account = "Hesap"
    t_lang_label = "Uygulama Dili"
    t_theme = "Tema"
    t_voice = "Ses"
    t_settings_header = "⚙️ Ayarlar"
    t_username = "Kullanıcı Adı:"
    t_save = "Ayarları Kaydet ve Uygula"
    t_saved_ok = "Ayarlar başarıyla kaydedildi!"
    t_secretary_title = "🧑‍💼 Akıllı Sekreter (Çok Dilli, Mikrofon ve Uyarılar)"
    t_schedule_title = "📅 Gün ve Saat İçeren Görev Programı"
    t_task_input = "Bir görev girin:"
    t_day_label = "Gün Seçin:"
    t_time_label = "Saat:"
    t_add_task_btn = "Görevi Ekle"
    t_task_added = "Görev başarıyla eklendi!"
    t_schedule_list = "📌 Kayıtlı Görevleriniz:"
    t_mic_prompt = "🎙️ Sekreterinizle konuşmak için mikrofona tıklayın:"
    t_type_prompt = "Veya buraya yazın..."
    t_choose_sec = "Başlamak için uygun bölümü seçin:"
    t_back_grid = "⬅️ Izgaraya Dön"
    t_new_chat = "✨ Yeni Sohbet"
    t_archive_btn = "💾 Kaydet ve Arşivle"
    t_archived_ok = "Sohbet arşivlendi!"
    t_exit_arch = "↩️ Arşivden Çık"
    t_file_upload = "➕ Dosya veya Resim Ekle"
    t_archive_header = "📚 Arşiv"
    t_no_archive = "Arşivlenmiş sohbet yok."
    t_browse = "📖 Gözat"

    SECTIONS_NAMES = {
        "المساعد الشامل": "Genel Asistan",
        "المعلم الشامل": "Okul Öğretmeni",
        "قسم كرة القدم": "Futbol (FC Barcelona)",
        "تعليم اللغات": "Dil Eğitimi",
        "البرمجة": "Programlama",
        "الطبخ والوصفات": "Yemek Tarifleri",
        "مكياج وسكين كير": "Makyaj ve Cilt Bakımı",
        "ديزاين وملابس وشوبينغ": "Moda ve Alışveriş",
        "أفكار دول وسفرات": "Seyahat Planlayıcı",
        "قسم التاريخ": "Tarih Uzmanı",
        "الصحة، الدايت والجيم": "Sağlık ve Fitness",
        "نصائح وتطوير الذات": "Kişisel Gelişim",
        "قسم الرسم وتصميم الصور": "Sanat ve Tasarım",
        "صانع الفيديوهات والأفكار": "Video ve Fikir Üreticisi (AI Video)"
    }
else:
    t_title = "💜 BRAS AI - المنصة الشاملة الذكية 💜"
    t_login_title = "🔐 تسجيل الدخول إلى منصتكِ الذكية"
    t_email = "البريد الإلكتروني:"
    t_password = "كلمة المرور:"
    t_login_btn = "دخول المنصة"
    t_nav = "📍 تنقلي في منصتكِ:"
    t_sec_main = "🏠 الشبكة الرئيسية (الأقسام)"
    t_sec_settings = "⚙️ إعدادات BRAS AI والحساب"
    t_sec_secretary = "🧑‍💼 وضع السكرتير الذكي (صوت، ميكروفون، وكاميرا اختيارية)"
    t_sec_archive = "📚 أرشيف المحادثات المحفوظة"
    t_account = "الحساب"
    t_lang_label = "🌐 لغة التطبيق وتفضيل المحادثة (أكثر من 40 لغة):"
    t_theme = "المظهر:"
    t_voice = "الصوت:"
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
        "قسم الرسم وتصميم الصور": "قسم الرسم وتصميم الصور",
        "صانع الفيديوهات والأفكار": "صانع الفيديوهات والأفكار (مولد الفيديوهات الذكي)"
    }

# تحديد الألوان الذكية حسب اختيار الثيم (داكن / فاتح)
is_dark = "داكن" in st.session_state.theme or "Dark" in st.session_state.theme
bg_color = "#0d0614" if is_dark else "#fcf8ff"
text_color = "#ffffff" if is_dark else "#111111"
card_bg = "#1a1026" if is_dark else "#ffffff"
border_color = "#9b5de5"
accent_color = "#9b5de5"

st.markdown(f"""
<style>
.stApp {{
    background-color: {bg_color};
    color: {text_color};
}}
.main-title {{
    text-align: center;
    color: {accent_color};
    font-weight: bold;
    font-size: 3rem;
    margin-bottom: 20px;
}}
.user-info {{
    background-color: {card_bg};
    color: {text_color};
    padding: 15px;
    border-radius: 15px;
    border: 1px solid {border_color};
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 10px rgba(155, 93, 229, 0.2);
}}
.stButton>button {{
    width: 100%;
    height: 110px;
    background-color: {card_bg};
    color: {text_color};
    border: 2px solid {border_color};
    border-radius: 20px;
    font-size: 1.1rem;
    font-weight: bold;
    transition: 0.3s;
    box-shadow: 0 4px 15px rgba(155, 93, 229, 0.3);
}}
.stButton>button:hover {{
    background-color: {accent_color};
    color: #ffffff;
    border-color: #f15bb5;
    box-shadow: 0 6px 25px rgba(241, 91, 181, 0.5);
    transform: translateY(-4px);
}}
.secretary-circle {{
    width: 200px;
    height: 200px;
    border-radius: 50%;
    background: radial-gradient(circle, #9b5de5, #38135e, #0d0614);
    margin: 20px auto;
    display: flex;
    justify-content: center;
    align-items: center;
    color: white;
    font-weight: bold;
    font-size: 1.2rem;
    text-align: center;
    box-shadow: 0 0 60px #9b5de5, inset 0 0 30px #f15bb5;
    animation: pulse 2s infinite;
}}
@keyframes pulse {{
    0% {{ transform: scale(1); box-shadow: 0 0 40px #9b5de5; }}
    50% {{ transform: scale(1.08); box-shadow: 0 0 80px #f15bb5; }}
    100% {{ transform: scale(1); box-shadow: 0 0 40px #9b5de5; }}
}}
.settings-panel {{
    background-color: {card_bg};
    color: {text_color};
    padding: 20px;
    border-radius: 20px;
    border: 2px solid {border_color};
    margin-top: 20px;
}}
p, span, label, h1, h2, h3, h4 {{
    color: {text_color} !important;
}}
</style>
""", unsafe_allow_html=True)

st.markdown(f"<h1 class='main-title'>{t_title}</h1>", unsafe_allow_html=True)

api_key = st.secrets.get("OPENAI_API_KEY")

def render_optional_camera():
    camera_html = """
    <div style="width: 100%; text-align: center; background: #1a1026; padding: 15px; border-radius: 20px; border: 2px solid #9b5de5;">
        <div style="margin-bottom: 12px; display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
            <button onclick="startCamera()" style="background: #9b5de5; color: white; border: none; padding: 12px 24px; border-radius: 12px; font-size: 16px; font-weight: bold; cursor: pointer;">
                🔴 Camera On
            </button>
            <button onclick="stopCamera()" style="background: #38135e; color: white; border: none; padding: 12px 24px; border-radius: 12px; font-size: 16px; font-weight: bold; cursor: pointer;">
                ⏹️ Stop Camera
            </button>
        </div>
        <video id="liveVideo" autoplay playsinline style="width: 100%; max-height: 400px; object-fit: cover; border-radius: 16px; background: #000; border: 2px solid #f15bb5; transform: scaleX(-1);"></video>
        <p id="camStatus" style="color: #ffffff; margin-top: 10px; font-family: sans-serif;">Optional Camera</p>
    </div>

    <script>
        let currentStream = null;
        async function startCamera() {
            stopCamera();
            try {
                currentStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                document.getElementById('liveVideo').srcObject = currentStream;
                document.getElementById('camStatus').innerText = "🟢 Camera Active";
            } catch (err) {
                document.getElementById('camStatus').innerText = "⚠️ Please allow camera access";
            }
        }
        function stopCamera() {
            if (currentStream) {
                currentStream.getTracks().forEach(track => track.stop());
                currentStream = null;
                document.getElementById('liveVideo').srcObject = null;
                document.getElementById('camStatus').innerText = "⏹️ Camera Stopped";
            }
        }
    </script>
    """
    components.html(camera_html, height=520)

if not api_key:
    st.error("يرجى ضبط مفتاح OpenAI API في إعدادات Streamlit Secrets.")
else:
    client = OpenAI(api_key=api_key)

    if not st.session_state.logged_in:
        st.markdown(f"<h3 style='text-align: center;'>{t_login_title}</h3>", unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input(t_email, value=st.session_state.user_email)
            password = st.text_input(t_password, type="password", value="••••••••")
            submit_button = st.form_submit_button(t_login_btn)
            if submit_button:
                st.session_state.logged_in = True
                st.rerun()
    else:
        st.markdown(f"""
        <div class='user-info'>
            <span>👤 {t_account}: <b>{st.session_state.username}</b> ({st.session_state.user_email}) | 🌐 Lang: {st.session_state.language}</span>
            <span>🎨 Theme: {st.session_state.theme} | 🎙️ Voice: {st.session_state.voice}</span>
        </div>
        """, unsafe_allow_html=True)

        nav_mode = st.sidebar.radio(
            t_nav,
            (t_sec_main, t_sec_settings, t_sec_secretary, t_sec_archive)
        )

        base_system_prompt = (
            f"You are BRAS AI, a helpful assistant created exclusively by Retaj Luqman ismail Gargary (ريتاج لقمان گەرگەری). "
            f"If anyone asks who created you or where you are from, you must proudly answer that you are from Kurdistan Iraq (كردستان العراق). "
            f"The current user language setting is: {st.session_state.language}. Respond fluently in this language. "
            "Always remember previous conversations with Retaj in this session, and when she asks if you remember something she said earlier, confirm enthusiastically ('إيه أتذكر'). "
            "Pronounce the letter 'گ' (Ga) correctly and clearly."
        )

        BASE_SECTIONS = {
            "المساعد الشامل": ("🤖", f"{base_system_prompt} You are a versatile assistant."),
            "المعلم الشامل": ("📚", f"{base_system_prompt} You are an expert school teacher."),
            "قسم كرة القدم": ("⚽", f"{base_system_prompt} You are an expert football analyst covering FC Barcelona."),
            "تعليم اللغات": ("🗣️", f"{base_system_prompt} You are a multilingual tutor."),
            "البرمجة": ("💻", f"{base_system_prompt} You are an expert programmer."),
            "الطبخ والوصفات": ("🍳", f"{base_system_prompt} You are a master chef."),
            "مكياج وسكين كير": ("💄", f"{base_system_prompt} You are an expert makeup artist and skincare consultant."),
            "ديزاين وملابس وشوبينغ": ("🛍️", f"{base_system_prompt} You are a fashion designer and shopping advisor."),
            "أفكار دول وسفرات": ("✈️", f"{base_system_prompt} You are a travel planner expert."),
            "قسم التاريخ": ("📜", f"{base_system_prompt} You are a historian expert."),
            "الصحة، الدايت والجيم": ("💪", f"{base_system_prompt} You are a fitness coach."),
            "نصائح وتطوير الذات": ("💡", f"{base_system_prompt} You are a life advisor."),
            "قسم الرسم وتصميم الصور": ("🎨", f"{base_system_prompt} You are an art assistant."),
            "صانع الفيديوهات والأفكار": ("🎬", f"{base_system_prompt} You are an advanced AI video producer and script/idea generator, creating professional video storyboards and voice scripts.")
        }

        # بناء الأقسام مع الأسماء المترجمة
        SECTIONS = {}
        for orig_key, (emoji, prompt) in BASE_SECTIONS.items():
            translated_name = SECTIONS_NAMES.get(orig_key, orig_key)
            SECTIONS[translated_name] = (emoji, prompt)

        if t_sec_main in nav_mode:
            if st.session_state.selected_section is None:
                st.markdown(f"<h3 style='text-align: center;'>{t_choose_sec}</h3>", unsafe_allow_html=True)
                cols = st.columns(3)
                section_items = list(SECTIONS.items())
                
                for index, (sec_name, (emoji, prompt)) in enumerate(section_items):
                    col = cols[index % 3]
                    if col.button(f"{emoji}\n\n{sec_name}", key=f"sec_btn_{index}"):
                        st.session_state.selected_section = sec_name
                        st.session_state.current_archive_title = None
                        st.rerun()
            else:
                sec_name = st.session_state.selected_section
                emoji, system_prompt = SECTIONS[sec_name]
                is_archived_view = st.session_state.current_archive_title is not None
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(f"{sec_name} {emoji}")
                with col2:
                    if st.button(t_back_grid):
                        st.session_state.selected_section = None
                        st.session_state.current_archive_title = None
                        st.rerun()
                        
                if not is_archived_view:
                    col_new, col_arc = st.columns(2)
                    if col_new.button(t_new_chat):
                        st.session_state.section_messages[sec_name] = []
                        st.rerun()
                    if col_arc.button(t_archive_btn):
                        if sec_name in st.session_state.section_messages and len(st.session_state.section_messages[sec_name]) > 0:
                            archive_title = f"{sec_name} - {st.session_state.section_messages[sec_name][0]['content'][:25]}..."
                            st.session_state.archives.append({
                                "title": archive_title,
                                "section": sec_name,
                                "messages": list(st.session_state.section_messages[sec_name])
                            })
                            st.success(t_archived_ok)
                else:
                    if st.button(t_exit_arch):
                        st.session_state.current_archive_title = None
                        st.rerun()

                with st.expander(t_file_upload, expanded=False):
                    attached_file = st.file_uploader("File:", type=["png", "jpg", "jpeg", "webp", "mp4", "pdf"], key=f"up_{sec_name}")

                if is_archived_view:
                    active_messages = []
                    for arch in st.session_state.archives:
                        if arch["title"] == st.session_state.current_archive_title:
                            active_messages = arch["messages"]
                            break
                else:
                    if sec_name not in st.session_state.section_messages:
                        st.session_state.section_messages[sec_name] = []
                    active_messages = st.session_state.section_messages[sec_name]

                for message in active_messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                user_spoken_text = None
                if not is_archived_view:
                    audio_val = st.audio_input("🎙️ Mic Input:", key=f"mic_sec_{sec_name}")
                    if audio_val:
                        try:
                            transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_val)
                            user_spoken_text = transcription.text
                        except Exception as e:
                            st.error(f"Error: {e}")

                typed_prompt = st.chat_input("Type here...")
                final_prompt = user_spoken_text if user_spoken_text else typed_prompt

                if final_prompt and not is_archived_view:
                    st.session_state.section_messages[sec_name].append({"role": "user", "content": final_prompt})
                    with st.chat_message("user"):
                        st.markdown(final_prompt)

                    with st.chat_message("assistant"):
                        try:
                            selected_voice_api = "onyx" if "رجل" in st.session_state.voice or "Onyx" in st.session_state.voice else "nova"
                            messages_payload = [{"role": "system", "content": f"{system_prompt} Respond fluently in {st.session_state.language}."}] + [
                                {"role": m["role"], "content": m["content"]} for m in st.session_state.section_messages[sec_name]
                            ]
                            response = client.chat.completions.create(model="gpt-4o", messages=messages_payload)
                            full_response = response.choices[0].message.content
                            
                            audio_resp = client.audio.speech.create(model="tts-1", voice=selected_voice_api, input=full_response)
                            audio_resp.stream_to_file("resp.mp3")
                            st.audio("resp.mp3")
                            
                            st.markdown(full_response)
                            st.session_state.section_messages[sec_name].append({"role": "assistant", "content": full_response})
                        except Exception as e:
                            st.error(f"Error: {e}")

        elif t_sec_settings in nav_mode:
            st.markdown(f"<h2 style='text-align: center;'>{t_settings_header}</h2>", unsafe_allow_html=True)
            with st.container():
                st.markdown("<div class='settings-panel'>", unsafe_allow_html=True)
                new_name = st.text_input(t_username, value=st.session_state.username)
                new_theme = st.radio(t_theme, ("داكن (Dark)", "فاتح (Light)"), index=0 if "داكن" in st.session_state.theme or "Dark" in st.session_state.theme else 1)
                new_voice = st.radio(t_voice, ("صوت بنت نقي وواضح (Nova)", "صوت رجل نقي وواضح (Onyx)"), index=0 if "بنت" in st.session_state.voice or "Nova" in st.session_state.voice else 1)
                
                languages_40 = [
                    "العربية (Arabic)", "الإنجليزية (English)", "الكوردية (Kurdish Badini)", "التركية (Türkçe)",
                    "الفرنسية (Français)", "الألمانية (Deutsch)", "الإسبانية (Español)", "الإيطالية (Italiano)",
                    "الروسية (Русский)", "الصينية المبسطة (中文)", "اليابانية (日本語)", "الكورية (한국어)",
                    "الفارسية (فارسی)", "الأوردو (اردو)", "الهندية (हिन्दी)", "البرتغالية (Português)",
                    "البنغالية (বাংলা)", "البنجابية (ਪੰਜਾਬੀ)", "الإندونيسية (Bahasa Indonesia)", "الماليزية (Bahasa Melayu)",
                    "الفيتنامية (Tiếng Việt)", "التايلاندية (ไทย)", "الهولندية (Nederlands)", "البولندية (Polski)",
                    "الأوكرانية (Українська)", "اليونانية (Ελληνικά)", "السويدية (Svenska)", "النرويجية (Norsk)",
                    "الدنماركية (Dansk)", "الفنلندية (Suomi)", "المجرية (Magyar)", "التشيكية (Čeština)",
                    "الرومانية (Română)", "البلغارية (Български)", "السلوفاكية (Slovenčina)", "الكرواتية (Hrvatski)",
                    "العبرية (עברית)", "الفلبينية (Tagalog)", "السواحلية (Kiswahili)", "الأمهرية (አማርኛ)"
                ]
                
                current_lang_idx = languages_40.index(st.session_state.language) if st.session_state.language in languages_40 else 0
                new_lang = st.selectbox(t_lang_label, languages_40, index=current_lang_idx)

                st.markdown("---")
                st.checkbox("Enable notifications on app open", value=True)

                if st.button(t_save):
                    st.session_state.username = new_name
                    st.session_state.theme = new_theme
                    st.session_state.voice = new_voice
                    st.session_state.language = new_lang
                    st.success(t_saved_ok)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        elif t_sec_secretary in nav_mode:
            st.markdown(f"<h2 style='text-align: center; color: #9b5de5;'>{t_secretary_title}</h2>", unsafe_allow_html=True)
            st.markdown("<div class='secretary-circle'><span>✨ SECRETARY ✨</span></div>", unsafe_allow_html=True)
            
            with st.expander("🎥 Camera / الكاميرا", expanded=False):
                render_optional_camera()

            st.markdown("---")
            st.subheader(t_schedule_title)
            
            with st.form("sch_form"):
                task_desc = st.text_input(t_task_input)
                col_d, col_t = st.columns(2)
                with col_d:
                    task_day = st.selectbox(t_day_label, ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"])
                with col_t:
                    task_time = st.text_input(t_time_label, value="12:00")

                if st.form_submit_button(t_add_task_btn) and task_desc:
                    full_task_info = f"📅 {task_day} - {task_time} ⏰ - {task_desc}"
                    st.session_state.my_schedule.append(full_task_info)
                    st.success(t_task_added)

            if st.session_state.my_schedule:
                st.info(t_schedule_list)
                for idx, t in enumerate(st.session_state.my_schedule, 1):
                    st.write(f"{idx}. {t}")

            st.markdown("---")
            st.subheader(t_mic_prompt)
            
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            sec_spoken_text = None
            sec_audio_val = st.audio_input("🎙️ Mic:", key="mic_secretary")
            if sec_audio_val:
                try:
                    transcription = client.audio.transcriptions.create(model="whisper-1", file=sec_audio_val)
                    sec_spoken_text = transcription.text
                except Exception as e:
                    st.error(f"Error: {e}")

            sec_typed_prompt = st.chat_input(t_type_prompt)
            final_sec_prompt = sec_spoken_text if sec_spoken_text else sec_typed_prompt

            if final_sec_prompt:
                st.session_state.messages.append({"role": "user", "content": final_sec_prompt})
                with st.chat_message("user"):
                    st.markdown(final_sec_prompt)
                with st.chat_message("assistant"):
                    try:
                        selected_voice_api = "onyx" if "رجل" in st.session_state.voice or "Onyx" in st.session_state.voice else "nova"
                        sec_sys = f"{base_system_prompt} You are Retaj's smart secretary. Current language setting: {st.session_state.language}. Current schedule: {st.session_state.my_schedule}. Always respond fluently in {st.session_state.language}."
                        resp = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": sec_sys}] + st.session_state.messages)
                        f_resp = resp.choices[0].message.content
                        
                        audio_resp = client.audio.speech.create(model="tts-1", voice=selected_voice_api, input=f_resp)
                        audio_resp.stream_to_file("sec.mp3")
                        st.audio("sec.mp3")
                        
                        st.markdown(f_resp)
                        st.session_state.messages.append({"role": "assistant", "content": f_resp})
                    except Exception as e:
                        st.error(f"Error: {e}")

        elif t_sec_archive in nav_mode:
            st.markdown(f"<h2 style='text-align: center; color: #9b5de5;'>{t_archive_header}</h2>", unsafe_allow_html=True)
            if not st.session_state.archives:
                st.info(t_no_archive)
            else:
                for idx, arch in enumerate(st.session_state.archives):
                    with st.expander(f"📁 {arch['title']}"):
                        if st.button(t_browse, key=f"arch_{idx}"):
                            st.session_state.selected_section = arch["section"]
                            st.session_state.current_archive_title = arch["title"]
                            st.rerun()
