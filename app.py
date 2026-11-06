import datetime
import streamlit as st
from openai import OpenAI

# 1. إعداد العميل (OpenAI Client) من الـ Secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 2. تحديد حدود الاستخدام المجاني
MAX_MESSAGES = 20
MAX_IMAGES = 5
MAX_VIDEOS = 1

# 3. إعداد وقت بداية الجلسة (للتحقق من مرور 24 ساعة)
if "session_start_time" not in st.session_state:
  st.session_state.session_start_time = datetime.datetime.now()

# 4. التحقق مما إذا مرت 24 ساعة لمسح الرسائل وسجل المحادثة
time_elapsed = datetime.datetime.now() - st.session_state.session_start_time
if time_elapsed.total_seconds() >= 86400:  # 86400 ثانية = 24 ساعة
  st.session_state.messages = []
  st.session_state.msg_count = 0
  st.session_state.img_count = 0
  st.session_state.video_count = 0
  st.session_state.session_start_time = datetime.datetime.now()
  st.warning("مرت 24 ساعة! تم إعادة ضبط المحادثة والعدادات المجانية تلقائياً.")

# 5. تهيئة العدادات وسجل المحادثات
if "messages" not in st.session_state:
  st.session_state.messages = []
if "msg_count" not in st.session_state:
  st.session_state.msg_count = 0
if "img_count" not in st.session_state:
  st.session_state.img_count = 0
if "video_count" not in st.session_state:
  st.session_state.video_count = 0

# عنوان التطبيق
st.title("💜 BRAS AI")

# الشريط الجانبي (العدادات والاشتراكات وروابط المتاجر)
with st.sidebar:
  st.header("📊 رصيدك المجاني المتبقي")
  st.write(
      f"💬 **الرسائل:** {max(0, MAX_MESSAGES - st.session_state.msg_count)} /"
      f" {MAX_MESSAGES}"
  )
  st.write(
      f"🖼️ **الصور:** {max(0, MAX_IMAGES - st.session_state.img_count)} /"
      f" {MAX_IMAGES}"
  )
  st.write(
      f"🎥 **الفيديو:** {max(0, MAX_VIDEOS - st.session_state.video_count)} /"
      f" {MAX_VIDEOS}"
  )
  st.caption("ملاحظة: تُمسح محادثات الحسابات المجانية تلقائياً بعد 24 ساعة.")

  st.divider()

  # عرض خطط الاشتراكات
  st.header("💎 خطط الاشتراك المميزة")
  st.markdown("""
    تريدي استخدام بلا حدود وبدون مسح للمحادثات؟ اختاري الخطّة المناسبة لكِ:
    * 🗓️ **اشتراك أسبوعي:** 5$ 
    * 📅 **اشتراك شهري:** 15$ 
    * 👑 **اشتراك سنوي:** 99$ *(الأوفُر والأفضل!)*
    """)

  st.write("💳 **طرق الدفع المتاحة:**")
  col1, col2 = st.columns(2)
  with col1:
    if st.button("Mastercard"):
      st.info("سيتم تحويلك لبوابة الدفع عبر Mastercard قريباً...")
  with col2:
    if st.button("Visa"):
      st.info("سيتم تحويلك لبوابة الدفع عبر Visa قريباً...")

  st.divider()

  # روابط التحميل من المتاجر ومتصفحات الهاتف
  st.header("📱 حمّلي تطبيق BRAS AI")
  st.markdown("متوفر الآن للاستخدام عبر المتصفح (Safari / Chrome) والمتاجر:")

  # زر App Store للأيفون
  st.link_button(
      "🍏 App Store (للأيفون)",
      "https://www.apple.com/app-store/",
      use_container_width=True,
  )

  # زر Google Play للأندرويد
  st.link_button(
      "🤖 Google Play (للأندرويد)",
      "https://play.google.com/",
      use_container_width=True,
  )

# 6. عرض المحادثات السابقة
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# 7. مربع إدخال الرسائل والتحقق من الحدود
if prompt := st.chat_input("تحدثي مع BRAS AI..."):
  if st.session_state.msg_count >= MAX_MESSAGES:
    st.error(
        "لقد استنفدتِ حد الـ 20 رسالة المجانية! 🛑\n\nيرجى الاشتراك في إحدى"
        " الباقات (أسبوعي 5$ / شهري 15$ / سنوي 99$) لمتابعة الاستخدام."
    )
  else:
    # إضافة رسالة المستخدم للسجل
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
      st.markdown(prompt)

    # زيادة عداد الرسائل
    st.session_state.msg_count += 1

    # طلب الرد من OpenAI
    with st.chat_message("assistant"):
      response = client.chat.completions.create(
          model="gpt-4o-mini",
          messages=[
              {"role": m["role"], "content": m["content"]}
              for m in st.session_state.messages
          ],
      )
      reply = response.choices[0].message.content
      st.markdown(reply)

    # إضافة رد الذكاء الاصطناعي للسجل
    st.session_state.messages.append({"role": "assistant", "content": reply})
