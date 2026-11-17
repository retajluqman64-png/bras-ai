import streamlit as st
from datetime import datetime

# إعداد الصفحة وتفعيل الاتجاه من اليمين لليسار
st.set_page_config(page_title="BRAS AI | براس", page_icon="🎓", layout="wide")

# تهيئة الذاكرة والتخزين المؤقت
if "activated" not in st.session_state:
    st.session_state.activated = False
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "فاتح (أبيض وأزرق)"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "مرحباً يا رتوجه! أنا براس (BRAS AI)، رفيقك الذكي. جاهز لمساعدتك في كل مواد إقليم كوردستان اليوم! 🌟"}
    ]
if "saved_lessons" not in st.session_state:
    st.session_state.saved_lessons = []
if "my_grades" not in st.session_state:
    st.session_state.my_grades = []
if "student_data" not in st.session_state:
    st.session_state.student_data = {"name": "", "grade": "الصف السابع الأساسي", "school": "", "lang": "کوردی بادینی"}

# نظام الألوان (فاتح / غامق - مخصص ومريح للعين)
if st.session_state.theme_mode == "فاتح (أبيض وأزرق)":
    bg_main = "#FFFFFF"
    text_main = "#000000"
    sidebar_bg = "#E3F2FD"
    card_bg = "#F5F9FF"
    border_c = "#90CAF9"
    btn_bg = "#1E88E5"
    btn_txt = "#FFFFFF"
else:
    bg_main = "#0A0E17"
    text_main = "#F0F8FF"
    sidebar_bg = "#0D1B2A"
    card_bg = "#112240"
    border_c = "#1E3A8A"
    btn_bg = "#2563EB"
    btn_txt = "#FFFFFF"

st.markdown(f"""
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: {bg_main} !important;
        color: {text_main} !important;
        direction: rtl;
        text-align: right;
    }}
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        direction: rtl;
        text-align: right;
    }}
    h1, h2, h3, h4, p, span, label, li, .stMarkdown {{
        color: {text_main} !important;
    }}
    .stButton > button {{
        background-color: {btn_bg} !important;
        color: {btn_txt} !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        width: 100%;
        border: 1px solid {border_c} !important;
    }}
    .box-card {{
        background-color: {card_bg};
        border: 2px solid {border_c};
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
    }}
</style>
""", unsafe_allow_html=True)

# زر تغيير المظهر (Dark / Light Mode) في الأعلى
col_m1, col_m2 = st.columns([5, 1])
with col_m2:
    new_theme = st.selectbox("🎨 المظهر:", ["فاتح (أبيض وأزرق)", "غامق (Dark Mode)"], key="theme_selector")
    if new_theme != st.session_state.theme_mode:
        st.session_state.theme_mode = new_theme
        st.rerun()

# ========================================================
# شاشة البداية والاشتراك ببطاقة كي كارد
# ========================================================
if not st.session_state.activated:
    st.title("🎓 تطبيق براس الذكي (BRAS AI)")
    st.subheader("المنصة التعليمية الشاملة لطلاب إقليم كوردستان - مناهج 2026")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="box-card">
            <h3>📜 شروط الاستخدام والأسعار</h3>
            <ul>
                <li>الحساب مخصص لطالب واحد فقط.</li>
                <li>يشمل جميع الصفوف ومناهج 2026 المحدثة.</li>
                <li><b>سعر الكورس الواحد:</b> 15 دولار.</li>
                <li><b>سعر الكورسين (سنة كاملة):</b> 30 دولار.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="box-card">
            <h3>💳 طريقة الدفع (بطاقة كي كارد Qi Card فقط)</h3>
            <p>1. قم بتحويل المبلغ إلى رقم بطاقة الكي كارد:</p>
            <h4><code>4921 - XXXX - XXXX - XXXX</code></h4>
            <p>2. أرسل صورة وصل التحويل للإدارة لاستلام كود الدخول.</p>
        </div>
        """, unsafe_allow_html=True)
        
        activation_code = st.text_input("🔑 أدخل كود التفعيل هنا:", type="password", placeholder="اكتب رقم 2026 للتجربة")
        if st.button("دخول إلى التطبيق 🚀"):
            if activation_code == "2026":
                st.session_state.activated = True
                st.rerun()
            else:
                st.error("⚠️ كود غير صحيح. (اكتب 2026 للتجربة)")
    st.stop()

# ========================================================
# القائمة الجانبية للتطبيق
# ========================================================
with st.sidebar:
    st.title("🎓 BRAS AI")
    st.session_state.student_data["lang"] = st.selectbox("🌐 لغة الشرح:", ["کوردی بادینی", "کوردی سۆرانی", "العربية"])
    st.divider()
    
    menu_choice = st.radio("📌 الأقسام الرئيسية:", [
        "💬 المساعد الذكي (براس)",
        "📚 مكتبة الكتب و PDF (2026)",
        "🎯 كويزات جميع المواد والنتائج",
        "🎥 يوتيوب، قوتابخانەکەم وهەڵسەنگاندن",
        "🗂️ الدردشات المحفوظة",
        "👤 معلومات الطالب والحساب"
    ])

# ========================================================
# 1. المساعد الذكي (براس)
# ========================================================
if menu_choice == "💬 المساعد الذكي (براس)":
    c_t, c_b = st.columns([3, 1])
    with c_t:
        st.header(f"💬 اسأل براس ({st.session_state.student_data['lang']})")
    with c_b:
        if st.button("➕ دردشة جديدة"):
            if st.session_state.chat_history:
                st.session_state.saved_lessons.append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "chats": list(st.session_state.chat_history)
                })
                st.session_state.chat_history = []
                st.success("تم حفظ الدردشة السابقة!")
                st.rerun()

    with st.expander("🎙️ أدوات الصوت، رفع الصور، مشاركة الشاشة"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.audio_input("🎤 تسجيل سؤال صوتي")
        with col_b:
            st.file_uploader("📷 رفع صورة سؤال أو صفحة كتاب", type=["png", "jpg", "jpeg"])
        with col_c:
            st.checkbox("🔊 تفعيل الرد الصوتي", value=True)
            st.button("📤 مشاركة الإجابة")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_q = st.chat_input("اكتب سؤالك أو رحب بـ براس...")
    if user_q:
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        q_lower = user_q.lower()
        if "مرحبا" in q_lower or "هلا" in q_lower or "سلام" in q_lower or "بژین" in q_lower:
            ai_reply = f"أهلاً بكِ يا رتوجه! 🌸 أنا معكِ دائماً لمساعدتكِ في كل مواد كوردستان. اسأليني عن أي درس وسأشرحه لكِ فوراً!"
        else:
            ai_reply = f"**شرح براس المفصل ({st.session_state.student_data['lang']}):**\nلقد بحثتُ لكِ عن موضوع (*{user_q}*) وفق منهج 2026:\n\n1. **الشرح المبسط:** هذا الدرس يعتمد على الفهم السريع والتطبيقات العملية.\n2. **ملخص مهم:** ركزي على هذه النقطة لأنها مهمة للامتحانات.\n\n🎥 **فيديوهات يوتيوب مقترحة:**\n- [شرح درس {user_q} على يوتيوب (اضغط هنا)](https://www.youtube.com)"
            
        st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
        st.rerun()

# ========================================================
# 2. مكتبة الكتب و PDF (2026) - مرتبة وبيرفكت
# ========================================================
elif menu_choice == "📚 مكتبة الكتب و PDF (2026)":
    st.header("📚 مكتبة كتب إقليم كوردستان الرسمية (طبعة 2026)")
    st.write("اختر الكتاب المطلوب لتصفحه أو تحميله بصيغة PDF مباشرة:")
    
    selected_grade = st.selectbox("اختر الصف الدراسي:", ["الصف السابع الأساسي", "الصف الثامن", "الصف التاسع (وزاري)", "الصف العاشر", "الصف الحادي عشر", "الصف الثاني عشر"])
    
    col_b1, col_b2, col_b3 = st.columns(3)
    
    with col_b1:
        st.markdown("""
        <div class="box-card" style="text-align: center;">
            <h3>💻 Computer</h3>
            <p><b>المنهج الجديد (English)</b></p>
            <p>طبعة 2026 الرسمية</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("📖 تصفح وقراءة كتاب الحاسوب PDF", "https://gov.krd")
        
    with col_b2:
        st.markdown("""
        <div class="box-card" style="text-align: center;">
            <h3>📐 الرياضيات</h3>
            <p><b>Mathematics</b></p>
            <p>المناهج المحدثة 2026</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("📖 تصفح وقراءة كتاب الرياضيات PDF", "https://gov.krd")
        
    with col_b3:
        st.markdown("""
        <div class="box-card" style="text-align: center;">
            <h3>🧪 العلوم العامة</h3>
            <p><b>Science & Chemistry</b></p>
            <p>طبعة 2026</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("📖 تصفح وقراءة كتاب العلوم PDF", "https://gov.krd")

# ========================================================
# 3. كويزات جميع المواد والنتائج
# ========================================================
elif menu_choice == "🎯 كويزات جميع المواد والنتائج":
    st.header("🎯 قسم الكويزات الشامل لجميع المواد")
    
    quiz_subject = st.selectbox("اختر المادة للاختبار:", ["Computer 2026", "الرياضيات", "العلوم", "اللغة الإنجليزية", "اللغة الكوردية"])
    
    if quiz_subject == "Computer 2026":
        q_ans = st.radio("سؤال 1: ما هي لغة برمجة وتدريس منهج الحاسوب الجديد في كوردستان 2026؟", ["اللغة الإنجليزية (English)", "اللغة العربية فقط"])
        if st.button("إنهاء واحتساب النتيجة 📊"):
            score = 100 if q_ans == "اللغة الإنجليزية (English)" else 0
            st.session_state.my_grades.append({"التاريخ": datetime.now().strftime("%Y-%m-%d"), "المادة": quiz_subject, "الدرجة": f"{score}/100", "النسبة": f"{score}%"})
            st.success(f"ممتاز! درجتك في {quiz_subject} هي: {score} من 100 (النسبة: {score}%)")
    else:
        q_ans2 = st.radio("سؤال تجريبي في المادة المختارة:", ["الإجابة الصحيحة الأولى", "الإجابة الثانية الخاطئة"])
        if st.button("إنهاء واحتساب النتيجة 📊"):
            score = 100 if q_ans2 == "الإجابة الصحيحة الأولى" else 0
            st.session_state.my_grades.append({"التاريخ": datetime.now().strftime("%Y-%m-%d"), "المادة": quiz_subject, "الدرجة": f"{score}/100", "النسبة": f"{score}%"})
            st.success(f"درجتك في {quiz_subject} هي: {score} من 100")

    st.divider()
    st.subheader("🏆 سجل درجاتك ونتائجك المحفوظة:")
    if st.session_state.my_grades:
        st.table(st.session_state.my_grades)
    else:
        st.info("لم تقم بأي اختبار بعد. ابدأ الحل وسجل درجتك هنا!")

# ========================================================
# 4. يوتيوب، قوتابخانەکەم وهەڵسەنگاندن
# ========================================================
elif menu_choice == "🎥 يوتيوب، قوتابخانەکەم وهەڵسەنگاندن":
    st.header("🎥 الروابط الرسمية وبوابة الطالب")
    
    c_l, c_r = st.columns(2)
    with c_l:
        st.markdown("""
        <div class="box-card">
            <h3>📊 الدخول إلى قوتابخانەکەم (Qutabxanakam) و هەڵسەنگاندن</h3>
            <p>اضغط للانتقال السريع لبوابات الوزارة لمتابعة الدرجات والتقييمات:</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("🔗 فتح موقع / تطبيق قوتابخانەکەم", "https://www.youtube.com")
        st.link_button("🔗 فتح بوابة هەڵسەنگاندن الرسمية", "https://www.youtube.com")
        
    with c_r:
        st.markdown("""
        <div class="box-card">
            <h3>🎥 مكتبة فيديوهات يوتيوب التعليمية</h3>
            <p>شروحات إضافية لجميع مواد إقليم كوردستان عبر القنوات التعليمية المعتمدة.</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("📺 الانتقال إلى يوتيوب التعليمي", "https://youtube.com")

# ========================================================
# 5. الدردشات المحفوظة
# ========================================================
elif menu_choice == "🗂️ الدردشات المحفوظة":
    st.header("🗂️ سجل الدردشات والدروس السابقة")
    if not st.session_state.saved_lessons:
        st.write("لا توجد دروس محفوظة حالياً. عند الضغط على زر (دردشة جديدة) سيتم حفظ المحادثة السابقة هنا تلقائياً.")
    else:
        for item in st.session_state.saved_lessons:
            with st.expander(f"📁 درس بتاريخ: {item['time']}"):
                for m in item["chats"]:
                    st.write(f"**{m['role']}:** {m['content']}")

# ========================================================
# 6. معلومات الطالب والحساب
# ========================================================
elif menu_choice == "👤 معلومات الطالب والحساب":
    st.header("👤 الملف الشخصي للطالب والحساب")
    col_s, col_acc = st.columns(2)
    with col_s:
        st.subheader("🎒 معلومات الطالب (منفصلة عن الحساب)")
        st.session_state.student_data["name"] = st.text_input("اسم الطالب:", st.session_state.student_data["name"])
        st.session_state.student_data["grade"] = st.selectbox("الصف الدراسي:", ["الصف السابع الأساسي", "الصف الثامن", "الصف التاسع", "الصف العاشر", "الصف الحادي عشر", "الصف الثاني عشر"])
        st.session_state.student_data["school"] = st.text_input("اسم المدرسة / المحافظة:", st.session_state.student_data["school"])
        if st.button("حفظ بيانات الطالب 💾"):
            st.success("تم حفظ بيانات الطالب بنجاح!")
    with col_acc:
        st.subheader("💳 تفاصيل اشتراك كي كارد")
        st.write("**حالة الحساب:** مفعل ونشط ✅")
        st.write("**الباقة:** كورس واحد (15$) أو كورسين (30$)")
        st.write("**طريقة الدفع:** تحويل مباشر عبر Qi Card")
