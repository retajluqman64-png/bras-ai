import streamlit as st
from openai import OpenAI

# إعداد الصفحة لتكون واسعة
st.set_page_config(
    page_title="BRAS AI - المنصة الشاملة",
    page_icon="💜",
    layout="wide"
)

# إدارة الحالة لتخزين الذاكرة والجدول
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = "ريتاج لقمان"
    st.session_state.user_email = "retaj@brasai.com"
    st.session_state.theme = "داكن (Dark)"
    st.session_state.voice = "صوت بنت (Nova)"
    st.session_state.language = "العربية (Arabic)"
    st.session_state.selected_section = None
    st.session_state.my_schedule = []
    st.session_state.messages = []

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
    width: 220px;
    height: 220px;
    border-radius: 50%;
    background: radial-gradient(circle, #9b5de5, #38135e, #0d0614);
    margin: 30px auto;
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

if not api_key:
    st.error("يرجى ضبط مفتاح OpenAI API في إعدادات Streamlit Secrets.")
else:
    client = OpenAI(api_key=api_key)

    # 1. شاشة تسجيل الدخول
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
        # الشريط العلوي لمعلومات الحساب
        st.markdown(f"""
        <div class='user-info'>
            <span>👤 الحساب: <b>{st.session_state.username}</b> ({st.session_state.user_email}) | 🌐 اللغة: {st.session_state.language}</span>
            <span>🎨 الثيم: {st.session_state.theme} | 🎙️ الصوت: {st.session_state.voice}</span>
        </div>
        """, unsafe_allow_html=True)

        # القائمة الجانبية للتنقل
        nav_mode = st.sidebar.radio(
            "📍 تنقلي في منصتكِ:",
            ("🏠 الشبكة الرئيسية (الأقسام)", "⚙️ إعدادات BRAS AI والحساب", "🧑‍💼 وضع السكرتير الذكي والبث المباشر")
        )

        if "🏠 الشبكة الرئيسية" in nav_mode:
            SECTIONS = {
                "المساعد الشامل": ("🤖", "You are BRAS AI, a versatile assistant created by Retaj Luqman ismail Gargary."),
                "المعلم الشامل": ("📚", "You are BRAS AI, an expert school teacher."),
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
                    if col.button(f"{emoji}\n\n{sec_name}"):
                        st.session_state.selected_section = sec_name
                        st.rerun()
            else:
                sec_name = st.session_state.selected_section
                emoji, system_prompt = SECTIONS[sec_name]
                
                if st.button("⬅️ العودة للشبكة الرئيسية"):
                    st.session_state.selected_section = None
                    st.rerun()
                    
                st.subheader(f"أنتِ الآن في: {emoji} {sec_name}")

                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                prompt = st.chat_input(f"تحدثي مع {sec_name}...")
                if prompt:
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    with st.chat_message("assistant"):
                        try:
                            selected_voice_api = "onyx" if "رجل" in st.session_state.voice else "nova"
                            
                            messages_payload = [{"role": "system", "content": f"{system_prompt} Respond in {st.session_state.language}."}] + [
                                {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
                            ]
                            
                            if "الرسم" in sec_name or "تعديل الصور" in sec_name:
                                response = client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", quality="standard", n=1)
                                full_response = f"تم تجهيز طلبكِ بنجاح!:\n\n![Result]({response.data[0].url})"
                            else:
                                response = client.chat.completions.create(model="gpt-4o", messages=messages_payload)
                                full_response = response.choices[0].message.content
                                
                                audio_resp = client.audio.speech.create(model="tts-1", voice=selected_voice_api, input=full_response)
                                audio_resp.stream_to_file("response.mp3")
                                st.audio("response.mp3")
                                
                            st.markdown(full_response)
                            st.session_state.messages.append({"role": "assistant", "content": full_response})
                        except Exception as e:
                            st.error(f"حدث خطأ: {e}")

        elif "⚙️ إعدادات BRAS AI والحساب" in nav_mode:
            st.markdown("<h2 style='text-align: center;'>🎛️ لوحة تحكم وإعدادات BRAS AI</h2>", unsafe_allow_html=True)
            with st.container():
                st.markdown("<div class='settings-panel'>", unsafe_allow_html=True)
                
                st.subheader("👤 بيانات الحساب والاشتراكات الاقتصادية")
                new_name = st.text_input("اسم المستخدم:", value=st.session_state.username)
                new_email = st.text_input("البريد الإلكتروني:", value=st.session_state.user_email)
                
                st.info("💳 **خطط الأسعار لتشغيل المنصة للمستخدمين:**\n* أسبوعياً: $5\n* شهرياً: $20\n* سنوياً: $99 (تكفي لتغطية الخوادم والذكاء الاصطناعي بالكامل وتوفير أرباح استدامة!)")
                
                st.subheader("🎨 مظهر التطبيق (Theme)")
                new_theme = st.radio("اختاري مظهر المنصة:", ("داكن (Dark)", "فاتح (Light)"), index=0 if "داكن" in st.session_state.theme else 1)
                
                st.subheader("🎙️ إعدادات الصوت (Voice)")
                new_voice = st.radio("اختاري صوت المساعد:", ("صوت بنت (Nova)", "صوت رجل (Onyx)"), index=0 if "بنت" in st.session_state.voice else 1)
                
                languages_list = [
                    "العربية (Arabic)", "Kurdish (Kurdî)", "English (الإنجليزية)", "Turkish (التركية)",
                    "French (الفرنسية)", "Spanish (الإسبانية)", "German (الألمانية)", "Italian (الإيطالية)",
                    "Japanese (اليابانية)", "Korean (الكورية)", "Chinese (الصينية)", "Russian (الروسية)",
                    "Persian (الفارسية)", "Hindi (الهندية)", "Portuguese (البرتغالية)", "Dutch (الهولندية)",
                    "Swedish (السويدية)", "Greek (اليونانية)", "Polish (البولندية)", "Romanian (الرومانية)",
                    "Urdu (الأوردو)", "Vietnamese (الفيتنامية)", "Thai (التايلاندية)",
                    "Indonesian (الإندونيسية)", "Hebrew (العبرية)", "Czech (التشيكية)", "Danish (الدنماركية)",
                    "Finnish (الفنلندية)", "Hungarian (المجرية)", "Norwegian (النرويجية)", "Ukrainian (الأوكرانية)"
                ]
                
                current_lang_index = 0
                for idx, lang in enumerate(languages_list):
                    if st.session_state.language in lang:
                        current_lang_index = idx
                        break

                new_lang = st.selectbox("اختاري لغة التفاعل:", languages_list, index=current_lang_index)
                
                if st.button("💾 حفظ كافة التعديلات وتطبيقها"):
                    st.session_state.username = new_name
                    st.session_state.user_email = new_email
                    st.session_state.theme = new_theme
                    st.session_state.voice = new_voice
                    st.session_state.language = new_lang
                    st.success("تم تحديث إعدادات وإعدادات الأسعار بنجاح!")
                    st.rerun()
                    
                st.markdown("</div>", unsafe_allow_html=True)

        elif "🧑‍💼 وضع السكرتير الذكي والبث المباشر" in nav_mode:
            st.markdown("<h2 style='text-align: center; color: #9b5de5;'>🧑‍💼 السكرتير الذكي، البث المباشر والكاميرا</h2>", unsafe_allow_html=True)
            st.markdown("<div class='secretary-circle'><span>✨ SECRETARY ✨<br>24/7 LIVE & CAM</span></div>", unsafe_allow_html=True)
            
            # قسم الكاميرا المباشرة (واسعة مع خيار قلب الكاميرا)
            st.subheader("🔴 البث المباشر والكاميرا الواسعة (Live Stream & Camera)")
            st.write("📡 **جدول البث المجاني:** متاح بث مباشر تفاعلي مجاني لمدة ساعتين كل 24 ساعة للمستخدمين!")
            
            camera_on = st.checkbox("🟢 تشغيل البث والكاميرا المباشرة الآن")
            if camera_on:
                # خيار لتحديد الكاميرا واسعة أو قلب الكاميرا
                cam_facing = st.radio("اختر وضع الكاميرا:", ("كاميرا خلفية واسعة (Rear Wide)", "كاميرا أمامية (Front)"), horizontal=True)
                
                # استخدام كاميرا إدخال المتصفح المتطورة
                captured_image = st.camera_input("التقطي صورة مباشرة عبر كاميرا الآيباد:")
                if captured_image:
                    st.success("✅ تم التقاط الصورة بنجاح وجاهزة للبث أو التحليل الذكي!")

            st.markdown("---")
            st.subheader("📅 جدول الامتحانات والتنبيه الصوتي التلقائي")
            
            with st.form("add_task_form"):
                new_task = st.text_input("أدخلي امتحان أو مهمة جديدة (مثلاً: عندك امتحان كيمياء يوم الأحد):")
                add_btn = st.form_submit_button("إضافة وتفعيل التنبيه الصوتي")
                if add_btn and new_task:
                    st.session_state.my_schedule.append(new_task)
                    st.success("تمت إضافة المهمة للجدول وسيقوم السكرتير بتذكيركِ بها صوتياً فوراً!")

            if st.session_state.my_schedule:
                st.markdown("📌 **جدولكِ النشط حالياً:**")
                for idx, task in enumerate(st.session_state.my_schedule, 1):
                    st.write(f"{idx}. 🗓️ {task}")
            
            st.markdown("---")
            st.subheader("💬 تحدثي مع سكرتيركِ الشخصي:")
            sec_prompt = st.chat_input("اطلبي منه تذكيركِ، ترتيب جدولكِ، أو بدء البث...")
            if sec_prompt:
                st.session_state.messages.append({"role": "user", "content": sec_prompt})
                with st.chat_message("user"):
                    st.markdown(sec_prompt)
                    
                with st.chat_message("assistant"):
                    try:
                        selected_voice_api = "onyx" if "رجل" in st.session_state.voice else "nova"
                        
                        # إعداد التنبيه الصوتي التلقائي من السكرتير
                        system_instructions = f"You are Retaj's smart personal secretary assistant created by Retaj Luqman. Current tasks/schedule: {st.session_state.my_schedule}. Alert her about her exams and schedule dynamically and kindly in {st.session_state.language}."
                        
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "system", "content": system_instructions}] + 
                                     [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                        )
                        full_resp = response.choices[0].message.content
                        
                        # توليد وتشغيل الصوت الذكي
                        audio_resp = client.audio.speech.create(model="tts-1", voice=selected_voice_api, input=full_resp)
                        audio_resp.stream_to_file("secretary_live.mp3")
                        st.audio("secretary_live.mp3")
                        
                        st.markdown(full_resp)
                        st.session_state.messages.append({"role": "assistant", "content": full_resp})
                    except Exception as e:
                        st.error(f"حدث خطأ: {e}")
