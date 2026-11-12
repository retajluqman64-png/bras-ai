import streamlit as st
from openai import OpenAI

# إعداد الصفحة لتكون واسعة
st.set_page_config(
    page_title="BRAS AI",
    page_icon="💜",
    layout="wide"
)

# تخصيص الألوان (ثيم أسود وخلفيات مربعات بنفسجية أنيقة)
st.markdown("""
<style>
.stApp {
    background-color: #0d0614;
    color: #e0d8f0;
}
.main-title {
    text-align: center;
    color: #9b5de5;
    font-weight: bold;
    font-size: 3rem;
    margin-bottom: 30px;
}
.grid-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 20px;
    padding: 10px;
}
.stButton>button {
    width: 100%;
    height: 110px;
    background-color: #1a1026;
    color: #dfb2f4;
    border: 2px solid #9b5de5;
    border-radius: 20px;
    font-size: 1.1rem;
    font-weight: bold;
    transition: 0.3s;
    box-shadow: 0 4px 15px rgba(155, 93, 229, 0.3);
}
.stButton>button:hover {
    background-color: #38135e;
    color: white;
    border-color: #f15bb5;
    box-shadow: 0 6px 25px rgba(241, 91, 181, 0.5);
    transform: translateY(-4px);
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>💜 BRAS AI 💜</h1>", unsafe_allow_html=True)

# استدعاء مفتاح OpenAI من الـ Secrets بأمان
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.error("يرجى ضبط مفتاح OpenAI API في إعدادات Streamlit Secrets.")
else:
    client = OpenAI(api_key=api_key)

    # قائمة الأقسام مع الإيموجي والأوامر البرمجية الموجهة باسمكِ
    SECTIONS = {
        "المساعد الشامل": ("🤖", "You are BRAS AI, a versatile assistant created by Retaj Luqman ismail Gargary. Assist perfectly across all domains."),
        "المعلومات العامة": ("🌍", "You are BRAS AI, created by Retaj Luqman. Provide accurate, engaging general knowledge."),
        "المعلم الشامل": ("📚", "You are BRAS AI, an expert teacher created by Retaj Luqman. Explain subjects simply, considering Kurdistan educational context."),
        "تعليم اللغات": ("🗣️", "You are BRAS AI, a multilingual tutor created by Retaj Luqman. Teach English, Kurdish, Arabic, and Turkish gently."),
        "البرمجة": ("💻", "You are BRAS AI, an expert programmer created by Retaj Luqman. Write clean, well-explained code and debug."),
        "المعلومات الدينية": ("🕌", "You are BRAS AI, guiding on Islamic general knowledge created by Retaj Luqman. Provide reliable, moderate, and calm answers."),
        "الطبخ والوصفات": ("🍳", "You are BRAS AI, a master chef created by Retaj Luqman. Suggest delicious recipes with precise steps."),
        "استشارات الأطباء": ("🩺", "You are BRAS AI, a health advisor created by Retaj Luqman. Provide general health tips and strictly advise consulting real doctors."),
        "الصحة، الدايت والجيم": ("💪", "You are BRAS AI, a fitness coach created by Retaj Luqman. Help with BMI, diet plans, and workout routines."),
        "نصائح وتطوير الذات": ("💡", "You are BRAS AI, a life advisor created by Retaj Luqman. Give motivational, positive, and practical life advice."),
        "قسم الرسم": ("🎨", "You are BRAS AI, an art assistant created by Retaj Luqman. Generate detailed prompts for AI image generation."),
        "تعديل الصور - فوتوشوب": ("✨", "You are BRAS AI, an image editing expert created by Retaj Luqman. Guide users on professional image enhancement.")
    }

    if "selected_section" not in st.session_state:
        st.session_state.selected_section = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # الحالة الأولى: إذا لم يتم اختيار قسم، نعرض واجهة المربعات الرئيسية
    if st.session_state.selected_section is None:
        st.markdown("<p style='text-align: center; color: #dfb2f4; font-size: 1.2rem; margin-bottom: 25px;'>اخترِ القسم المناسب لبدء الإبداع:</p>", unsafe_allow_html=True)
        
        cols = st.columns(3)
        section_items = list(SECTIONS.items())
        
        for index, (sec_name, (emoji, prompt)) in enumerate(section_items):
            col = cols[index % 3]
            if col.button(f"{emoji}\n\n{sec_name}"):
                st.session_state.selected_section = sec_name
                st.rerun()
                
        st.markdown("<br><hr style='border-color: #38135e;'>", unsafe_allow_html=True)
        st.caption("✨ تم تصميم التطبيق خصيصاً لتلبية إبداعاتكِ ورؤيتكِ التقنية الرائعة.")

    # الحالة الثانية: عند اختيار قسم، تفتح صفحة المحادثة الخاصة به
    else:
        sec_name = st.session_state.selected_section
        emoji, system_prompt = SECTIONS[sec_name]
        
        col_back, col_title = st.columns([1, 6])
        if col_back.button("⬅️ الرئيسية"):
            st.session_state.selected_section = None
            st.session_state.messages = []
            st.rerun()
            
        col_title.markdown(f"<h3 style='color: #9b5de5;'>{emoji} {sec_name}</h3>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: #38135e; margin-top: 0px;'>", unsafe_allow_html=True)

        # عرض الرسائل السابقة داخل المحادثة
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # خانة إدخال الرسائل
        prompt = st.chat_input(f"تحدثي مع {sec_name}...")

        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    messages_payload = [{"role": "system", "content": system_prompt}] + [
                        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
                    ]

                    # إذا كان القسم متعلقاً بالرسم أو الفوتوشوب، نستخدم توليد الصور
                    if "الرسم" in sec_name or "فوتوشوب" in sec_name:
                        response = client.images.generate(
                            model="dall-e-3", prompt=prompt, size="1024x1024", quality="standard", n=1
                        )
                        image_url = response.data[0].url
                        full_response = f"تم تجهيز طلبكِ بنجاح!:\n\n![Result]({image_url})"
                    else:
                        response = client.chat.completions.create(model="gpt-4o", messages=messages_payload)
                        full_response = response.choices[0].message.content
                    
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                except Exception as e:
                    st.error(f"حدث خطأ أثناء المعالجة: {e}")
