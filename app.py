import streamlit as st
from datetime import datetime

# 1. إعداد الصفحة واتجاهها من اليمين لليسار
st.set_page_config(page_title="BRAS AI | براس", page_icon="🎓", layout="wide")

# 2. الذاكرة المؤقتة للتطبيق
if "activated" not in st.session_state:
    st.session_state.activated = False
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "فاتح (أبيض وأزرق)"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "saved_lessons" not in st.session_state:
    st.session_state.saved_lessons = []
if "my_grades" not in st.session_state:
    st.session_state.my_grades = []
if "student_data" not in st.session_state:
    st.session_state.student_data = {"name": "", "grade": "الصف السابع الأساسي", "school": "", "lang": "کوردی بادینی"}

# 3. الألوان والتحكم الشامل بالمظهر (فاتح / غامق)
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

# زر تغيير المظهر السريع في الأعلى
col_m1, col_m2 = st.columns([5, 1])
with col_m2:
    new_theme = st.selectbox("🎨 المظهر:", ["فاتح (أبيض وأزرق)", "غامق (أسود وأزرق)"], key="theme_selector")
    if new_theme != st.session_state.theme_mode:
        st.session_state.theme_mode = new_theme
        st.rerun()

# ========================================================
# 4. شاشة البداية (الشروط + الأسعار + الدفع كي كارد)
# ========================================================
if not st.session_state.activated:
    st.title("🎓 تطبيق براس الذكي (BRAS AI)")
    st.subheader("المنصة التعليمية لطلاب إقليم كوردستان - مناهج 2026")
    
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
# 5. القائمة الجانبية داخل التطبيق
# ========================================================
with st.sidebar:
    st.title("🎓 BRAS AI")
    st.session_state.student_data["lang"] = st.selectbox("🌐 لغة الشرح:", ["کوردی بادینی", "کوردی سۆرانی", "العربية"])
    st.divider()
    
    menu_choice = st.radio("📌 الأقسام الرئيسية:", [
        "💬 المساعد الذكي (براس)",
        "📚 كتب 2026 والحاسوب الجديد",
        "📝 بنك الأسئلة والوزاري",
        "🎯 الكويزات وسجل الدرجات",
        "🎥 يوتيوب وهەڵسەنگاندن والعطل",
        "🗂️ الدردشات المحفوظة",
        "👤 معلومات الطالب والحساب"
    ])

# ========================================================
# 6. محتوى الأقسام داخل التطبيق
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

    # أدوات تفاعلية (صوت، شاشة، زر مشاركة)
    with st.expander("🎙️ أدوات الصوت ومشاركة الشاشة والكتابة"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.audio_input("🎤 تسجيل سؤال صوتي")
        with col_b:
            st.file_uploader("🖥️ مشاركة لقطة شاشة أو صورة", type=["png", "jpg"])
        with col_b:
            st.checkbox("🔊 تفعيل الجواب الصوتي", value=True)
            st.button("📤 مشاركة الإجابة")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_q = st.chat_input("اكتب سؤالك هنا أو اطلب شرح درس...")
    if user_q:
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        ai_reply = f"**شرح براس:**\nأهلاً بك يا {st.session_state.student_data['name'] or 'طالبنا العزيز'}! إليك شرح مفصل لسؤالك: *{user_q}* حسب منهج 2026.\n\n🎥 **فيديو مقترح:** [اضغط هنا لمشاهدة الشرح على يوتيوب](https://youtube.com)"
        st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
        st.rerun()

elif menu_choice == "📚 كتب 2026 والحاسوب الجديد":
    st.header("📚 مكتبة المناهج الدراسية - طبعة 2026")
    g_sel = st.selectbox("اختر الصف:", ["السابع الأساسي", "الثامن", "التاسع (وزاري)", "العاشر", "الحادي عشر", "الثاني عشر (وزاري)"])
    sub_sel = st.selectbox("اختر المادة:", ["💻 الحاسوب الجديد (Computer - English)", "الرياضيات", "العلوم", "اللغة الإنجليزية", "اللغة الكوردية", "اللغة العربية", "الاجتماعيات"])
    
    st.markdown(f"""
    <div class="box-card">
        <b>📖 كتاب: {sub_sel} - {g_sel} (إصدار 2026)</b><br>
        المحتوى جاهز للنسخ، التلخيص، أو الترجمة الفورية عبر براس.
    </div>
    """, unsafe_allow_html=True)
    st.text_area("النص الرسمي للكتاب (قابل للنسخ):", "Unit 1: Introduction to 2026 Curriculum...\nهنا تظهر نصوص ومواضيع الكتاب الدراسي كاملة.", height=180)

elif menu_choice == "📝 بنك الأسئلة والوزاري":
    st.header("📝 بنك الأسئلة والامتحانات")
    tab1, tab2 = st.tabs(["🤖 أسئلة يصنعها براس", "🏫 أسئلة المدارس والوزاري"])
    with tab1:
        topic_name = st.text_input("اكتب الفصل أو المادة لصنع أسئلة متوقعة:")
        if st.button("توليد الأسئلة الآن ✨"):
            st.write(f"**أسئلة مقترحة لموضوع ({topic_name}):**\n1. س1: عرف المفاهيم الأساسية...\n2. س2: قارن بين...")
    with tab2:
        st.selectbox("اختر السنة الدراسية:", ["2025-2026", "2024-2025", "2023-2024"])
        st.text_area("نموذج أسئلة وزارية / مدرسية سابقة:", "س1: أجب عن الفرع أ وب...\nس2: ما هي الوظائف الأساسية...", height=150)

elif menu_choice == "🎯 الكويزات وسجل الدرجات":
    st.header("🎯 الاختبارات السريعة وحساب النسبة")
    q_ans = st.radio("سؤال تجريبي: بأي لغة يُدرّس منهج الحاسوب الجديد في كوردستان 2026؟", ["اللغة الإنجليزية", "اللغة العربية"])
    if st.button("إنهاء واحتساب الدرجة 📊"):
        got_score = 100 if q_ans == "اللغة الإنجليزية" else 0
        st.session_state.my_grades.append({"التاريخ": datetime.now().strftime("%Y-%m-%d"), "المادة": "Computer 2026", "الدرجة": f"{got_score}/100", "النسبة": f"{got_score}%"})
        st.success(f"درجتك هي: {got_score} من 100")
        
    st.subheader("🏆 سجل درجاتك المحفوظة:")
    if st.session_state.my_grades:
        st.table(st.session_state.my_grades)
    else:
        st.write("لم تقم بأي كويز بعد.")

elif menu_choice == "🎥 يوتيوب وهەڵسەنگاندن والعطل":
    st.header("🎥 روابط اليوتيوب وبوابة الطالب الرسمية")
    c_l, c_r = st.columns(2)
    with c_l:
        st.markdown("""
        <div class="box-card">
            <h3>📊 كيف تفتح درجاتك في هەڵسەنگاندن وقوتابخانەکەم؟</h3>
            <p>1. افتح تطبيق <b>قوتابخانەکەم (Qutabxanakam)</b> أو موقع هەڵسەنگاندن.</p>
            <p>2. أدخل كود الطالب والرمز السري.</p>
            <p>3. ستظهر درجاتك ونسبتك مباشرة.</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("🔗 فتح رابط اليوتيوب للشروحات", "https://youtube.com")
    with c_r:
        st.markdown("""
        <div class="box-card">
            <h3>📅 جدول العطل والامتحانات المدرسية</h3>
            <p>• تابع هنا آخر أخبار العطل الرسمية.</p>
            <p>• جداول امتحانات نصف السنة والنهائية.</p>
        </div>
        """, unsafe_allow_html=True)

elif menu_choice == "🗂️ الدردشات المحفوظة":
    st.header("🗂️ سجل الدروس السابقة")
    if not st.session_state.saved_lessons:
        st.write("لا توجد دروس محفوظة حالياً. عند الضغط على (دردشة جديدة) سيحفظ الدرس هنا.")
    else:
        for item in st.session_state.saved_lessons:
            with st.expander(f"📁 درس بتاريخ: {item['time']}"):
                for m in item["chats"]:
                    st.write(f"**{m['role']}:** {m['content']}")

elif menu_choice == "👤 معلومات الطالب والحساب":
    st.header("👤 الملف الشخصي للطالب والحساب")
    col_s, col_acc = st.columns(2)
    with col_s:
        st.subheader("🎒 معلومات الطالب الدراسية")
        st.session_state.student_data["name"] = st.text_input("اسم الطالب:", st.session_state.student_data["name"])
        st.session_state.student_data["grade"] = st.selectbox("الصف:", ["الصف السابع", "الصف الثامن", "الصف التاسع", "الصف العاشر", "الصف الحادي عشر", "الصف الثاني عشر"])
        st.session_state.student_data["school"] = st.text_input("اسم المدرسة والمحافظة:", st.session_state.student_data["school"])
        if st.button("حفظ بيانات الطالب 💾"):
            st.success("تم حفظ بيانات الطالب بنجاح!")
    with col_acc:
        st.subheader("💳 تفاصيل حساب الاشتراك")
        st.write("**حالة الاشتراك:** نشط ومفعل ✅")
        st.write("**الباقة المختارة:** كورس واحد (15$)")
        st.write("**طريقة الدفع:** بطاقة كي كارد (Qi Card)")
