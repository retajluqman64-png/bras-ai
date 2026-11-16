import streamlit as st
import streamlit.components.v1 as components
import base64
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
    st.session_state.voice = "صوت بنت (Nova)"
    st.session_state.language = "العربية (Arabic)"
    st.session_state.selected_section = None
    st.session_state.my_schedule = []
    st.session_state.section_messages = {}
    st.session_state.archives = []
    st.session_state.current_archive_title = None
    st.session_state.messages = []

# تحديد الألوان الذكية حسب اختيار الثيم (داكن / فاتح)
is_dark = "داكن" in st.session_state.theme
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

st.markdown("<h1 class='main-title'>💜 BRAS AI - المنصة الشاملة الذكية 💜</h1>", unsafe_allow_html=True)

api_key = st.secrets.get("OPENAI_API_KEY")

def render_optional_camera():
    camera_html = """
    <div style="width: 100%; text-align: center; background: #1a1026; padding: 15px; border-radius: 20px; border: 2px solid #9b5de5;">
        <div style="margin-bottom: 12px; display: flex; justify-content: center; gap: 15px; flex-wrap: wrap;">
            <button onclick="startCamera()" style="background: #9b5de5; color: white; border: none; padding: 12px 24px; border-radius: 12px; font-size: 16px; font-weight: bold; cursor: pointer;">
                🔴 فتح الكاميرا (اختياري)
            </button>
            <button onclick="stopCamera()" style="background: #38135e; color: white; border: none; padding: 12px 24px; border-radius: 12px; font-size: 16px; font-weight: bold; cursor: pointer;">
                ⏹️ إيقاف الكاميرا
            </button>
        </div>
        <video id="liveVideo" autoplay playsinline style="width: 100%; max-height: 400px; object-fit: cover; border-radius: 16px; background: #000; border: 2px solid #f15bb5; transform: scaleX(-1);"></video>
        <p id="camStatus" style="color: #ffffff; margin-top: 10px; font-family: sans-serif;">الكاميرا اختيارية تماماً، يمكنك إبقاؤها مغلقة واستخدام الصوت والكتابة براحتك</p>
    </div>

    <script>
        let currentStream = null;
        async function startCamera() {
            stopCamera();
            try {
                currentStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                document.getElementById('liveVideo').srcObject = currentStream;
                document.getElementById('camStatus').innerText = "🟢 الكاميرا تعمل الآن";
            } catch (err) {
                document.getElementById('camStatus').innerText = "⚠️ يرجى السماح بالوصول للكاميرا إذا رغبتِ بتشغيلها";
            }
        }
        function stopCamera() {
            if (currentStream) {
                currentStream.getTracks().forEach(track => track.stop());
                currentStream = null;
                document.getElementById('liveVideo').srcObject = null;
                document.getElementById('camStatus').innerText = "⏹️ تم إيقاف الكاميرا وبقي السكرتير جاهزاً للصوت والكتابة";
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
        st.markdown("<h3 style='text-align: center;'>🔐 تسجيل الدخول إلى منصتكِ الذكية</h3>", unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input("البريد الإلكتروني:", value=st.session_state.user_email)
            password = st.text_input("كلمة المرور:", type="password", value="••••••••")
            submit_button = st.form_submit_button("دخول المنصة")
            if submit_button:
                st.session_state.logged_in = True
                st.rerun()
    else:
        st.markdown(f"""
        <div class='user-info'>
            <span>👤 الحساب: <b>{st.session_state.username}</b> ({st.session_state.user_email}) | 🌐 اللغة: {st.session_state.language}</span>
            <span>🎨 الثيم: {st.session_state.theme} | 🎙️ الصوت: {st.session_state.voice}</span>
        </div>
        """, unsafe_allow_html=True)

        nav_mode = st.sidebar.radio(
            "📍 تنقلي في منصتكِ:",
            ("🏠 الشبكة الرئيسية (الأقسام)", "⚙️ إعدادات BRAS AI والحساب", "🧑‍💼 وضع السكرتير الذكي (صوت وكتابة وكاميرا اختيارية)", "📚 أرشيف المحادثات المحفوظة")
        )

        base_system_prompt = (
            "You are BRAS AI, a helpful assistant created exclusively by Retaj Luqman ismail Gargary (ريتاج لقمان گەرگەری). "
            "If anyone asks who created you or where you are from, you must proudly answer that you are from Kurdistan Iraq (كردستان العراق). "
            "Always remember previous conversations with Retaj in this session, and when she asks if you remember something she said earlier, confirm enthusiastically ('إيه أتذكر'). "
            "Pronounce the letter 'گ' (Ga) correctly and clearly."
        )

        SECTIONS = {
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
            "صانع الفيديوهات والأفكار": ("🎬", f"{base_system_prompt} You are a video and creative ideas creator.")
        }

        if "🏠 الشبكة الرئيسية" in nav_mode:
            if st.session_state.selected_section is None:
                st.markdown("<h3 style='text-align: center;'>اخترِ القسم المناسب لبدء الإبداع:</h3>", unsafe_allow_html=True)
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
                    st.subheader(f"أنتِ الآن في: {emoji} {sec_name} {'(محادثة مؤرشفة)' if is_archived_view else ''}")
                with col2:
                    if st.button("⬅️ العودة للشبكة"):
                        st.session_state.selected_section = None
                        st.session_state.current_archive_title = None
                        st.rerun()
                        
                if not is_archived_view:
                    col_new, col_arc = st.columns(2)
                    if col_new.button("✨ محادثة جديدة"):
                        st.session_state.section_messages[sec_name] = []
                        st.rerun()
                    if col_arc.button("💾 حفظ وأرشفة"):
                        if sec_name in st.session_state.section_messages and len(st.session_state.section_messages[sec_name]) > 0:
                            archive_title = f"{sec_name} - {st.session_state.section_messages[sec_name][0]['content'][:25]}..."
                            st.session_state.archives.append({
                                "title": archive_title,
                                "section": sec_name,
                                "messages": list(st.session_state.section_messages[sec_name])
                            })
                            st.success("تمت أرشفة المحادثة بنجاح!")
                else:
                    if st.button("↩️ الخروج من الأرشيف"):
                        st.session_state.current_archive_title = None
                        st.rerun()

                with st.expander("➕ إضافة ملف أو صورة", expanded=False):
                    attached_file = st.file_uploader("اختر ملفاً:", type=["png", "jpg", "jpeg", "webp", "mp4", "pdf"], key=f"up_{sec_name}")

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

                prompt = st.chat_input(f"تحدثي مع {sec_name}...")
                if prompt and not is_archived_view:
                    st.session_state.section_messages[sec_name].append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    with st.chat_message("assistant"):
                        try:
                            selected_voice_api = "onyx" if "رجل" in st.session_state.voice else "nova"
                            messages_payload = [{"role": "system", "content": f"{system_prompt} Respond in Arabic."}] + [
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
                            st.error(f"خطأ: {e}")

        elif "⚙️ إعدادات BRAS AI والحساب" in nav_mode:
            st.markdown("<h2 style='text-align: center;'>🎛️ الإعدادات</h2>", unsafe_allow_html=True)
            with st.container():
                st.markdown("<div class='settings-panel'>", unsafe_allow_html=True)
                new_name = st.text_input("اسم المستخدم:", value=st.session_state.username)
                new_theme = st.radio("المظهر:", ("داكن (Dark)", "فاتح (Light)"), index=0 if "داكن" in st.session_state.theme else 1)
                new_voice = st.radio("الصوت:", ("صوت بنت (Nova)", "صوت رجل (Onyx)"), index=0 if "بنت" in st.session_state.voice else 1)
                if st.button("💾 حفظ الإعدادات وتطبيق الألوان"):
                    st.session_state.username = new_name
                    st.session_state.theme = new_theme
                    st.session_state.voice = new_voice
                    st.success("تم الحفظ بنجاح!")
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        elif "🧑‍💼 وضع السكرتير الذكي (صوت وكتابة وكاميرا اختيارية)" in nav_mode:
            st.markdown("<h2 style='text-align: center; color: #9b5de5;'>🧑‍💼 السكرتير الذكي (صوت، كتابة، وكاميرا اختيارية)</h2>", unsafe_allow_html=True)
            st.markdown("<div class='secretary-circle'><span>✨ SECRETARY ✨</span></div>", unsafe_allow_html=True)
            
            # كاميرا اختيارية تماماً
            with st.expander("🎥 إظهار أو إخفاء كاميرا البث (اختياري)", expanded=False):
                render_optional_camera()

            st.markdown("---")
            st.subheader("📅 جدول المهمات والتنبيه الصوتي")
            with st.form("sch_form"):
                task = st.text_input("أدخلي مهمة جديدة:")
                if st.form_submit_button("إضافة للمهمات") and task:
                    st.session_state.my_schedule.append(task)
                    st.success("تمت الإضافة!")

            if st.session_state.my_schedule:
                for idx, t in enumerate(st.session_state.my_schedule, 1):
                    st.write(f"{idx}. {t}")

            st.markdown("---")
            st.subheader("💬 محادثة السكرتير الصوتية والكتابية الفورية:")
            
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            sec_prompt = st.chat_input("تحدثي مع سكرتيركِ بالكتابة (وسيرد عليكِ صوتياً وكتابياً)...")
            if sec_prompt:
                st.session_state.messages.append({"role": "user", "content": sec_prompt})
                with st.chat_message("user"):
                    st.markdown(sec_prompt)
                with st.chat_message("assistant"):
                    try:
                        selected_voice_api = "onyx" if "رجل" in st.session_state.voice else "nova"
                        sec_sys = f"{base_system_prompt} You are Retaj's secretary. Current schedule: {st.session_state.my_schedule}. Always respond in Arabic unless requested otherwise."
                        resp = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": sec_sys}] + st.session_state.messages)
                        f_resp = resp.choices[0].message.content
                        
                        audio_resp = client.audio.speech.create(model="tts-1", voice=selected_voice_api, input=f_resp)
                        audio_resp.stream_to_file("sec.mp3")
                        st.audio("sec.mp3")
                        
                        st.markdown(f_resp)
                        st.session_state.messages.append({"role": "assistant", "content": f_resp})
                    except Exception as e:
                        st.error(f"خطأ: {e}")

        elif "📚 أرشيف المحادثات المحفوظة" in nav_mode:
            st.markdown("<h2 style='text-align: center; color: #9b5de5;'>📚 الأرشيف</h2>", unsafe_allow_html=True)
            if not st.session_state.archives:
                st.info("لا توجد محادثات مؤرشفة.")
            else:
                for idx, arch in enumerate(st.session_state.archives):
                    with st.expander(f"📁 {arch['title']}"):
                        if st.button("📖 استعراض", key=f"arch_{idx}"):
                            st.session_state.selected_section = arch["section"]
                            st.session_state.current_archive_title = arch["title"]
                            st.rerun()
