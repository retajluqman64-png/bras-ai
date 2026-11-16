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
    st.session_state.language = "الكردية البادينية / Badini Kurdish"
    st.session_state.selected_section = None
    st.session_state.my_schedule = []
    st.session_state.section_messages = {}
    st.session_state.archives = []
    st.session_state.current_archive_title = None

# تحديد الألوان بناءً على الثيم المختار
bg_color = "#0d0614" if "داكن" in st.session_state.theme else "#f4edf7"
text_color = "#e0d8f0" if "داكن" in st.session_state.theme else "#1a1026"
card_bg = "#1a1026" if "داكن" in st.session_state.theme else "#ffffff"
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
    color: white;
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
    padding: 20px;
    border-radius: 20px;
    border: 2px solid {border_color};
    margin-top: 20px;
}}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>💜 BRAS AI - المنصة الشاملة الذكية 💜</h1>", unsafe_allow_html=True)

api_key = st.secrets.get("OPENAI_API_KEY")

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")

def render_media_hub():
    media_html = """
    <div style="width: 100%; text-align: center; background: #1a1026; padding: 20px; border-radius: 20px; border: 2px solid #9b5de5;">
        <div style="margin-bottom: 15px; display: flex; justify-content: center; gap: 12px; flex-wrap: wrap;">
            <button onclick="startCamera()" style="background: #9b5de5; color: white; border: none; padding: 12px 20px; border-radius: 12px; font-size: 15px; font-weight: bold; cursor: pointer;">
                🔴 كاميرا وبث مباشر (مع الصوت)
            </button>
            <button onclick="flipCamera()" style="background: #f15bb5; color: white; border: none; padding: 12px 20px; border-radius: 12px; font-size: 15px; font-weight: bold; cursor: pointer;">
                🔄 قلب الكاميرا
            </button>
            <button onclick="startScreenShare()" style="background: #00b4d8; color: white; border: none; padding: 12px 20px; border-radius: 12px; font-size: 15px; font-weight: bold; cursor: pointer;">
                💻 مشاركة شاشة الآيباد
            </button>
            <button onclick="stopAll()" style="background: #38135e; color: white; border: none; padding: 12px 20px; border-radius: 12px; font-size: 15px; font-weight: bold; cursor: pointer;">
                ⏹️ إيقاف الكل
            </button>
        </div>
        <div style="position: relative; width: 100%; max-height: 550px; overflow: hidden; border-radius: 16px; background: #000; border: 2px solid #f15bb5;">
            <video id="liveVideo" autoplay playsinline style="width: 100%; max-height: 550px; object-fit: cover; transform: scaleX(-1);"></video>
        </div>
        <p id="mediaStatus" style="color: #e0d8f0; margin-top: 12px; font-family: sans-serif;">اختاري "كاميرا" أو "مشاركة شاشة الآيباد" للبدء</p>
    </div>

    <script>
        let currentStream = null;
        let useFrontCamera = false;

        async function startCamera() {
            stopAll();
            const constraints = {
                video: {
                    facingMode: useFrontCamera ? "user" : "environment",
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                },
                audio: true
            };
            try {
                currentStream = await navigator.mediaDevices.getUserMedia(constraints);
                const videoEl = document.getElementById('liveVideo');
                videoEl.srcObject = currentStream;
                document.getElementById('mediaStatus').innerText = useFrontCamera ? "🟢 الكاميرا الأمامية مفعلة بالصوت والصورة" : "🟢 الكاميرا الخلفية الواسعة مفعلة بالصوت والصورة";
            } catch (err) {
                document.getElementById('mediaStatus').innerText = "⚠️ يرجى السماح بالوصول للكاميرا والميكروفون: " + err.message;
            }
        }

        function flipCamera() {
            useFrontCamera = !useFrontCamera;
            startCamera();
        }

        async function startScreenShare() {
            stopAll();
            try {
                currentStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
                const videoEl = document.getElementById('liveVideo');
                videoEl.srcObject = currentStream;
                document.getElementById('mediaStatus').innerText = "💻 جاري مشاركة شاشة الآيباد بنجاح!";
                
                currentStream.getVideoTracks()[0].onended = function() {
                    stopAll();
                };
            } catch (err) {
                document.getElementById('mediaStatus').innerText = "⚠️ تم إلغاء مشاركة الشاشة أو لم يتم السماح بها: " + err.message;
            }
        }

        function stopAll() {
            if (currentStream) {
                currentStream.getTracks().forEach(track => track.stop());
                currentStream = null;
                const videoEl = document.getElementById('liveVideo');
                videoEl.srcObject = null;
                document.getElementById('mediaStatus').innerText = "⏹️ تم إيقاف العرض والكاميرا والشاشة";
            }
        }
    </script>
    """
    components.html(media_html, height=680)

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
            ("🏠 الشبكة الرئيسية (الأقسام)", "⚙️ إعدادات BRAS AI والحساب", "🧑‍💼 وضع السكرتير الذكي والبث ومشاركة الشاشة", "📚 أرشيف المحادثات المحفوظة")
        )

        if "🏠 الشبكة الرئيسية" in nav_mode:
            SECTIONS = {
                "المساعد الشامل": ("🤖", "You are BRAS AI, a versatile assistant created by Retaj Luqman ismail Gargary (ريتاج لقمان گەرگەری). When speaking Kurdish names or words containing the letter 'گ' (Ga), pronounce them with a clear 'G' sound and never substitute it with 'Q'."),
                "المعلم الشامل": ("📚", "You are BRAS AI, an expert school teacher assisting Retaj Luqman ismail Gargary (گەرگەری)."),
                "قسم كرة القدم": ("⚽", "You are BRAS AI, an expert football analyst covering FC Barcelona and matches for Retaj Luqman ismail Gargary (گەرگەری)."),
                "تعليم اللغات": ("🗣️", "You are BRAS AI, a multilingual tutor."),
                "البرمجة": ("💻", "You are BRAS AI, an expert programmer."),
                "الطبخ والوصفات": ("🍳", "You are BRAS AI, a master chef."),
                "مكياج وسكين كير": ("💄", "You are BRAS AI, an expert makeup artist and professional skincare consultant."),
                "ديزاين وملابس وشوبينغ": ("🛍️", "You are BRAS AI, a fashion designer, stylist, and shopping advisor."),
                "أفكار دول وسفرات": ("✈️", "You are BRAS AI, a travel planner and tour guide expert."),
                "قسم التاريخ": ("📜", "You are BRAS AI, a historian expert."),
                "الصحة، الدايت والجيم": ("💪", "You are BRAS AI, a fitness coach."),
                "نصائح وتطوير الذات": ("💡", "You are BRAS AI, a life advisor."),
                "قسم الرسم وتصميم الصور": ("🎨", "You are BRAS AI, an art assistant."),
                "صانع الفيديوهات والأفكار": ("🎬", "You are BRAS AI, a video and creative ideas creator.")
            }

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
                    if st.button("⬅️ العودة للشبكة الرئيسية"):
                        st.session_state.selected_section = None
                        st.session_state.current_archive_title = None
                        st.rerun()
                        
                if not is_archived_view:
                    col_new, col_arc = st.columns(2)
                    if col_new.button("✨ بدء محادثة جديدة في هذا القسم"):
                        st.session_state.section_messages[sec_name] = []
                        st.rerun()
                    if col_arc.button("💾 حفظ وأرشفة هذه المحادثة"):
                        if sec_name in st.session_state.section_messages and len(st.session_state.section_messages[sec_name]) > 0:
                            archive_title = f"{sec_name} - {st.session_state.section_messages[sec_name][0]['content'][:30]}..."
                            st.session_state.archives.append({
                                "title": archive_title,
                                "section": sec_name,
                                "messages": list(st.session_state.section_messages[sec_name])
                            })
                            st.success(f"تمت أرشفة المحادثة بنجاح تحت اسم: {archive_title}")
                else:
                    if st.button("↩️ الخروج من الأرشيف والعودة للدردشة الحالية"):
                        st.session_state.current_archive_title = None
                        st.rerun()

                with st.expander("➕ إضافة صورة أو فيديو أو ملف للتحليل", expanded=False):
                    attached_file = st.file_uploader(
                        "اختاري صورة، فيديو، أو ملف من جهازكِ:",
                        type=["png", "jpg", "jpeg", "webp", "mp4", "mov", "pdf", "txt"],
                        key=f"uploader_{sec_name}"
                    )

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
                    new_user_msg = {"role": "user", "content": prompt}
                    st.session_state.section_messages[sec_name].append(new_user_msg)
                    
                    with st.chat_message("user"):
                        st.markdown(prompt)
                        if attached_file is not None and attached_file.type.startswith("image"):
                            st.image(attached_file, width=300)
                        elif attached_file is not None and attached_file.type.startswith("video"):
                            st.video(attached_file)

                    with st.chat_message("assistant"):
                        try:
                            selected_voice_api = "onyx" if "رجل" in st.session_state.voice else "nova"
                            
                            if "الرسم" in sec_name or "تعديل الصور" in sec_name:
                                response = client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", quality="standard", n=1)
                                full_response = f"تم تجهيز طلبكِ بنجاح!:\n\n![Result]({response.data[0].url})"
                            else:
                                user_content = [{"type": "text", "text": prompt}]
                                if attached_file is not None:
                                    if attached_file.type.startswith("image"):
                                        base64_img = encode_image(attached_file)
                                        user_content.append({
                                            "type": "image_url",
                                            "image_url": {"url": f"data:{attached_file.type};base64,{base64_img}"}
                                        })
                                    else:
                                        user_content[0]["text"] += f"\n[المستخدم أرفق ملفاً باسم: {attached_file.name}]"

                                messages_payload = [{"role": "system", "content": f"{system_prompt} Respond in {st.session_state.language}."}] + [
                                    {"role": m["role"], "content": m["content"]} for m in st.session_state.section_messages[sec_name][:-1]
                                ] + [{"role": "user", "content": user_content}]

                                response = client.chat.completions.create(model="gpt-4o", messages=messages_payload)
                                full_response = response.choices[0].message.content
                                
                                audio_resp = client.audio.speech.create(model="tts-1", voice=selected_voice_api, input=full_response)
                                audio_resp.stream_to_file("response.mp3")
                                st.audio("response.mp3")
                                
                            st.markdown(full_response)
                            st.session_state.section_messages[sec_name].append({"role": "assistant", "content": full_response})
                        except Exception as e:
                            st.error(f"حدث خطأ: {e}")

        elif "⚙️ إعدادات BRAS AI والحساب" in nav_mode:
            st.markdown("<h2 style='text-align: center;'>🎛️ لوحة تحكم وإعدادات BRAS AI</h2>", unsafe_allow_html=True)
            with st.container():
                st.markdown("<div class='settings-panel'>", unsafe_allow_html=True)
                st.subheader("👤 بيانات الحساب والاشتراكات الاقتصادية")
                new_name = st.text_input("اسم المستخدم:", value=st.session_state.username)
                new_email = st.text_input("البريد الإلكتروني:", value=st.session_state.user_email)
                st.info("💳 **خطط الأسعار لتشغيل المنصة للمستخدمين:**\n* أسبوعياً: $5\n* شهرياً: $20\n* سنوياً: $99")
                st.subheader("🎨 مظهر التطبيق (Theme)")
                new_theme = st.radio("اختاري مظهر المنصة:", ("داكن (Dark)", "فاتح (Light)"), index=0 if "داكن" in st.session_state.theme else 1)
                st.subheader("🎙️ إعدادات الصوت (Voice)")
                new_voice = st.radio("اختاري صوت المساعد:", ("صوت بنت (Nova)", "صوت رجل (Onyx)"), index=0 if "بنت" in st.session_state.voice else 1)
                
                languages_list = [
                    "العربية (Arabic)", "الكردية البادينية / Badini Kurdish", "English (الإنجليزية)", "Turkish (التركية)",
                    "French (الفرنسية)", "Spanish (الإسبانية)", "German (الألمانية)", "Italian (الإيطالية)"
                ]
                current_lang_index = 0
                for idx, lang in enumerate(languages_list):
                    if st.session_state.language in lang:
                        current_lang_index = idx
                        break
                new_lang = st.selectbox("اختر لغة التفاعل:", languages_list, index=current_lang_index)
                
                if st.button("💾 حفظ كافة التعديلات وتطبيقها"):
                    st.session_state.username = new_name
                    st.session_state.user_email = new_email
                    st.session_state.theme = new_theme
                    st.session_state.voice = new_voice
                    st.session_state.language = new_lang
                    st.success("تم تحديث الإعدادات بنجاح!")
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        elif "🧑‍💼 وضع السكرتير الذكي والبث ومشاركة الشاشة" in nav_mode:
            st.markdown("<h2 style='text-align: center; color: #9b5de5;'>🧑‍💼 السكرتير الذكي، البث المباشر ومشاركة الشاشة</h2>", unsafe_allow_html=True)
            st.markdown("<div class='secretary-circle'><span>✨ SECRETARY ✨<br>LIVE & SCREEN SHARE</span></div>", unsafe_allow_html=True)
            
            st.subheader("🔴 مركز البث المباشر، الكاميرا ومشاركة شاشة الآيباد")
            st.write("📡 **ملاحظة:** يمكنكِ تشغيل الكاميرا بالصوت والصورة، أو الضغط على **'مشاركة شاشة الآيباد'** لعرض شاشتكِ مباشرة في المنصة!")
            
            render_media_hub()

            st.markdown("---")
            st.subheader("📅 جدول الامتحانات والتنبيه الصوتي التلقائي")
            with st.form("add_task_form"):
                new_task = st.text_input("أدخلي امتحان أو مهمة جديدة:")
                add_btn = st.form_submit_button("إضافة وتفعيل التنبيه الصوتي")
                if add_btn and new_task:
                    st.session_state.my_schedule.append(new_task)
                    st.success("تمت إضافة المهمة للجدول!")

            if st.session_state.my_schedule:
                st.markdown("📌 **جدولكِ النشط حالياً:**")
                for idx, task in enumerate(st.session_state.my_schedule, 1):
                    st.write(f"{idx}. 🗓️ {task}")
            
            st.markdown("---")
            st.subheader("💬 تحدثي مع سكرتيركِ الشخصي:")
            with st.expander("➕ إضافة صورة أو ملف للسكرتير", expanded=False):
                sec_file = st.file_uploader("ارفعي صورة جدولكِ المدرسي أو أي ملف:", type=["png", "jpg", "jpeg", "webp", "mp4", "pdf"], key="uploader_secretary")

            sec_prompt = st.chat_input("اطلبي منه تذكيركِ، ترتيب جدولكِ، أو تحليل صورة...")
            if sec_prompt:
                st.session_state.messages.append({"role": "user", "content": sec_prompt})
                with st.chat_message("user"):
                    st.markdown(sec_prompt)
                    if sec_file is not None and sec_file.type.startswith("image"):
                        st.image(sec_file, width=300)
                    elif sec_file is not None and sec_file.type.startswith("video"):
                        st.video(sec_file)
                    
                with st.chat_message("assistant"):
                    try:
                        selected_voice_api = "onyx" if "رجل" in st.session_state.voice else "nova"
                        system_instructions = f"You are Retaj's smart personal secretary assistant created by Retaj Luqman ismail Gargary (گەرگەری). Current tasks/schedule: {st.session_state.my_schedule}. Alert her about her exams and schedule dynamically and kindly in {st.session_state.language}."
                        
                        user_sec_content = [{"type": "text", "text": sec_prompt}]
                        if sec_file is not None and sec_file.type.startswith("image"):
                            base64_sec_img = encode_image(sec_file)
                            user_sec_content.append({"type": "image_url", "image_url": {"url": f"data:{sec_file.type};base64,{base64_sec_img}"}})

                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "system", "content": system_instructions}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]] + [{"role": "user", "content": user_sec_content}]
                        )
                        full_resp = response.choices[0].message.content
                        audio_resp = client.audio.speech.create(model="tts-1", voice=selected_voice_api, input=full_resp)
                        audio_resp.stream_to_file("secretary_live.mp3")
                        st.audio("secretary_live.mp3")
                        st.markdown(full_resp)
                        st.session_state.messages.append({"role": "assistant", "content": full_resp})
                    except Exception as e:
                        st.error(f"حدث خطأ: {e}")

        elif "📚 أرشيف المحادثات المحفوظة" in nav_mode:
            st.markdown("<h2 style='text-align: center; color: #9b5de5;'>📚 أرشيف المحادثات المحفوظة</h2>", unsafe_allow_html=True)
            if not st.session_state.archives:
                st.info("لا توجد محادثات مؤرشفة حالياً. يمكنكِ الضغط على 'حفظ وأرشفة هذه المحادثة' داخل أي قسم!")
            else:
                for idx, arch in enumerate(st.session_state.archives):
                    with st.expander(f"📁 {arch['title']} (القسم: {arch['section']})"):
                        st.write(f"عدد الرسائل المؤرشفة: {len(arch['messages'])}")
                        if st.button("📖 استعراض هذه المحادثة", key=f"arch_btn_{idx}"):
                            st.session_state.selected_section = arch["section"]
                            st.session_state.current_archive_title = arch["title"]
                            st.rerun()
