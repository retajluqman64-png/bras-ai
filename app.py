import os
import streamlit as st
from openai import OpenAI

# إعداد الصفحة
st.set_page_config(
    page_title="BRAS AI",
    page_icon="💜",
    layout="wide"
)

# تنسيق الألوان (أسود وذهبي)
st.markdown("""
<style>
.stApp {
    background: #090812;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("💜 BRAS AI")

# استدعاء المفتاح بأمان من الـ Secrets
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.error("OpenAI API Key not found. Please set it in Streamlit Secrets.")
else:
    client = OpenAI(api_key=api_key)

    # الشريط الجانبي لاختيار القسم والصوت
    st.sidebar.title("إعدادات التطبيق")
    
    # اختيار القسم
    section = st.sidebar.selectbox(
        "اختر القسم:",
        [
            "المساعد الشامل (All-in-One)",
            "المعلومات العامة (General)",
            "المعلم الشامل (Study)",
            "تعليم اللغات (Languages)",
            "البرمجة (Programming)",
            "المعلومات الدينية (Religious)",
            "الطبخ والوصفات (Cooking)",
            "استشارات الأطباء (Doctors)",
            "الصحة، الدايت والجيم (Fitness & Diet)",
            "نصائح وتطوير الذات (Advice)",
            "قسم الرسم (Drawing)",
            "تعديل الصور - فوتوشوب (Photoshop)"
        ]
    )

    # اختيار الصوت
    voice_gender = st.sidebar.radio(
        "اختر صوت المساعد:",
        ("صوت بنت (Nova)", "صوت رجل (Onyx)")
    )
    gender_tag = "female" if "بنت" in voice_gender else "male"

    # الأوامر البرمجية الموجهة لكل قسم
    SECTIONS_PROMPTS = {
        "المساعد الشامل (All-in-One)": "You are BRAS AI, a versatile assistant created by Retaj Luqman ismail Gargary. You have all capabilities to assist the user perfectly.",
        "المعلومات العامة (General)": "You are BRAS AI, created by Retaj Luqman. Answer general questions accurately.",
        "المعلم الشامل (Study)": "You are BRAS AI, an expert school teacher created by Retaj Luqman. Explain subjects simply, considering the local context in Kurdistan.",
        "تعليم اللغات (Languages)": "You are BRAS AI, a multilingual tutor created by Retaj Luqman. Teach English, Kurdish, Arabic, and Turkish, correcting errors gently.",
        "البرمجة (Programming)": "You are BRAS AI, an expert programmer created by Retaj Luqman. Write clean, explained code and fix bugs.",
        "المعلومات الدينية (Religious)": "You are BRAS AI, guiding on Islamic general knowledge created by Retaj Luqman. Provide reliable, moderate answers calmly.",
        "الطبخ والوصفات (Cooking)": "You are BRAS AI, a chef created by Retaj Luqman. Suggest delicious recipes with exact steps.",
        "استشارات الأطباء (Doctors)": "You are BRAS AI, a health advisor created by Retaj Luqman. Provide general health tips, always advising to consult real doctors.",
        "الصحة، الدايت والجيم (Fitness & Diet)": "You are BRAS AI, a fitness coach created by Retaj Luqman. Help with BMI, diet plans, and workout routines.",
        "نصائح وتطوير الذات (Advice)": "You are BRAS AI, a life advisor created by Retaj Luqman. Give motivational and practical life advice.",
        "قسم الرسم (Drawing)": "You are BRAS AI, an art assistant created by Retaj Luqman. Help users create detailed prompts for AI image generation.",
        "تعديل الصور - فوتوشوب (Photoshop)": "You are BRAS AI, an image editing expert created by Retaj Luqman. Guide users on how to professionally edit and enhance images."
    }

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # عرض الرسائل السابقة
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # واجهة الإدخال
    prompt = st.chat_input("تحدث مع BRAS AI أو اطلب منه تنفيذ أمر...")

    if prompt:
        # إضافة رسالة المستخدم
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # إعداد الرسائل مع النظام (System Prompt) لضمان معرفة اسمكِ
                system_instruction = SECTIONS_PROMPTS.get(section, "You are BRAS AI by Retaj Luqman.")
                messages_payload = [{"role": "system", "content": system_instruction}] + [
                    {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
                ]

                # معالجة طلب الرسم أو التعديل
                if "الرسم" in section or "فوتوشوب" in section:
                    response = client.images.generate(
                        model="dall-e-3",
                        prompt=prompt,
                        size="1024x1024",
                        quality="standard",
                        n=1
                    )
                    image_url = response.data[0].url
                    full_response = f"تم تجهيز طلبكِ بنجاح! يمكنكِ مشاهدة النتيجة هنا:\n\n![Result]({image_url})"
                    st.markdown(full_response)
                else:
                    # الرد النصي والصوتي لباقي الأقسام
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages_payload
                    )
                    full_response = response.choices[0].message.content
                    st.markdown(full_response)
                    
                    # توليد الصوت
                    selected_voice = "onyx" if gender_tag == "male" else "nova"
                    audio_response = client.audio.speech.create(
                        model="tts-1",
                        voice=selected_voice,
                        input=full_response
                    )
                    audio_path = "temp_response.mp3"
                    audio_response.stream_to_file(audio_path)
                    st.audio(audio_path, format="audio/mp3")

                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"حدث خطأ أثناء المعالجة: {e}")
