import os
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="BRAS AI",
    page_icon="💜",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: #090812;
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("💜 BRAS AI")

api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.error("OpenAI API Key not found. Please set it in Streamlit Secrets.")
else:
    client = OpenAI(api_key=api_key)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask Bras AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=st.session_state.messages
            )
            full_response = response.choices[0].message.content
            with st.chat_message("assistant"):
                st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
