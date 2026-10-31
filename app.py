import streamlit as st

# إعدادات الصفحة وتصميمها الأنيق
st.set_page_config(page_title="Bras AI", page_icon="🤖", layout="centered")




# واجهة الترحيب والهوية الرسمية
st.title("🤖 Bras AI - مساعدكِ الذكي المتعدد اللغات")
st.markdown("### مرحباً بكِ في عالم الذكاء الاصطناعي! 🌸")

st.markdown(
    """
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px;">
        <p><b>تطوير وبرمجة:</b> ريتاج لقمان إسماعيل الجرجري (رتوجه)</p>
        <p>مساعد ذكي يدعم اللغات: <b>العربية، الكوردية (باديني)، التركية، والإنكليزية</b>.</p>
    </div>
    """, 
    unsafe_allow_html=True
)

st.write("---")

# اختيار لغة المحادثة
language = st.selectbox(
    "اختر لغتك المفضلة / Select your preferred language:",
    ["العربية", "Kurdî (Badînî)", "Türkçe", "English"]
)

# صندوق إدخال السؤال
user_query = st.text_input("اكتب سؤالك هنا / Write your question here:")

if st.button("إرسال / Send"):
    if user_query:
        if language == "العربية":
            st.success(f"أهلاً بكِ يا رتوجه! لقد تلقيت سؤالكِ: '{user_query}'. أنا هنا لمساعدتك دائماً! 🚀")
        elif language == "Kurdî (Badînî)":
            st.success(f"بشخێر هاتى رەتوجه! پەیاما تە گەهشت: '{user_query}'. ئەز ل ڤێرەم بۆ هاریکاریا تە! 🌟")
        elif language == "Türkçe":
            st.success(f"Hoş geldin Retaj! Mesajını aldım: '{user_query}'. Sana yardım etmek için buradayım! ✨")
        else:
            st.success(f"Hello Retaj! Received your query: '{user_query}'. I'm here to help you! 💻")
    else:
        st.warning("الرجاء كتابة سؤالك أولاً! / Please type your question first!")

# تذييل الصفحة
st.write("---")
st.caption("© 2026 Bras AI - All rights reserved for Retaj Luqman.")
