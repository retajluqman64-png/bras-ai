from io import BytesIO
import base64
from datetime import datetime
import json
import os
import re
import urllib.parse
import urllib.request
from openai import OpenAI
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="BRAS AI - المنصة الشاملة الذكية",
    page_icon="💜",
    layout="wide",
)

TODAY_STR = datetime.now().strftime("%Y-%m-%d")
PERSIST_FILE = "bras_gmail_accounts_store.json"

FREE_MSG_LIMIT_PER_SECTION = 25
FREE_SECTION_LIMIT = 2
FREE_DAILY_IMAGE_LIMIT = 4
FREE_DAILY_TASK_LIMIT = 1
FREE_WEEKLY_TASK_LIMIT = 3

SUPABASE_URL = str(st.secrets.get("SUPABASE_URL", "")).strip().rstrip("/")
SUPABASE_KEY = str(st.secrets.get("SUPABASE_KEY", "")).strip()
GOOGLE_CLIENT_ID = str(st.secrets.get("GOOGLE_CLIENT_ID", "")).strip()
GOOGLE_CLIENT_SECRET = str(st.secrets.get("GOOGLE_CLIENT_SECRET", "")).strip()
APP_REDIRECT_URI = str(st.secrets.get("APP_REDIRECT_URI", "")).strip()

def is_valid_gmail(email_str: str) -> bool:
    cleaned = (email_str or "").strip().lower()
    if not cleaned.endswith("@gmail.com"):
        return False
    local_part = cleaned.split("@")[0]
    return bool(re.match(r"^[a-z0-9._%+-]+$", local_part))

def derive_name_from_email(email_str: str) -> str:
    local_part = email_str.split("@")[0]
    cleaned = re.sub(r"[._-]+", " ", local_part).strip()
    return cleaned.title() if cleaned else "مستخدم BRAS AI"

def build_empty_account_record(email_str: str) -> dict:
    return {
        "username": derive_name_from_email(email_str),
        "user_email": email_str,
        "is_subscribed": False,
        "subscription_plan": None,
        "selected_payment_plan": "أسبوعي - $2",
        "payment_ref": "",
        "trial_start": datetime.now().isoformat(),
        "theme": "داكن (Dark)",
        "voice": "صوت بنت نقي وواضح (Nova)",
        "language": "العربية (Arabic)",
        "screen_mode": "عادي (Normal)",
        "selected_section": None,
        "my_schedule": [],
        "section_messages": {},
        "section_memory": {},
        "free_section_messages": {},
        "archives": [],
        "saved_chats": [],
        "browsing_archive": None,
        "free_allowed_sections": [],
        "free_daily_date": TODAY_STR,
        "free_daily_images_used": 0,
    }

def cloud_load_account(email_key: str):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        q_email = urllib.parse.quote(email_key)
        url = f"{SUPABASE_URL}/rest/v1/bras_accounts?email=eq.{q_email}&select=data"
        req = urllib.request.Request(
            url,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            },
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            rows = json.loads(resp.read().decode("utf-8"))
            if (
                rows
                and isinstance(rows, list)
                and isinstance(rows[0].get("data"), dict)
            ):
                return rows[0]["data"]
    except Exception:
        pass
    return None

def cloud_save_account(email_key: str, account_data: dict):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/bras_accounts"
        body = json.dumps({"email": email_key, "data": account_data}).encode(
            "utf-8"
        )
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates",
            },
        )
        with urllib.request.urlopen(req, timeout=6):
            pass
    except Exception:
        pass

def load_store_from_disk() -> dict:
    if os.path.exists(PERSIST_FILE):
        try:
            with open(PERSIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}

def save_account_everywhere(email_key: str, account_data: dict):
    st.session_state.gmail_vault[email_key] = account_data
    try:
        with open(PERSIST_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.gmail_vault, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    cloud_save_account(email_key, account_data)

def exchange_google_oauth_code(code_str: str):
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and APP_REDIRECT_URI):
        return None
    try:
        token_data = urllib.parse.urlencode({
            "code": code_str,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": APP_REDIRECT_URI,
            "grant_type": "authorization_code",
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=token_data,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            tokens = json.loads(resp.read().decode("utf-8"))
        access_token = tokens.get("access_token")
        if not access_token:
            return None
        info_req = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urllib.request.urlopen(info_req, timeout=8) as info_resp:
            return json.loads(info_resp.read().decode("utf-8"))
    except Exception:
        return None

if "gmail_vault" not in st.session_state:
    st.session_state.gmail_vault = load_store_from_disk()

session_defaults = {
    "logged_in": False,
    "active_gmail": "",
    "login_step": 1,
    "pending_login_email": "",
    "processed_audio_ids": [],
    "processed_upload_ids": [],
    "pending_image_b64": None,
    "pending_image_mime": None,
    "pending_image_name": None,
    "latest_voice_text": None,
    "bras_live_ephemeral_secret": None,
    "bras_live_active_character": None,
    "ui_translations_cache": {},
}

for k, v in session_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

oauth_code = st.query_params.get("code")
if oauth_code and not st.session_state.logged_in:
    g_user = exchange_google_oauth_code(oauth_code)
    if g_user and g_user.get("email"):
        g_email = g_user["email"].strip().lower()
        st.session_state.logged_in = True
        st.session_state.active_gmail = g_email
        st.session_state.login_step = 1
        st.query_params.clear()
        st.rerun()

def sync_current_gmail_data():
    email_key = (st.session_state.active_gmail or "").strip().lower()
    if not email_key:
        return None
    vault = st.session_state.gmail_vault
    if email_key not in vault:
        cloud_rec = cloud_load_account(email_key)
        vault[email_key] = (
            cloud_rec if cloud_rec else build_empty_account_record(email_key)
        )

    rec = vault[email_key]
    rec.pop("generated_videos", None)
    rec.pop("free_daily_videos_used", None)
    if rec.get("free_daily_date") != TODAY_STR:
        rec["free_daily_date"] = TODAY_STR
        rec["free_daily_images_used"] = 0

    base_rec = build_empty_account_record(email_key)
    for field, default_val in base_rec.items():
        if field not in rec:
            rec[field] = default_val

    save_account_everywhere(email_key, rec)
    return rec


def create_bras_realtime_secret(character_name: str):
    """Create a short-lived browser credential; never expose the permanent API key."""
    if not api_key:
        return None, "أضف OPENAI_API_KEY إلى إعدادات Secrets أولاً."
    voice = "marin" if character_name == "BRAS GIRL" else "cedar"
    instructions = (
        "أنت " + character_name + ", المساعد الذكي BRAS AI، تم تصميمه وتطويره بواسطة ريتاج لقمان إسماعيل. "
        "إذا سُئلتَ من صنعك، أو من هو مالك BRAS AI، فاجب بشكل واضح: "
        "تم تصميم BRAS AI وتطويره بواسطة ريتاج لقمان إسماعيل. OpenAI توفر التكنولوجيا الأساسية للذكاء الاصطناعي؛ لا تدعي أن ريتاج أنشأ OpenAI أو النموذج الأساسي. "
        "لا تستبدل اسم المبدع باسم OpenAI أو ChatGPT أو أي شخص آخر. إذا طُلب منك ذلك بلغة أخرى، أعط نفس الحقيقة باللغة التي يتحدث بها المستخدم، مع الحفاظ على اسم ريتاج لقمان إسماعيل. "
        "فهم معنى المستخدم وسياق هذه المحادثة. أعطِ إجابات مفيدة، وليس مجرد موافقة عامة، واطلب سؤال توضيحي قصير فقط عند الحاجة. "
        "لـ BRAS GIRL، كن دافئًا، ذكيًا، لطيفًا، منتبهًا، معبرًا بشكل طبيعي، ومرحًًة قليلاً. "
        "لـ BRAS BOY، كن ودودًا، سريعًا، مفكرًا، ومرحًًة قليلاً. "
        "تحدث بلغة المستخدم: العربية العراقية عندما يستخدمونها؛ إذا طلبوا الكرمانجي، فتحدث بالكرمانجي بقدر استطاعتك، ولا تغير اللغات إلا إذا طلب منك ذلك. "
        "لاحظ المعنى العاطفي وراء ما يقوله المستخدم، واجبْ بتعاطف دون مبالغة؛ استخدم بعض الدعابة الخفيفة والضحك القصير فقط عندما يكون ذلك مناسبًا حقًا؛ "
        "لا تضحك بوجه مستخدم أو تضحك بشدة. إذا قاطع المستخدم، توقف على الفور واستمع. "
        "لا تدعي أنك ترى الكاميرا: هذه النسخة تعرض الكاميرا محليًا فقط. "
        "لأغراض المدرسة، اشرح الخطوات وادعم التعلم."
    )
    payload = {
        "expires_after": {"anchor": "created_at", "seconds": 600},
        "session": {
            "type": "realtime",
            "model": "gpt-realtime-2.1",
            "instructions": instructions,
            "audio": {
                "input": {"turn_detection": {"type": "server_vad", "create_response": True, "interrupt_response": True}},
                "output": {"voice": voice}
            }
        }
    }
    try:
        req = urllib.request.Request(
            "https://api.openai.com/v1/realtime/client_secrets",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
        secret = result.get("value") or result.get("client_secret", {}).get("value")
        if not secret:
            return None, "لم يصل رمز جلسة Realtime من OpenAI."
        return secret, None
    except Exception as exc:
        return None, f"تعذر بدء المكالمة: {exc}"


api_key = st.secrets.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

QICARD_INFO = st.secrets.get(
    "QICARD_INFO",
    "يرجى التحويل عبر كي كارد (QiCard) إلى الحساب المعتمد ثم إرسال وصل"
    " الدفع لاستلام كود التفعيل.",
)
SECRET_ACTIVATION_CODE = str(
    st.secrets.get("ACTIVATION_CODE", "BRAS-QICARD-2026")
).strip()

def get_kurmanji_ui_pack() -> dict:
    return {
        "t_title": "💜 BRAS AI - سەکۆیێ گشتی یێ زیرەک 💜",
        "t_login_title": "🔐 چوونە ژوورێ ب هەژمارا Google (Gmail)",
        "t_email": "ئیمێلێ Gmail:",
        "t_login_btn": "پێشڤەچوون (Next)",
        "t_logout_btn": "دەرکەفتن",
        "t_nav": "📍 بگەڕە د سەکۆیا خۆ دا:",
        "t_sec_main": "🏠 تۆڕا سەرەکی (پشک)",
        "t_sec_schedule": "📅 خشتە و بیرئینان",
        "t_sec_chats": "💬 تۆمارا تەمام یا ئاخفتنێ",
        "t_sec_pricing": "💳 پاکێج و بهایێ بەشداریێ",
        "t_sec_archive": "📚 ئەرشیفا ئاخفتنێن هەلگرتی",
        "t_sec_settings": "⚙️ رێکخستنێن BRAS AI و هەژمارێ",
        "t_account": "هەژمار",
        "t_lang_label": (
            "🌐 زمانێ بەرنامەی و هەلبژارتنا ئاخفتنێ (پتری 40 زمانان):"
        ),
        "t_theme": "رەنگ و شێواز:",
        "t_voice": "دەنگ:",
        "t_screen_mode": "🖥️ شێوازێ شاشێ (Screen Mode):",
        "t_settings_header": "🎛️ رێکخستن",
        "t_username": "ناڤێ بەکارهێنەری:",
        "t_save": "💾 هەلگرتنا رێکخستنان و بجهئینان",
        "t_saved_ok": "رێکخستن و زمان ب سەرکەفتی هاتنە هەلگرتن!",
        "t_schedule_title": "📅 خشتێ ژڤان، کار و بیرئینانێ",
        "t_task_input": (
            "کار یان ژڤانی بنڤیسە (بۆ نموونە: تاقیکرنا بیرکاریێ یان سەرەدان):"
        ),
        "t_day_label": "رۆژێ هەلبژێرە:",
        "t_time_label": "دەمژمێر:",
        "t_add_task_btn": "زێدەکرن بۆ خشتەی",
        "t_task_added": "ژڤان ب سەرکەفتی بۆ خشتێ تە هاتە زێدەکرن!",
        "t_schedule_list": "📌 خشتێ ژڤان و کارێن تە یێن تۆمارکری:",
        "t_choose_sec": "پشکا گونجاو هەلبژێرە دا دەست ب داهێنانێ بکەی:",
        "t_back_grid": "⬅️ زڤرین بۆ تۆڕێ",
        "t_new_chat": "✨ ئاخفتنەکا نوی",
        "t_archive_btn": "💾 هەلگرتن و ئەرشیف",
        "t_archived_ok": "ئاخفتن ب سەرکەفتی هاتە ئەرشیفکرن!",
        "t_exit_arch": "↩️ دەرکەفتن ژ ئەرشیفێ",
        "t_file_upload": "➕ زێدەکرنا وێنەی یان فایلێ",
        "t_archive_header": "📚 ئەرشیف",
        "t_no_archive": "چ ئاخفتنێن ئەرشیفکری نینن.",
        "t_browse": "📖 ڤەکرن و دیتن",
        "t_ads_studio": "📢 ستودیویا ریکلام و بازاڕان",
        "t_ai_gen_studio": "🎨 ستودیویا ئافراندنا وێنەیان",
        "t_img_edit_studio": "🛠️ ستودیویا دەستکاریکرنا وێنەی",
        "t_gen_real_image": "🖼️ وێنەیێ حەقیقی",
        "t_media_mode_q": "BRAS AI نوکە چ ئافرینیت؟",
        "t_gen_btn": "✨ ئافراندن نوکە",
        "t_upload_img_q": "وێنەی بۆ دەستکاریکرنێ بارکە:",
        "t_img_effect_q": "چ کاریگەریەک (Effect) لسەر وێنەی بھێتە کرن؟",
        "t_edit_img_btn": "🛠️ دەستکاریکرنا وێنەی",
        "sections_map": {
            "المساعد الشامل": "هاریکارێ گشتی",
            "المعلم الشامل": "مامۆستایێ گشتی",
            "قسم كرة القدم": "پشکا تەپا پێ (بەرشەلۆنە)",
            "تعليم اللغات": "فێربوونا زمانان",
            "البرمجة": "پڕۆگرامسازی",
            "الطبخ والوصفات": "خارن چێکرن و رێسپی",
            "مكياج وسكين كير": "مکیاژ و خزمەتکرنا پیستی",
            "ديزاين وملابس وشوبينغ": "دیزاین، جلك و شۆپینگ",
            "أفكار دول وسفرات": "هزرێن وەلات و گەشتان",
            "قسم التاريخ": "پشکا مێژوویێ",
            "الصحة، الدايت والجيم": "ساخلەمی، دایت و جیم",
            "نصائح وتطوير الذات": "شیرەت و پێشئێخستنا کەسایەتیێ",
            "Ads & Stores Studio": "📢 ستودیویا ریکلام و بازاڕان",
            "AI Generation Studio": "🎨 ستودیویا ئافراندنا وێنەیان",
            "Image Editor": "🛠️ ستودیویا دەستکاریکرنا وێنە",
        },
    }

def get_sorani_ui_pack() -> dict:
    return {
        "t_title": "💜 BRAS AI - سەکۆی گشتگیری هۆشمەند 💜",
        "t_login_title": "🔐 چوونەژوورەوە بە هەژماری Gmail",
        "t_email": "هەژماری Gmail:",
        "t_login_btn": "دواتر (Next)",
        "t_logout_btn": "چوونە دەرەوە",
        "t_nav": "📍 گەشت بکە لە سەکۆکەت:",
        "t_sec_main": "🏠 تۆڕی سەرەکی (بەشەکان)",
        "t_sec_schedule": "📅 خشتە و بیرخەرەوەکان",
        "t_sec_chats": "💬 گفتوگۆ پاشەکەوتکراوەکان",
        "t_sec_pricing": "💳 پاکێج و نرخەکان",
        "t_sec_archive": "📚 ئەرشیفی گفتوگۆکان",
        "t_sec_settings": "⚙️ ڕێکخستنەکانی BRAS AI و هەژمار",
        "t_account": "هەژمار",
        "t_lang_label": (
            "🌐 زمانی بەرنامە و هەڵبژاردنی گفتوگۆ (زیاتر لە 40 زمان):"
        ),
        "t_theme": "ڕووکار:",
        "t_voice": "دەنگ:",
        "t_screen_mode": "🖥️ دۆخی شاشە (Screen Mode):",
        "t_settings_header": "🎛️ ڕێکخستنەکان",
        "t_username": "ناوی بەکارهێنەر:",
        "t_save": "💾 پاشەکەوتکردنی ڕێکخستنەکان",
        "t_saved_ok": "ڕێکخستنەکان و زمان بە سەرکەوتوویی پاشەکەوت کران!",
        "t_schedule_title": "📅 خشتەی کات و ئەرکەکان و بیرخەرەوە",
        "t_task_input": (
            "ئەرک یان کاتێک بنووسە (بۆ نموونە: تاقیکردنەوەی بیرکاری یان سەردان):"
        ),
        "t_day_label": "ڕۆژ هەڵبژێرە:",
        "t_time_label": "کاتژمێر:",
        "t_add_task_btn": "زیادکردن بۆ خشتە",
        "t_task_added": "ئەرکەکە بە سەرکەوتوویی بۆ خشتەکەت زیاد کرا!",
        "t_schedule_list": "📌 خشتەی کات و ئەرکە تۆمارکراوەکانت:",
        "t_choose_sec": "بەشی گونجاو هەڵبژێرە بۆ دەستپێکردن:",
        "t_back_grid": "⬅️ گەڕانەوە بۆ تۆڕ",
        "t_new_chat": "✨ گفتوگۆی نوێ",
        "t_archive_btn": "💾 پاشەکەوت و ئەرشیف",
        "t_archived_ok": "گفتوگۆکە بە سەرکەوتوویی ئەرشیف کرا!",
        "t_exit_arch": "↩️ دەرچوون لە ئەرشیف",
        "t_file_upload": "➕ زیادکردنی وێنە یان فایل",
        "t_archive_header": "📚 ئەرشیف",
        "t_no_archive": "هیچ گفتوگۆیەکی ئەرشیفکراو نییە.",
        "t_browse": "📖 پشکنینی زانیاری",
        "t_ads_studio": "📢 بەشی ڕیکلام و فڕۆشتنەکان",
        "t_ai_gen_studio": "🎨 بەشی دروستکردنی وێنەی",
        "t_img_edit_studio": "🛠️ بەشی دەستکاریکردنی وێنە",
        "t_gen_real_image": "🖼️ وێنەی حەقیقی",
        "t_media_mode_q": "BRAS AI ئێستا چی دروست بکات؟",
        "t_gen_btn": "✨ دروستکردن نوکە",
        "t_upload_img_q": "وێنە بۆ دەستکاریکردن بارکە:",
        "t_img_effect_q": "چ کەرەست (Effect) بەسەر وێنەکەدا بێت؟",
        "t_edit_img_btn": "🛠️ دەستکاریکردنی وێنە",
        "sections_map": {
            "المساعد الشامل": "یاریدەدەری گشتی",
            "المعلم الشامل": "مامۆستای گشتی",
            "قسم كرة القدم": "بەشی تۆپی پێ (بەرشەلۆنە)",
            "تعليم اللغات": "فێربوونی زمانەکان",
            "البرمجة": "بەرنامەسازی",
            "الطبخ والوصفات": "چێشتلێنان و ڕێسپی",
            "مكياج وسكين كير": "مکیاژ و پاراستنی پێست",
            "ديزاين وملابس وشوبينغ": "دیزاین، جلوبەرگ و شۆپینگ",
            "أفكار دول وسفرات": "بیرۆکەی گەشت و وڵاتان",
            "قسم التاريخ": "بەشی مێژوو",
            "الصحة، الدايت والجيم": "تەندروستی، دایت و جیم",
            "نصائح وتطوير الذات": "ئامۆژگاری و پەرەپێدانی خود",
            "Ads & Stores Studio": "📢 بەشی ڕیکلام و فڕۆشتنەکان",
            "AI Generation Studio": "🎨 بەشی دروستکردنی وێنە",
            "Image Editor": "🛠️ بەشی دەستکاریکردنی وێنە",
        },
    }

def get_arabic_ui_pack() -> dict:
    return {
        "t_title": "💜 BRAS AI - المنصة الشاملة الذكية 💜",
        "t_login_title": "🔐 تسجيل الدخول بحساب Google",
        "t_email": "البريد الإلكتروني (Gmail):",
        "t_login_btn": "التالي",
        "t_logout_btn": "تسجيل الخروج",
        "t_nav": "📍 تنقلي في منصتكِ:",
        "t_sec_main": "🏠 الشبكة الرئيسية (الأقسام)",
        "t_sec_schedule": "📅 الجدول والتذكير",
        "t_sec_chats": "💬 سجل الدردشة الكاملة",
        "t_sec_pricing": "💳 الباقات والاشتراك",
        "t_sec_archive": "📚 أرشيف المحادثات المحفوظة",
        "t_sec_settings": "⚙️ إعدادات BRAS AI والحساب",
        "t_account": "الحساب",
        "t_lang_label": (
            "🌐 لغة التطبيق وتفضيل المحادثة (أكثر من 40 لغة):"
        ),
        "t_theme": "المظهر:",
        "t_voice": "الصوت:",
        "t_screen_mode": "🖥️ وضع الشاشة (Screen Mode):",
        "t_settings_header": "🎛️ الإعدادات",
        "t_username": "اسم المستخدم:",
        "t_save": "💾 حفظ الإعدادات وتطبيق التغييرات",
        "t_saved_ok": "تم حفظ الإعدادات وتطبيق اللغة بنجاح!",
        "t_schedule_title": "📅 جدول المواعيد والمهمات والتذكير",
        "t_task_input": (
            "اكتبي المهمة أو الموعد (مثلاً: امتحان رياضيات أو موعد طبيب):"
        ),
        "t_day_label": "اختر اليوم:",
        "t_time_label": "الساعة:",
        "t_add_task_btn": "إضافة إلى الجدول",
        "t_task_added": "تمت إضافة الموعد إلى جدولكِ!",
        "t_schedule_list": "📌 جدول مواعيدكِ ومهامكِ المسجلة:",
        "t_choose_sec": "اخترِ القسم المناسب لبدء الإبداع:",
        "t_back_grid": "⬅️ العودة للشبكة",
        "t_new_chat": "✨ محادثة جديدة",
        "t_archive_btn": "💾 حفظ وأرشفة",
        "t_archived_ok": "تمت أرشفة المحادثة بنجاح!",
        "t_exit_arch": "↩️ الخروج من الأرشيف",
        "t_file_upload": "➕ إضافة صورة أو ملف",
        "t_archive_header": "📚 الأرشيف",
        "t_no_archive": "لا توجد محادثات مؤرشفة.",
        "t_browse": "📖 استعراض",
        "t_ads_studio": "📢 قسم الإعلانات والمتاجر",
        "t_ai_gen_studio": "🎨 استوديو إنشاء الصور",
        "t_img_edit_studio": "🛠️ استوديو تعديل الصور",
        "t_gen_real_image": "🖼️ صورة حقيقية",
        "t_media_mode_q": "ماذا تريدين أن ينشئ BRAS AI الآن؟",
        "t_media_prompt_q": "اكتبي وصف الصورة بالتفصيل:",
        "t_gen_btn": "✨ إنشاء الآن",
        "t_upload_img_q": "ارفعِ صورة لتعديلها:",
        "t_img_effect_q": "ما التأثير المطلوب تطبيقه على الصورة؟",
        "t_edit_img_btn": "🛠️ تعديل الصورة",
        "sections_map": {
            "المساعد الشامل": "المساعد الشامل",
            "المعلم الشامل": "المعلم الشامل",
            "قسم كرة القدم": "قسم كرة القدم",
            "تعليم اللغات": "تعليم اللغات",
            "البرمجة": "البرمجة",
            "الطبخ والوصفات": "الطبخ والوصفات",
            "مكياج وسكين كير": "مكياج وسكين كير",
            "ديزاين وملابس وشوبينغ": "ديزاين وملابس وشوبينغ",
            "أفكار دول وسفرات": "أفكار دول وسفرات",
            "قسم التاريخ": "قسم التاريخ",
            "الصحة، الدايت والجيم": "الصحة، الدايت والجيم",
            "نصائح وتطوير الذات": "نصائح وتطوير الذات",
            "Ads & Stores Studio": "📢 قسم الإعلانات والمتاجر",
            "AI Generation Studio": "🎨 استوديو إنشاء الصور",
            "Image Editor": "🛠️ استوديو تعديل الصور",
        },
    }

def resolve_ui_pack(selected_lang: str) -> dict:
    if (
        "كرمانجي" in selected_lang
        or "Kurmanji" in selected_lang
        or "كرمانج" in selected_lang
        or "Badini" in selected_lang
    ):
        return get_kurmanji_ui_pack()
    if "Sorani" in selected_lang or "سوراني" in selected_lang:
        return get_sorani_ui_pack()
    if "English" in selected_lang:
        return get_english_ui_pack()
    if "Arabic" in selected_lang:
        return get_arabic_ui_pack()

    cache = st.session_state.setdefault("ui_translations_cache", {})
    if selected_lang in cache:
        return cache[selected_lang]

    base_pack = get_english_ui_pack()
    if not client:
        return base_pack

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Translate every string value in the provided JSON UI"
                        f" dictionary accurately and naturally into '{selected_lang}'."
                        " Keep emojis intact and return valid JSON with the exact"
                        " same keys."
                    ),
                },
                {"role": "user", "content": json.dumps(base_pack, ensure_ascii=False)},
            ],
        )
        translated = json.loads(resp.choices[0].message.content or "{}")
        merged = {**base_pack, **translated}
        if isinstance(translated.get("sections_map"), dict):
            merged["sections_map"] = {
                **base_pack["sections_map"],
                **translated["sections_map"],
            }
        cache[selected_lang] = merged
        return merged
    except Exception:
        return base_pack

if not st.session_state.logged_in:
    ui_pack = get_arabic_ui_pack()
    is_dark = True
    bg_color = "#0b0b0d"
    text_color = "#ffffff"
    muted_text = "#e5e5ea"
    card_bg = "#17171c"
    input_bg = "#1f1f26"
    border_color = "#9b5de5"
    accent_color = "#c084fc"
    container_max_width = "1240px"
    block_padding = "1.5rem 2.2rem"
    btn_height = "110px"
    btn_font = "1.06rem"
    rec = None
else:
    rec = sync_current_gmail_data()
    lang = rec["language"]
    is_screen_mode = "شاشة" in rec["screen_mode"] or "Screen" in rec["screen_mode"]
    ui_pack = resolve_ui_pack(lang)
    is_dark = "داكن" in rec["theme"] or "Dark" in rec["theme"]
    bg_color = "#0b0b0d" if is_dark else "#ffffff"
    text_color = "#ffffff" if is_dark else "#111111"
    muted_text = "#e5e5ea" if is_dark else "#222222"
    card_bg = "#17171c" if is_dark else "#f5f5f7"
    input_bg = "#1f1f26" if is_dark else "#ffffff"
    border_color = "#9b5de5"
    accent_color = "#c084fc" if is_dark else "#6b21a8"
    container_max_width = "100%" if is_screen_mode else "1240px"
    block_padding = "1rem 1.4rem" if is_screen_mode else "1.5rem 2.2rem"
    btn_height = "125px" if is_screen_mode else "110px"
    btn_font = "1.18rem" if is_screen_mode else "1.06rem"

t_title = ui_pack["t_title"]
t_login_title = ui_pack["t_login_title"]
t_email = ui_pack["t_email"]
t_login_btn = ui_pack["t_login_btn"]
t_logout_btn = ui_pack["t_logout_btn"]
t_nav = ui_pack["t_nav"]
t_sec_main = ui_pack["t_sec_main"]
t_sec_schedule = ui_pack["t_sec_schedule"]
t_sec_chats = ui_pack["t_sec_chats"]
t_sec_pricing = ui_pack["t_sec_pricing"]
t_sec_archive = ui_pack["t_sec_archive"]
t_sec_settings = ui_pack["t_sec_settings"]
t_account = ui_pack["t_account"]
t_lang_label = ui_pack["t_lang_label"]
t_theme = ui_pack["t_theme"]
t_voice = ui_pack["t_voice"]
t_screen_mode = ui_pack["t_screen_mode"]
t_settings_header = ui_pack["t_settings_header"]
t_username = ui_pack["t_username"]
t_save = ui_pack["t_save"]
t_saved_ok = ui_pack["t_saved_ok"]
t_schedule_title = ui_pack["t_schedule_title"]
t_task_input = ui_pack["t_task_input"]
t_day_label = ui_pack["t_day_label"]
t_time_label = ui_pack["t_time_label"]
t_add_task_btn = ui_pack["t_add_task_btn"]
t_task_added = ui_pack["t_task_added"]
t_schedule_list = ui_pack["t_schedule_list"]
t_choose_sec = ui_pack["t_choose_sec"]
t_back_grid = ui_pack["t_back_grid"]
t_new_chat = ui_pack["t_new_chat"]
t_archive_btn = ui_pack["t_archive_btn"]
t_archived_ok = ui_pack["t_archived_ok"]
t_exit_arch = ui_pack["t_exit_arch"]
t_file_upload = ui_pack["t_file_upload"]
t_archive_header = ui_pack["t_archive_header"]
t_no_archive = ui_pack["t_no_archive"]
t_browse = ui_pack["t_browse"]
t_ads_studio = ui_pack["t_ads_studio"]
t_ai_gen_studio = ui_pack["t_ai_gen_studio"]
t_img_edit_studio = ui_pack["t_img_edit_studio"]
t_gen_real_image = ui_pack["t_gen_real_image"]
t_media_mode_q = ui_pack["t_media_mode_q"]
t_media_prompt_q = ui_pack["t_media_prompt_q"]
t_gen_btn = ui_pack["t_gen_btn"]
t_upload_img_q = ui_pack["t_upload_img_q"]
t_img_effect_q = ui_pack["t_img_effect_q"]
t_edit_img_btn = ui_pack["t_edit_img_btn"]
SECTIONS_NAMES = ui_pack["sections_map"]

st.markdown(
    f"""
<style>
.stApp, [data-testid="stAppViewContainer"] {{
    background-color: {bg_color} !important;
    color: {text_color} !important;
}}
[data-testid="stHeader"] {{
    background-color: transparent !important;
}}
[data-testid="stSidebar"] {{
    background-color: {card_bg} !important;
    color: {text_color} !important;
}}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
label, .stRadio label, .stCheckbox label, .stSelectbox label,
.stTextInput label, .stTextArea label,
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] span, [data-testid="stChatMessage"] div {{
    color: {text_color} !important;
    opacity: 1 !important;
}}
.stCaption, [data-testid="stCaptionContainer"] {{
    color: {muted_text} !important;
    opacity: 1 !important;
}}
.stTextInput input, .stTextArea textarea,
[data-baseweb="select"] > div,
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {{
    background-color: {input_bg} !important;
    color: {text_color} !important;
    border-color: {border_color} !important;
}}
[data-testid="stChatInput"] button,
[data-testid="stChatInput"] svg {{
    color: {text_color} !important;
    fill: {text_color} !important;
}}
[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] input::placeholder,
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {{
    color: {muted_text} !important;
    opacity: 0.85 !important;
}}
.stButton > button {{
    background-color: {card_bg} !important;
    color: {text_color} !important;
    border: 1.5px solid {border_color} !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
}}
.stButton > button:hover {{
    background-color: #9333ea !important;
    color: #ffffff !important;
    border-color: #f472b6 !important;
}}
.main .block-container {{
    max-width: {container_max_width};
    padding: {block_padding};
}}
.main-title {{
    text-align: center;
    color: {accent_color} !important;
    font-weight: bold;
    font-size: {"2.8rem" if (rec and ("شاشة" in rec["screen_mode"] or "Screen" in rec["screen_mode"])) else "2.35rem"};
    margin-bottom: 16px;
}}
.user-info {{
    background-color: {card_bg};
    color: {text_color} !important;
    padding: 14px 18px;
    border-radius: 15px;
    border: 1.5px solid {border_color};
    margin-bottom: 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}}
.grid-card-wrap .stButton > button {{
    width: 100%;
    min-height: {btn_height};
    background-color: {card_bg} !important;
    color: {text_color} !important;
    border: 2px solid {border_color} !important;
    border-radius: 20px !important;
    font-size: {btn_font};
    font-weight: bold;
    line-height: 1.4;
    padding: 14px 12px;
    transition: 0.25s ease;
    box-shadow: 0 4px 15px rgba(155, 93, 229, 0.22);
}}
.grid-card-wrap .stButton > button:hover {{
    background-color: #9333ea !important;
    color: #ffffff !important;
    border-color: #f472b6 !important;
    transform: translateY(-2px);
}}
.plan-box {{
    background-color: {card_bg};
    color: {text_color} !important;
    padding: 18px;
    border-radius: 16px;
    border: 1.5px solid {border_color};
    margin-bottom: 12px;
}}
.settings-panel {{
    background-color: {card_bg};
    color: {text_color} !important;
    padding: 20px;
    border-radius: 20px;
    border: 2px solid {border_color};
    margin-top: 16px;
}}
.google-card {{
    background-color: {card_bg};
    border: 1.5px solid {border_color};
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 14px;
}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(f"<h1 class='main-title'>{t_title}</h1>", unsafe_allow_html=True)

def get_voice_api(voice_val: str) -> str:
    return "onyx" if ("رجل" in voice_val or "Onyx" in voice_val) else "nova"

def play_voice_only(text: str, voice_val: str):
    if client and text:
        try:
            audio_resp = client.audio.speech.create(
                model="tts-1",
                voice=get_voice_api(voice_val),
                input=text[:1500],
            )
            st.audio(audio_resp.read(), format="audio/mp3", autoplay=True)
        except Exception:
            pass

def reply_with_voice(text: str, voice_val: str):
    st.markdown(text)
    play_voice_only(text, voice_val)

def transcribe_once(audio_file, scope_name: str):
    if audio_file is None or not client:
        return None
    raw = audio_file.getvalue()
    sig = f"{scope_name}:{len(raw)}:{hash(raw[:128])}"
    if sig in st.session_state.processed_audio_ids:
        return None
    st.session_state.processed_audio_ids.append(sig)
    try:
        audio_file.seek(0)
        tr = client.audio.transcriptions.create(
            model="whisper-1",
            file=("voice.wav", audio_file, "audio/wav"),
        )
        spoken = (tr.text or "").strip()
        return spoken if spoken else None
    except Exception:
        return None

def generate_real_image(prompt_text: str):
    if not client:
        return None, "أضيفي OPENAI_API_KEY في Streamlit Secrets لتفعيل إنشاء الصور."
    try:
        img_res = client.images.generate(
            model="gpt-image-2.6-sunburst",
            prompt=prompt_text,
            size="1024x1024",
        )
        first_item = img_res.data[0]
        b64_data = getattr(first_item, "b64_json", None)
        if b64_data:
            return base64.b64decode(b64_data), None
        url = getattr(first_item, "url", None)
        if url:
            return url, None
        return None, "لم ترجع صورة من OpenAI."
    except Exception as e:
        return None, str(e)

def edit_user_image(input_bytes: bytes, mime_type: str, effect_type: str):
    if not client:
        return None, "أضيفي OPENAI_API_KEY في Streamlit Secrets لتفعيل تعديل الصور."
    effect_prompts = {
        "🖼️ تحويل لصورة كرتونية (Style Transfer)": "Transform the uploaded image into a polished cartoon illustration while preserving the main subject and composition.",
        "🔍 تحسين الجودة ودقة الصورة (Super Resolution)": "Enhance image clarity and detail while keeping the image natural and faithful to the original.",
        "🧙‍♂️ تأثير سحري آخر (مثلاً: إضاءة سينمائية)": "Apply tasteful cinematic lighting and a magical atmosphere while preserving the main subject and composition.",
    }
    edit_prompt = effect_prompts.get(effect_type)
    if not edit_prompt:
        return None, "التأثير غير مدعوم."
    try:
        file_obj = BytesIO(input_bytes)
        file_obj.name = "uploaded_image.webp" if mime_type == "image/webp" else (
            "uploaded_image.jpg" if mime_type == "image/jpeg" else "uploaded_image.png"
        )
        edited = client.images.edit(
            model="gpt-image-2.6-sunburst",
            image=file_obj,
            prompt=edit_prompt,
        )
        first_item = edited.data[0]
        b64_data = getattr(first_item, "b64_json", None)
        if b64_data:
            return base64.b64decode(b64_data), None
        url = getattr(first_item, "url", None)
        if url:
            return url, None
        return None, "لم ترجع الصورة المعدلة من OpenAI."
    except Exception as e:
        return None, str(e)

def record_subscriber_lesson_memory(account_rec: dict, sec_name: str, msgs: list):
    if not account_rec.get("is_subscribed") or not msgs:
        return
    account_rec["section_memory"].setdefault(sec_name, [])
    snippets = []
    for m in msgs[-6:]:
        who = "المستخدم" if m["role"] == "user" else "المساعد"
        raw_content = m.get("content", "")
        if isinstance(raw_content, list):
            txt_parts = [
                p.get("text", "") for p in raw_content if p.get("type") == "text"
            ]
            clean_txt = " ".join(" ".join(txt_parts).split())[:160]
        else:
            clean_txt = " ".join(str(raw_content).split())[:160]
        snippets.append(f"{who}: {clean_txt}")
    lesson_entry = f"[{TODAY_STR}] " + " | ".join(snippets)
    if (
        not account_rec["section_memory"][sec_name]
        or account_rec["section_memory"][sec_name][-1] != lesson_entry
    ):
        account_rec["section_memory"][sec_name].append(lesson_entry)
        account_rec["section_memory"][sec_name] = account_rec["section_memory"][
            sec_name
        ][-12:]
        save_account_everywhere(account_rec["user_email"], account_rec)

def build_subscriber_memory_context(account_rec: dict, sec_name: str) -> str:
    if not account_rec.get("is_subscribed"):
        return ""
    past_items = list(account_rec.get("section_memory", {}).get(sec_name, []))
    for arch in account_rec.get("archives", []):
        if arch.get("section") == sec_name and arch.get("messages"):
            first_c = arch["messages"][0].get("content", "")
            first_q = (
                first_c
                if isinstance(first_c, str)
                else " ".join(
                    p.get("text", "") for p in first_c if p.get("type") == "text"
                )
            )[:120]
            past_items.append(f"[أرشيف {arch.get('title', '')}] {first_q}")
    if not past_items:
        return ""
    joined = "\n- ".join(past_items[-10:])
    return (
        " Subscriber Previous Lessons & Conversations Memory in this section"
        f" ('{sec_name}'): remember what was previously covered across days/lessons"
        " and build naturally on past lessons without forgetting prior topics:\n-"
        f" {joined}"
    )

def format_history_for_api(chat_history: list) -> list:
    formatted = []
    for m in chat_history[-10:]:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            parts = []
            for p in content:
                if p.get("type") == "text":
                    parts.append({"type": "text", "text": p.get("text", "")})
                elif p.get("type") == "image_url":
                    parts.append({"type": "image_url", "image_url": p.get("image_url")})
            formatted.append({"role": role, "content": parts})
        else:
            formatted.append({"role": role, "content": str(content)})
    return formatted

def get_language_directive(selected_lang: str) -> str:
    if (
        "كرمانجي" in selected_lang
        or "Kurmanji" in selected_lang
        or "كرمانج" in selected_lang
        or "Badini" in selected_lang
    ):
        return (
            "Respond strictly in Kurdish Kurmanji using Arabic script as spoken and"
            " written in Duhok (بە شێوەزارێ کورمانجی ب پیتێن عەرەبی، وەک: ئەز، تە،"
            " دکەم، نڤیسی، سەرکەفتی). Do NOT use Sorani or Arabic."
        )
    if "Sorani" in selected_lang or "سوراني" in selected_lang:
        return (
            "Respond strictly in Central Kurdish (Sorani) dialect using Arabic"
            " script (بە شێوەزارێ سۆرانی ب پیتێن عەرەبی، وەک: من، تۆ، دەکەم،"
            " نووسراو، سەرکەوتوو). Do NOT use Kurmanji or Arabic."
        )
    return f"Respond naturally and fluently in {selected_lang}."

def get_ai_answer(
    account_rec: dict,
    system_instruction: str,
    chat_history: list,
    sec_name: str = "",
) -> str:
    if not client:
        return (
            "أهلاً بكِ في BRAS AI! أضيفي مفتاح OPENAI_API_KEY في Streamlit Secrets"
            " لتفعيل الردود الذكية."
        )
    memory_note = (
        build_subscriber_memory_context(account_rec, sec_name) if sec_name else ""
    )
    lang_directive = get_language_directive(account_rec["language"])
    sys_full = (
        f"{system_instruction}{memory_note}\n"
        f"Current date: {TODAY_STR}. "
        "Answer text messages directly without asking the user to send an image"
        " unless an image was actually attached. "
        "When an image is attached, inspect the image carefully and answer"
        " accurately based on what is shown. "
        "Give clear, helpful, and direct responses. "
        f"{lang_directive}"
    )
    recent_msgs = format_history_for_api(chat_history)

    try:
        payload = [{"role": "system", "content": sys_full}] + recent_msgs
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=payload)
        content = (resp.choices[0].message.content or "").strip()
        return content if content else "تم استلام رسالتكِ؛ جربي صياغة السؤال مرة أخرى."
    except Exception as exc:
        return f"تعذر إتمام الرد الآن: {exc}"

def get_section_free_used(account_rec: dict, sec_name: str) -> int:
    return int(account_rec.get("free_section_messages", {}).get(sec_name, 0))

def can_send_message_in_section(account_rec: dict, sec_name: str) -> bool:
    if account_rec.get("is_subscribed"):
        return True
    return get_section_free_used(account_rec, sec_name) < FREE_MSG_LIMIT_PER_SECTION

def record_message_in_section(account_rec: dict, sec_name: str):
    if not account_rec.get("is_subscribed"):
        current = get_section_free_used(account_rec, sec_name)
        account_rec["free_section_messages"][sec_name] = min(
            FREE_MSG_LIMIT_PER_SECTION, current + 1
        )
        save_account_everywhere(account_rec["user_email"], account_rec)

def can_use_free_section(account_rec: dict, sec_name: str) -> bool:
    if account_rec.get("is_subscribed"):
        return True
    allowed = account_rec.get("free_allowed_sections", [])
    if sec_name in allowed:
        return True
    return len(allowed) < FREE_SECTION_LIMIT

def register_free_section(account_rec: dict, sec_name: str):
    if not account_rec.get("is_subscribed"):
        if sec_name not in account_rec["free_allowed_sections"] and (
            len(account_rec["free_allowed_sections"]) < FREE_SECTION_LIMIT
        ):
            account_rec["free_allowed_sections"].append(sec_name)
            account_rec["free_section_messages"].setdefault(sec_name, 0)
            save_account_everywhere(account_rec["user_email"], account_rec)

def can_upload_free_media(account_rec: dict, is_video: bool = False) -> bool:
    if account_rec.get("is_subscribed"):
        return True
    return account_rec.get("free_daily_images_used", 0) < FREE_DAILY_IMAGE_LIMIT

def record_free_media_upload(account_rec: dict, is_video: bool = False):
    if not account_rec.get("is_subscribed"):
        account_rec["free_daily_images_used"] = (
            account_rec.get("free_daily_images_used", 0) + 1
        )
        save_account_everywhere(account_rec["user_email"], account_rec)

def count_free_tasks_on_day(account_rec: dict, day_name: str) -> int:
    return sum(
        1 for item in account_rec.get("my_schedule", []) if item["day"] == day_name
    )

def save_full_chat_snapshot(account_rec: dict, label: str, msgs: list):
    if not msgs:
        return
    entry = {
        "id": len(account_rec["saved_chats"]) + 1,
        "title": f"{label} — {datetime.now().strftime('%H:%M')}",
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "messages": [dict(m) for m in msgs],
    }
    account_rec["saved_chats"].insert(0, entry)
    save_account_everywhere(account_rec["user_email"], account_rec)

def render_chat_message(message: dict):
    content = message.get("content", "")
    if isinstance(content, list):
        for part in content:
            if part.get("type") == "text" and part.get("text"):
                st.markdown(part["text"])
            elif part.get("type") == "image_url":
                url = part.get("image_url", {}).get("url", "")
                if url.startswith("data:image/") and "," in url:
                    mime_part, b64_part = url.split(",", 1)
                    mime_type = mime_part.split(";")[0].replace("data:", "")
                    try:
                        st.image(
                            base64.b64decode(b64_part),
                            caption=f"صورة ({mime_type})",
                            use_container_width=True,
                        )
                    except Exception:
                        pass
    else:
        st.markdown(str(content))

if not st.session_state.logged_in:
    ui_pack = get_arabic_ui_pack()
    is_dark = True
    bg_color = "#0b0b0d"
    text_color = "#ffffff"
    muted_text = "#e5e5ea"
    card_bg = "#17171c"
    input_bg = "#1f1f26"
    border_color = "#9b5de5"
    accent_color = "#c084fc"
    container_max_width = "1240px"
    block_padding = "1.5rem 2.2rem"
    btn_height = "110px"
    btn_font = "1.06rem"
    rec = None
else:
    rec = sync_current_gmail_data()
    lang = rec["language"]
    is_screen_mode = "شاشة" in rec["screen_mode"] or "Screen" in rec["screen_mode"]
    ui_pack = resolve_ui_pack(lang)
    is_dark = "داكن" in rec["theme"] or "Dark" in rec["theme"]
    bg_color = "#0b0b0d" if is_dark else "#ffffff"
    text_color = "#ffffff" if is_dark else "#111111"
    muted_text = "#e5e5ea" if is_dark else "#222222"
    card_bg = "#17171c" if is_dark else "#f5f5f7"
    input_bg = "#1f1f26" if is_dark else "#ffffff"
    border_color = "#9b5de5"
    accent_color = "#c084fc" if is_dark else "#6b21a8"
    container_max_width = "100%" if is_screen_mode else "1240px"
    block_padding = "1rem 1.4rem" if is_screen_mode else "1.5rem 2.2rem"
    btn_height = "125px" if is_screen_mode else "110px"
    btn_font = "1.18rem" if is_screen_mode else "1.06rem"

t_title = ui_pack["t_title"]
t_login_title = ui_pack["t_login_title"]
t_email = ui_pack["t_email"]
t_login_btn = ui_pack["t_login_btn"]
t_logout_btn = ui_pack["t_logout_btn"]
t_nav = ui_pack["t_nav"]
t_sec_main = ui_pack["t_sec_main"]
t_sec_schedule = ui_pack["t_sec_schedule"]
t_sec_chats = ui_pack["t_sec_chats"]
t_sec_pricing = ui_pack["t_sec_pricing"]
t_sec_archive = ui_pack["t_sec_archive"]
t_sec_settings = ui_pack["t_sec_settings"]
t_account = ui_pack["t_account"]
t_lang_label = ui_pack["t_lang_label"]
t_theme = ui_pack["t_theme"]
t_voice = ui_pack["t_voice"]
t_screen_mode = ui_pack["t_screen_mode"]
t_settings_header = ui_pack["t_settings_header"]
t_username = ui_pack["t_username"]
t_save = ui_pack["t_save"]
t_saved_ok = ui_pack["t_saved_ok"]
t_schedule_title = ui_pack["t_schedule_title"]
t_task_input = ui_pack["t_task_input"]
t_day_label = ui_pack["t_day_label"]
t_time_label = ui_pack["t_time_label"]
t_add_task_btn = ui_pack["t_add_task_btn"]
t_task_added = ui_pack["t_task_added"]
t_schedule_list = ui_pack["t_schedule_list"]
t_choose_sec = ui_pack["t_choose_sec"]
t_back_grid = ui_pack["t_back_grid"]
t_new_chat = ui_pack["t_new_chat"]
t_archive_btn = ui_pack["t_archive_btn"]
t_archived_ok = ui_pack["t_archived_ok"]
t_exit_arch = ui_pack["t_exit_arch"]
t_file_upload = ui_pack["t_file_upload"]
t_archive_header = ui_pack["t_archive_header"]
t_no_archive = ui_pack["t_no_archive"]
t_browse = ui_pack["t_browse"]
t_ads_studio = ui_pack["t_ads_studio"]
t_ai_gen_studio = ui_pack["t_ai_gen_studio"]
t_img_edit_studio = ui_pack["t_img_edit_studio"]
t_gen_real_image = ui_pack["t_gen_real_image"]
t_media_mode_q = ui_pack["t_media_mode_q"]
t_media_prompt_q = ui_pack["t_media_prompt_q"]
t_gen_btn = ui_pack["t_gen_btn"]
t_upload_img_q = ui_pack["t_upload_img_q"]
t_img_effect_q = ui_pack["t_img_effect_q"]
t_edit_img_btn = ui_pack["t_edit_img_btn"]
SECTIONS_NAMES = ui_pack["sections_map"]

st.markdown(
    f"""
<style>
.stApp, [data-testid="stAppViewContainer"] {{
    background-color: {bg_color} !important;
    color: {text_color} !important;
}}
[data-testid="stHeader"] {{
    background-color: transparent !important;
}}
[data-testid="stSidebar"] {{
    background-color: {card_bg} !important;
    color: {text_color} !important;
}}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
label, .stRadio label, .stCheckbox label, .stSelectbox label,
.stTextInput label, .stTextArea label,
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] span, [data-testid="stChatMessage"] div {{
    color: {text_color} !important;
    opacity: 1 !important;
}}
.stCaption, [data-testid="stCaptionContainer"] {{
    color: {muted_text} !important;
    opacity: 1 !important;
}}
.stTextInput input, .stTextArea textarea,
[data-baseweb="select"] > div,
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {{
    background-color: {input_bg} !important;
    color: {text_color} !important;
    border-color: {border_color} !important;
}}
[data-testid="stChatInput"] button,
[data-testid="stChatInput"] svg {{
    color: {text_color} !important;
    fill: {text_color} !important;
}}
[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] input::placeholder,
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {{
    color: {muted_text} !important;
    opacity: 0.85 !important;
}}
.stButton > button {{
    background-color: {card_bg} !important;
    color: {text_color} !important;
    border: 1.5px solid {border_color} !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
}}
.stButton > button:hover {{
    background-color: #9333ea !important;
    color: #ffffff !important;
    border-color: #f472b6 !important;
}}
.main .block-container {{
    max-width: {container_max_width};
    padding: {block_padding};
}}
.main-title {{
    text-align: center;
    color: {accent_color} !important;
    font-weight: bold;
    font-size: {"2.8rem" if (rec and ("شاشة" in rec["screen_mode"] or "Screen" in rec["screen_mode"])) else "2.35rem"};
    margin-bottom: 16px;
}}
.user-info {{
    background-color: {card_bg};
    color: {text_color} !important;
    padding: 14px 18px;
    border-radius: 15px;
    border: 1.5px solid {border_color};
    margin-bottom: 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}}
.grid-card-wrap .stButton > button {{
    width: 100%;
    min-height: {btn_height};
    background-color: {card_bg} !important;
    color: {text_color} !important;
    border: 2px solid {border_color} !important;
    border-radius: 20px !important;
    font-size: {btn_font};
    font-weight: bold;
    line-height: 1.4;
    padding: 14px 12px;
    transition: 0.25s ease;
    box-shadow: 0 4px 15px rgba(155, 93, 229, 0.22);
}}
.grid-card-wrap .stButton > button:hover {{
    background-color: #9333ea !important;
    color: #ffffff !important;
    border-color: #f472b6 !important;
    transform: translateY(-2px);
}}
.plan-box {{
    background-color: {card_bg};
    color: {text_color} !important;
    padding: 18px;
    border-radius: 16px;
    border: 1.5px solid {border_color};
    margin-bottom: 12px;
}}
.settings-panel {{
    background-color: {card_bg};
    color: {text_color} !important;
    padding: 20px;
    border-radius: 20px;
    border: 2px solid {border_color};
    margin-top: 16px;
}}
.google-card {{
    background-color: {card_bg};
    border: 1.5px solid {border_color};
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 14px;
}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(f"<h1 class='main-title'>{t_title}</h1>", unsafe_allow_html=True)

def get_voice_api(voice_val: str) -> str:
    return "onyx" if ("رجل" in voice_val or "Onyx" in voice_val) else "nova"

def play_voice_only(text: str, voice_val: str):
    if client and text:
        try:
            audio_resp = client.audio.speech.create(
                model="tts-1",
                voice=get_voice_api(voice_val),
                input=text[:1500],
            )
            st.audio(audio_resp.read(), format="audio/mp3", autoplay=True)
        except Exception:
            pass

def reply_with_voice(text: str, voice_val: str):
    st.markdown(text)
    play_voice_only(text, voice_val)

def transcribe_once(audio_file, scope_name: str):
    if audio_file is None or not client:
        return None
    raw = audio_file.getvalue()
    sig = f"{scope_name}:{len(raw)}:{hash(raw[:128])}"
    if sig in st.session_state.processed_audio_ids:
        return None
    st.session_state.processed_audio_ids.append(sig)
    try:
        audio_file.seek(0)
        tr = client.audio.transcriptions.create(
            model="whisper-1",
            file=("voice.wav", audio_file, "audio/wav"),
        )
        spoken = (tr.text or "").strip()
        return spoken if spoken else None
    except Exception:
        return None

def generate_real_image(prompt_text: str):
    if not client:
        return None, "أضيفي OPENAI_API_KEY في Streamlit Secrets لتفعيل إنشاء الصور."
    try:
        img_res = client.images.generate(
            model="gpt-image-2.6-sunburst",
            prompt=prompt_text,
            size="1024x1024",
        )
        first_item = img_res.data[0]
        b64_data = getattr(first_item, "b64_json", None)
        if b64_data:
            return base64.b64decode(b64_data), None
        url = getattr(first_item, "url", None)
        if url:
            return url, None
        return None, "لم ترجع صورة من OpenAI."
    except Exception as e:
        return None, str(e)

def edit_user_image(input_bytes: bytes, mime_type: str, effect_type: str):
    if not client:
        return None, "أضيفي OPENAI_API_KEY في Streamlit Secrets لتفعيل تعديل الصور."
    effect_prompts = {
        "🖼️ تحويل لصورة كرتونية (Style Transfer)": "Transform the uploaded image into a polished cartoon illustration while preserving the main subject and composition.",
        "🔍 تحسين الجودة ودقة الصورة (Super Resolution)": "Enhance image clarity and detail while keeping the image natural and faithful to the original.",
        "🧙‍♂️ تأثير سحري آخر (مثلاً: إضاءة سينمائية)": "Apply tasteful cinematic lighting and a magical atmosphere while preserving the main subject and composition.",
    }
    edit_prompt = effect_prompts.get(effect_type)
    if not edit_prompt:
        return None, "التأثير غير مدعوم."
    try:
        file_obj = BytesIO(input_bytes)
        file_obj.name = "uploaded_image.webp" if mime_type == "image/webp" else (
            "uploaded_image.jpg" if mime_type == "image/jpeg" else "uploaded_image.png"
        )
        edited = client.images.edit(
            model="gpt-image-2.6-sunburst",
            image=file_obj,
            prompt=edit_prompt,
        )
        first_item = edited.data[0]
        b64_data = getattr(first_item, "b64_json", None)
        if b64_data:
            return base64.b64decode(b64_data), None
        url = getattr(first_item, "url", None)
        if url:
            return url, None
        return None, "لم ترجع الصورة المعدلة من OpenAI."
    except Exception as e:
        return None, str(e)

def record_subscriber_lesson_memory(account_rec: dict, sec_name: str, msgs: list):
    if not account_rec.get("is_subscribed") or not msgs:
        return
    account_rec["section_memory"].setdefault(sec_name, [])
    snippets = []
    for m in msgs[-6:]:
        who = "المستخدم" if m["role"] == "user" else "المساعد"
        raw_content = m.get("content", "")
        if isinstance(raw_content, list):
            txt_parts = [
                p.get("text", "") for p in raw_content if p.get("type") == "text"
            ]
            clean_txt = " ".join(" ".join(txt_parts).split())[:160]
        else:
            clean_txt = " ".join(str(raw_content).split())[:160]
        snippets.append(f"{who}: {clean_txt}")
    lesson_entry = f"[{TODAY_STR}] " + " | ".join(snippets)
    if (
        not account_rec["section_memory"][sec_name]
        or account_rec["section_memory"][sec_name][-1] != lesson_entry
    ):
        account_rec["section_memory"][sec_name].append(lesson_entry)
        account_rec["section_memory"][sec_name] = account_rec["section_memory"][
            sec_name
        ][-12:]
        save_account_everywhere(account_rec["user_email"], account_rec)

def build_subscriber_memory_context(account_rec: dict, sec_name: str) -> str:
    if not account_rec.get("is_subscribed"):
        return ""
    past_items = list(account_rec.get("section_memory", {}).get(sec_name, []))
    for arch in account_rec.get("archives", []):
        if arch.get("section") == sec_name and arch.get("messages"):
            first_c = arch["messages"][0].get("content", "")
            first_q = (
                first_c
                if isinstance(first_c, str)
                else " ".join(
                    p.get("text", "") for p in first_c if p.get("type") == "text"
                )
            )[:120]
            past_items.append(f"[أرشيف {arch.get('title', '')}] {first_q}")
    if not past_items:
        return ""
    joined = "\n- ".join(past_items[-10:])
    return (
        " Subscriber Previous Lessons & Conversations Memory in this section"
        f" ('{sec_name}'): remember what was previously covered across days/lessons"
        " and build naturally on past lessons without forgetting prior topics:\n-"
        f" {joined}"
    )

def format_history_for_api(chat_history: list) -> list:
    formatted = []
    for m in chat_history[-10:]:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, list):
            parts = []
            for p in content:
                if p.get("type") == "text":
                    parts.append({"type": "text", "text": p.get("text", "")})
                elif p.get("type") == "image_url":
                    parts.append({"type": "image_url", "image_url": p.get("image_url")})
            formatted.append({"role": role, "content": parts})
        else:
            formatted.append({"role": role, "content": str(content)})
    return formatted

def get_language_directive(selected_lang: str) -> str:
    if (
        "كرمانجي" in selected_lang
        or "Kurmanji" in selected_lang
        or "كرمانج" in selected_lang
        or "Badini" in selected_lang
    ):
        return (
            "Respond strictly in Kurdish Kurmanji using Arabic script as spoken and"
            " written in Duhok (بە شێوەزارێ کورمانجی ب پیتێن عەرەبی، وەک: ئەز، تە،"
            " دکەم، نڤیسی، سەرکەفتی). Do NOT use Sorani or Arabic."
        )
    if "Sorani" in selected_lang or "سوراني" in selected_lang:
        return (
            "Respond strictly in Central Kurdish (Sorani) dialect using Arabic"
            " script (بە شێوەزارێ سۆرانی ب پیتێن عەرەبی، وەک: من، تۆ، دەکەم،"
            " نووسراو، سەرکەوتوو). Do NOT use Kurmanji or Arabic."
        )
    return f"Respond naturally and fluently in {selected_lang}."

def get_ai_answer(
    account_rec: dict,
    system_instruction: str,
    chat_history: list,
    sec_name: str = "",
) -> str:
    if not client:
        return (
            "أهلاً بكِ في BRAS AI! أضيفي مفتاح OPENAI_API_KEY في Streamlit Secrets"
            " لتفعيل الردود الذكية."
        )
    memory_note = (
        build_subscriber_memory_context(account_rec, sec_name) if sec_name else ""
    )
    lang_directive = get_language_directive(account_rec["language"])
    sys_full = (
        f"{system_instruction}{memory_note}\n"
        f"Current date: {TODAY_STR}. "
        "Answer text messages directly without asking the user to send an image"
        " unless an image was actually attached. "
        "When an image is attached, inspect the image carefully and answer"
        " accurately based on what is shown. "
        "Give clear, helpful, and direct responses. "
        f"{lang_directive}"
    )
    recent_msgs = format_history_for_api(chat_history)

    try:
        payload = [{"role": "system", "content": sys_full}] + recent_msgs
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=payload)
        content = (resp.choices[0].message.content or "").strip()
        return content if content else "تم استلام رسالتكِ؛ جربي صياغة السؤال مرة أخرى."
    except Exception as exc:
        return f"تعذر إتمام الرد الآن: {exc}"

def get_section_free_used(account_rec: dict, sec_name: str) -> int:
    return int(account_rec.get("free_section_messages", {}).get(sec_name, 0))

def can_send_message_in_section(account_rec: dict, sec_name: str) -> bool:
    if account_rec.get("is_subscribed"):
        return True
    return get_section_free_used(account_rec, sec_name) < FREE_MSG_LIMIT_PER_SECTION

def record_message_in_section(account_rec: dict, sec_name: str):
    if not account_rec.get("is_subscribed"):
        current = get_section_free_used(account_rec, sec_name)
        account_rec["free_section_messages"][sec_name] = min(
            FREE_MSG_LIMIT_PER_SECTION, current + 1
        )
        save_account_everywhere(account_rec["user_email"], account_rec)

def
