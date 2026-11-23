if not st.session_state.logged_in:
    st.markdown(
        f"<h3 style='text-align: center;'>{t_login_title}</h3>",
        unsafe_allow_html=True,
    )
    c_left, c_right = st.columns([2, 1])
    with c_left:
        with st.form("login_form"):
            email = st.text_input(
                t_email,
                value=st.session_state.user_email,
                placeholder="name@example.com",
            )
            password = st.text_input(
                t_password,
                type="password",
                placeholder="أدخل كلمة السر الخاصة بحسابك",
            )
            submit_button = st.form_submit_button(t_login_btn)
            if submit_button:
                clean_email = (email or "").strip().lower()
                clean_password = (password or "").strip()
                account_data = AUTHORIZED_ACCOUNTS.get(clean_email)
                if not is_valid_email(clean_email):
                    st.error("يرجى إدخال بريد إلكتروني صحيح.")
                elif not clean_password:
                    st.error("يرجى إدخال كلمة السر.")
                elif account_data is None:
                    st.error("هذا البريد الإلكتروني غير موجود في الحسابات المعتمدة.")
                elif account_data["password"] != clean_password:
                    st.error("كلمة السر غير صحيحة لهذا الحساب.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_email = clean_email
                    st.session_state.username = account_data["username"]
                    if st.session_state.trial_start is None:
                        st.session_state.trial_start = datetime.now()
                    st.rerun()
    with c_right:
        st.info(
            "✨ تسجيل الدخول بحسابكِ وكلمة سركِ\n\n• تجربة مجانية 24 ساعة\n•"
            " الباقات بعد التجربة:\n  - أسبوعي: **$2**\n  - شهري: **$10**\n "
            " - سنوي: **$50**"
        )
