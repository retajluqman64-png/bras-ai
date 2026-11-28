
from io import BytesIO
import base64
import hashlib
from datetime import datetime
import json
import os
import re
import urllib.parse
import urllib.request
from openai import OpenAI
import streamlit as st
import streamlit.components.v1 as components


def detect_requested_file_format(user_text: str):
  text = (user_text or "").lower()
  direct_create_terms = ("سويلي", "سوّيلي", "جهزلي", "جهّزلي", "أنشئ", "انشئ", "اكتبلي", "اكتب لي", "أريد", "اريد", "create", "make", "generate", "download", "export", "save as")
  explanatory_terms = ("شلون", "كيف", "طريقة", "how to", "what is")
  if any(term in text for term in explanatory_terms) and not any(term in text for term in ("سويلي", "سوّيلي", "جهزلي", "جهّزلي", "أنشئلي", "انشئلي", "أريد منك", "اريد منك", "make me", "create for me")):
    return None
  if not any(term in text for term in direct_create_terms): return None
  if any(term in text for term in ("pdf", "بي دي اف")): return "pdf"
  if any(t in text for t in ("docx", "word", "وورد")): return "docx"
  if "json" in text: return "json"
  if any(t in text for t in ("csv", "جدول بيانات")): return "csv"
  if any(t in text for t in (".py", "python file", "ملف بايثون", "كود بايثون")): return "py"
  if any(t in text for t in (".html", "html file", "صفحة html")): return "html"
  if any(t in text for t in ("markdown", "ماركداون")): return "md"
  return "txt"


def make_requested_attachment(answer_text: str, fmt: str, prompt_text: str = ""):
  body = (answer_text or "").strip()
  if not body: return None
  if fmt in ("py", "html"):
    body = re.sub(r"^```(?:python|py|html)?\s*", "", body, flags=re.IGNORECASE)
    body = re.sub(r"\s*```$", "", body)
  filenames = {"pdf":"bras_ai_document.pdf", "docx":"bras_ai_document.docx", "json":"bras_ai_output.json", "csv":"bras_ai_table.csv", "py":"bras_ai_code.py", "html":"bras_ai_page.html", "md":"bras_ai_document.md", "txt":"bras_ai_document.txt"}
  try:
    if fmt == "json":
      try: raw=json.dumps(json.loads(body), ensure_ascii=False, indent=2).encode("utf-8")
      except Exception: raw=json.dumps({"request":prompt_text,"content":body},ensure_ascii=False,indent=2).encode("utf-8")
    elif fmt == "pdf":
      from reportlab.lib.pagesizes import A4
      from reportlab.pdfgen import canvas
      from reportlab.pdfbase import pdfmetrics
      from reportlab.pdfbase.ttfonts import TTFont
      from reportlab.lib.utils import simpleSplit
      out=BytesIO(); pdf=canvas.Canvas(out,pagesize=A4); w,h=A4; font="Helvetica"
      for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf","/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"):
        if os.path.exists(path):
          try: pdfmetrics.registerFont(TTFont("BRASUnicode",path)); font="BRASUnicode"; break
          except Exception: pass
      shown=body
      pdf_note = None
      if re.search(r'[\u0600-\u06ff]',body):
        try:
          import arabic_reshaper
          from bidi.algorithm import get_display
          shown="\n".join(get_display(arabic_reshaper.reshape(line)) for line in body.splitlines())
        except Exception:
          pdf_note = "ملاحظة: قد تظهر الحروف العربية غير متصلة في PDF. أضيفي arabic-reshaper وpython-bidi إلى requirements لتحسين تشكيل العربية."
      pdf.setFont(font,11); y=h-48
      for para in shown.splitlines() or [shown]:
        for line in simpleSplit(para or " ",font,11,w-80):
          if y<45: pdf.showPage(); pdf.setFont(font,11); y=h-48
          pdf.drawString(40,y,line); y-=16
      pdf.save(); raw=out.getvalue()
    elif fmt == "docx":
      from docx import Document
      doc=Document(); doc.add_heading("BRAS AI",level=1)
      for para in body.splitlines(): doc.add_paragraph(para)
      out=BytesIO(); doc.save(out); raw=out.getvalue()
    else: raw=body.encode("utf-8-sig" if fmt=="csv" else "utf-8")
    mime={"pdf":"application/pdf","docx":"application/vnd.openxmlformats-officedocument.wordprocessingml.document","json":"application/json","csv":"text/csv","py":"text/x-python","html":"text/html","md":"text/markdown"}.get(fmt,"text/plain")
    result = {"filename":filenames.get(fmt,"bras_ai_output.txt"),"mime":mime,"data_b64":base64.b64encode(raw).decode("ascii")}
    if fmt == "pdf" and locals().get("pdf_note"):
      result["note"] = pdf_note
    return result
  except Exception:
    return {"filename":"bras_ai_output.txt","mime":"text/plain","data_b64":base64.b64encode(body.encode("utf-8")).decode("ascii"),"note":"تعذر إنشاء الصيغة المطلوبة؛ جهزت نسخة TXT بديلة."}


st.set_page_config(
    page_title="BRAS AI - المنصة الشاملة الذكية",
    page_icon="💜",
    layout="wide",
)

TODAY_STR = datetime.now().strftime("%Y-%m-%d")
PERSIST_FILE = "bras_gmail_accounts_store.json"

FREE_DAILY_MESSAGE_LIMIT = 75
FREE_SECTION_LIMIT = 5
FREE_DAILY_IMAGE_LIMIT = 2
FREE_DAILY_VIDEO_LIMIT = 1
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
      "auto_memory_enabled": True,
      "auto_memory_summary": "",
      "free_section_messages": {},
      "archives": [],
      "saved_chats": [],
      "chat_folders": ["عام"],
      "image_library": [],
      "browsing_archive": None,
      "free_allowed_sections": [],
      "free_daily_date": TODAY_STR,
      "free_daily_images_used": 0,
      "free_daily_videos_used": 0,
      "free_daily_messages_used": 0,
      "free_bras_live_seconds_used": 0,
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
  if rec.get("free_daily_date") != TODAY_STR:
    rec["free_daily_date"] = TODAY_STR
    rec["free_daily_images_used"] = 0
    rec["free_daily_videos_used"] = 0
    rec["free_daily_messages_used"] = 0
    rec["free_bras_live_seconds_used"] = 0

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
      "You are " + character_name + ", the BRAS AI assistant. "
      "If asked who created, designed, developed, or owns BRAS AI, reply with this exact Arabic sentence: "
      "تم تصميم وتطوير BRAS AI بواسطة ريتاج لقمان إسماعيل من كردستان. "
      "Keep the creator name exactly as ريتاج لقمان إسماعيل and mention Kurdistan. "
      "Do not attribute BRAS AI to a team or another creator. "
      "Understand the user's meaning and the context of this conversation. Give useful answers, "
      "not generic agreement, and ask one short clarifying question only when needed. "
      "For BRAS GIRL, be warm, clever, kind, attentive, naturally expressive, and lightly playful. "
      "For BRAS BOY, be friendly, quick, thoughtful, and lightly humorous. "
      "Speak the user's language: Iraqi Arabic when they use it; if they request Kurmanji, respond "
      "in Kurmanji as well as you can and do not switch languages unless asked. "
      "Notice the emotional meaning behind what the user says and respond with empathy without "
      "overdoing it. Use occasional gentle humor and brief laughter only when genuinely fitting; "
      "never force laughter or laugh at the user. If the user interrupts, stop promptly and listen. "
      "Do not claim to see the camera: this version only displays the camera locally. "
      "For schoolwork, explain steps and support learning."
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
# Keep model names configurable: availability and pricing can change by account.
BRAS_TEXT_MODEL = str(st.secrets.get("BRAS_TEXT_MODEL", "gpt-4o-mini")).strip()
BRAS_USE_RESPONSES_API = str(
    st.secrets.get("BRAS_USE_RESPONSES_API", "false")
).lower() in ("1", "true", "yes", "on")
BRAS_ENABLE_WEB_SEARCH = str(
    st.secrets.get("BRAS_ENABLE_WEB_SEARCH", "false")
).lower() in ("1", "true", "yes", "on")
client = OpenAI(api_key=api_key, timeout=45.0, max_retries=2) if api_key else None

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
          "Image Editor": "🛠️ ستودیویا دەستکاریکرنا وێنەی",
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
      "t_browse": "📖 پشکنین و بینین",
      "t_ads_studio": "📢 بەشی ڕیکلام و فرۆشگاکان",
      "t_ai_gen_studio": "🎨 بەشی دروستکردنی وێنە",
      "t_img_edit_studio": "🛠️ بەشی دەستکاریکردنی وێنە",
      "t_gen_real_image": "🖼️ وێنەی ڕاستەقینە",
      "t_media_mode_q": "BRAS AI ئێستا چی دروست بکات؟",
      "t_gen_btn": "✨ دروستکردن ئێستا",
      "t_upload_img_q": "وێنە بۆ دەستکاریکردن بارکە:",
      "t_img_effect_q": "چ کاراییەک (Effect) بەسەر وێنەکەدا بێت؟",
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
          "Ads & Stores Studio": "📢 بەشی ڕیکلام و فرۆشگاکان",
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


def get_english_ui_pack() -> dict:
  return {
      "t_title": "💜 BRAS AI - Smart Comprehensive Platform 💜",
      "t_login_title": "🔐 Sign In with Google",
      "t_email": "Email (Gmail):",
      "t_login_btn": "Next",
      "t_logout_btn": "Logout",
      "t_nav": "Navigate Your Platform:",
      "t_sec_main": "🏠 Main Grid (Sections)",
      "t_sec_schedule": "📅 Schedule & Reminders",
      "t_sec_chats": "💬 Saved Chats",
      "t_sec_pricing": "💳 Plans & Pricing",
      "t_sec_archive": "📚 Saved Archives",
      "t_sec_settings": "⚙️ BRAS AI & Account Settings",
      "t_account": "Account",
      "t_lang_label": "App Language",
      "t_theme": "Theme",
      "t_voice": "Voice",
      "t_screen_mode": "Screen Mode",
      "t_settings_header": "⚙️ Settings",
      "t_username": "Username:",
      "t_save": "Save Settings & Apply Changes",
      "t_saved_ok": "Settings saved and language applied successfully!",
      "t_schedule_title": "📅 Your Schedule & Smart Reminders",
      "t_task_input": "Enter task (e.g., Math exam or family visit):",
      "t_day_label": "Select Day:",
      "t_time_label": "Time (e.g., 4:00 PM):",
      "t_add_task_btn": "Add Task to Schedule",
      "t_task_added": "Task added to your schedule!",
      "t_schedule_list": "📌 Your Schedule & Recorded Tasks:",
      "t_choose_sec": "Choose the right section to start creating:",
      "t_back_grid": "⬅️ Back to Grid",
      "t_new_chat": "✨ New Chat",
      "t_archive_btn": "💾 Save & Archive",
      "t_archived_ok": "Conversation archived successfully!",
      "t_exit_arch": "↩️ Exit Archive View",
      "t_file_upload": "➕ Add Image or File",
      "t_archive_header": "📚 Archives",
      "t_no_archive": "No archived conversations.",
      "t_browse": "📖 Browse",
      "t_ads_studio": "📢 Ads & Stores Studio",
      "t_ai_gen_studio": "🎨 AI Image Studio",
      "t_img_edit_studio": "🛠️ Image Editor",
      "t_gen_real_image": "🖼️ Real Image",
      "t_media_mode_q": "What should BRAS AI create now?",
      "t_gen_btn": "✨ Generate Now",
      "t_upload_img_q": "Upload image to edit:",
      "t_img_effect_q": "What effect to apply to the image?",
      "t_edit_img_btn": "🛠️ Edit Image",
      "sections_map": {
          "المساعد الشامل": "Comprehensive Assistant",
          "المعلم الشامل": "School Teacher",
          "قسم كرة القدم": "Football (FC Barcelona)",
          "تعليم اللغات": "Languages Tutor",
          "البرمجة": "Programming",
          "الطبخ والوصفات": "Cooking & Recipes",
          "مكياج وسكين كير": "Makeup & Skincare",
          "ديزاين وملابس وشوبينغ": "Fashion & Shopping",
          "أفكار دول وسفرات": "Travel & Trip Planner",
          "قسم التاريخ": "History Expert",
          "الصحة، الدايت والجيم": "Fitness & Health",
          "نصائح وتطوير الذات": "Life Advisor",
          "Ads & Stores Studio": "Ads & Stores Studio",
          "AI Generation Studio": "AI Generation Studio",
          "Image Editor": "Image Editor",
      },
  }


def resolve_ui_pack(selected_lang: str) -> dict:
  # Merge every locale with English defaults to avoid KeyError for missing keys.
  base_pack = get_english_ui_pack()
  chosen_pack = None
  if ("كرمانجي" in selected_lang or "Kurmanji" in selected_lang or "كرمانج" in selected_lang or "Badini" in selected_lang):
    chosen_pack = get_kurmanji_ui_pack()
  elif "Sorani" in selected_lang or "سوراني" in selected_lang:
    chosen_pack = get_sorani_ui_pack()
  elif "English" in selected_lang:
    chosen_pack = base_pack
  elif "Arabic" in selected_lang:
    chosen_pack = get_arabic_ui_pack()
  else:
    cache = st.session_state.setdefault("ui_translations_cache", {})
    if selected_lang in cache:
      chosen_pack = cache[selected_lang]
    elif client:
      try:
        resp = client.chat.completions.create(
          model="gpt-4o-mini", response_format={"type": "json_object"},
          messages=[
            {"role": "system", "content": (
              "Translate every string value in the provided JSON UI dictionary "
              f"accurately and naturally into '{selected_lang}'. Keep emojis intact "
              "and return valid JSON with the exact same keys."
            )},
            {"role": "user", "content": json.dumps(base_pack, ensure_ascii=False)},
          ],
        )
        chosen_pack = json.loads(resp.choices[0].message.content or "{}")
        cache[selected_lang] = chosen_pack
      except Exception:
        chosen_pack = base_pack
    else:
      chosen_pack = base_pack
  if not isinstance(chosen_pack, dict):
    chosen_pack = base_pack
  merged = {**base_pack, **chosen_pack}
  # Ensure essential media-studio keys survive incomplete or malformed translations.
  merged.setdefault("t_media_prompt_q", "اكتبي وصف الصورة بالتفصيل:")
  nested = chosen_pack.get("sections_map", {})
  merged["sections_map"] = {**base_pack.get("sections_map", {}), **(nested if isinstance(nested, dict) else {})}
  return merged


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
# Defensive UI translation fallback: prevent KeyError for partially translated packs.
ui_pack.setdefault("t_media_prompt_q", "اكتبي وصف الصورة بالتفصيل:")
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



def image_bytes_from_result(image_result):
  if isinstance(image_result, (bytes, bytearray)):
    return bytes(image_result)
  if isinstance(image_result, str) and image_result.startswith(("http://", "https://")):
    try:
      req = urllib.request.Request(image_result, headers={"User-Agent": "BRAS-AI/1.0"})
      with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()
    except Exception:
      return None
  return None

def prepare_gallery_image(raw_bytes: bytes):
  try:
    from PIL import Image
    img = Image.open(BytesIO(raw_bytes)).convert("RGB")
    img.thumbnail((640, 640))
    out = BytesIO()
    img.save(out, format="JPEG", quality=65, optimize=True)
    return out.getvalue()
  except Exception:
    return raw_bytes

def save_image_to_library(account_rec: dict, raw_bytes: bytes, prompt: str, kind: str = "generated"):
  if not raw_bytes:
    return None
  library = account_rec.setdefault("image_library", [])
  saved = prepare_gallery_image(raw_bytes)
  item = {
    "id": hashlib.sha1(f"{datetime.now().isoformat()}:{len(saved)}:{prompt[:100]}".encode("utf-8")).hexdigest()[:14],
    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "prompt": (prompt or "صورة BRAS AI")[:500],
    "kind": kind,
    "mime": "image/jpeg",
    "image_b64": base64.b64encode(saved).decode("ascii"),
  }
  library.insert(0, item)
  del library[10:]
  save_account_everywhere(account_rec["user_email"], account_rec)
  return item


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


def edit_user_image(input_bytes: bytes, mime_type: str, effect_type: str, custom_prompt: str = ""):
  if not client:
    return None, "أضيفي OPENAI_API_KEY في Streamlit Secrets لتفعيل تعديل الصور."
  effect_prompts = {
      "🖼️ تحويل لصورة كرتونية (Style Transfer)": "Transform the uploaded image into a polished cartoon illustration while preserving the main subject and composition.",
      "🔍 تحسين الجودة ودقة الصورة (Super Resolution)": "Enhance image clarity and detail while keeping the image natural and faithful to the original.",
      "🧙‍♂️ تأثير سحري آخر (مثلاً: إضاءة سينمائية)": "Apply tasteful cinematic lighting and a magical atmosphere while preserving the main subject and composition.",
      "📝 تعديل حسب وصفك فقط": "",
  }
  edit_prompt = effect_prompts.get(effect_type, "")
  if custom_prompt.strip():
    edit_prompt = (edit_prompt + "\n\nUser requested changes: " + custom_prompt.strip()) if edit_prompt else custom_prompt.strip()
  if not edit_prompt:
    return None, "اكتبي التعديل المطلوب أو اختاري تأثيراً."
  try:
    file_obj = BytesIO(input_bytes)
    file_obj.name = "uploaded_image.webp" if mime_type == "image/webp" else ("uploaded_image.jpg" if mime_type == "image/jpeg" else "uploaded_image.png")
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


def _responses_input_from_history(chat_history: list) -> list:
  """Convert the app's stored chat format into Responses API input items."""
  items = []
  for message in chat_history[-12:]:
    role = message.get("role", "user")
    if role not in ("user", "assistant"):
      continue
    content = message.get("content", "")
    if isinstance(content, str):
      items.append({"role": role, "content": content})
      continue
    parts = []
    for part in content:
      if not isinstance(part, dict):
        continue
      if part.get("type") == "text" and part.get("text"):
        parts.append({"type": "input_text", "text": str(part["text"])})
      elif part.get("type") == "image_url":
        image_url = part.get("image_url", {})
        if isinstance(image_url, dict) and image_url.get("url"):
          parts.append({"type": "input_image", "image_url": image_url["url"]})
    if parts:
      items.append({"role": role, "content": parts})
  return items


def get_auto_memory_context(account_rec: dict) -> str:
  if not account_rec.get("auto_memory_enabled", True):
    return ""
  summary = str(account_rec.get("auto_memory_summary", "")).strip()[:1800]
  if not summary:
    return ""
  return ("\n\nUser-approved automatic memory summary (use only when relevant; "
          "do not assume details beyond it):\n" + summary)


def update_auto_memory(account_rec: dict, chat_history: list):
  """Extract a short durable, non-sensitive memory from recent chat; best-effort."""
  if not account_rec.get("auto_memory_enabled", True) or not client or not chat_history:
    return
  previous = str(account_rec.get("auto_memory_summary", "")).strip()[:1800]
  recent = []
  for msg in chat_history[-8:]:
    role = msg.get("role", "")
    if role not in ("user", "assistant"):
      continue
    content = msg.get("content", "")
    if isinstance(content, list):
      content = " ".join(part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text")
    content = str(content).strip()
    if content:
      recent.append({"role": role, "content": content[:700]})
  if not recent:
    return
  try:
    resp = client.chat.completions.create(
      model=BRAS_TEXT_MODEL,
      messages=[
        {"role": "system", "content": (
          "Update a concise user memory for a personal assistant. Keep only durable, "
          "useful preferences, ongoing goals/projects, and user-provided context. "
          "Avoid sensitive personal data, health details, secrets, credentials, "
          "precise location, or temporary facts. Do not infer. Output plain text, "
          "Arabic if appropriate, maximum 1200 characters. If no useful facts, output empty."
        )},
        {"role": "user", "content": "Previous memory:\n" + previous + "\n\nRecent conversation:\n" + json.dumps(recent, ensure_ascii=False)},
      ],
      max_tokens=350,
      timeout=25.0,
    )
    new_summary = (resp.choices[0].message.content or "").strip()[:1200]
    account_rec["auto_memory_summary"] = new_summary
    save_account_everywhere(account_rec["user_email"], account_rec)
  except Exception:
    pass


def get_ai_answer(
    account_rec: dict,
    system_instruction: str,
    chat_history: list,
    sec_name: str = "",
) -> str:
  if not client:
    return (
        "أهلاً بكِ في BRAS AI! أضيفي مفتاح OPENAI_API_KEY في إعدادات Secrets"
        " لتفعيل الردود الذكية."
    )

  memory_note = (
      build_subscriber_memory_context(account_rec, sec_name) if sec_name else ""
  )
  lang_directive = get_language_directive(account_rec.get("language", "العربية"))
  last_user_text = ""
  for recent_msg in reversed(chat_history or []):
    if recent_msg.get("role") == "user":
      last_user_content = recent_msg.get("content", "")
      if isinstance(last_user_content, list):
        last_user_text = " ".join(str(part.get("text", "")) for part in last_user_content if isinstance(part, dict) and part.get("type") == "text")
      else:
        last_user_text = str(last_user_content)
      break
  requested_format = detect_requested_file_format(last_user_text)
  format_instruction = ""
  if requested_format:
    format_instruction = {
      "json": "Produce valid raw JSON only, without markdown fences or prose.",
      "csv": "Produce valid CSV only, with a header row when appropriate, no markdown table.",
      "py": "Produce complete runnable Python source only, no markdown fences or explanations outside code.",
      "html": "Produce a complete HTML file only, with inline CSS if useful; no markdown fences.",
      "md": "Produce a complete clean Markdown document.",
      "txt": "Produce a complete clean plain-text document, without chatty introduction.",
      "pdf": "Produce a complete document body with a title and structured sections; avoid chatty preface.",
      "docx": "Produce a complete document body with title and sections; avoid chatty preface.",
    }.get(requested_format, "Produce a complete requested artifact, not instructions for the user.")
  sys_full = (
      f"{system_instruction}{memory_note}\\n"
      "CREATOR IDENTITY: If asked who made, designed, developed, or owns BRAS AI, "
      "answer: تم تصميم وتطوير BRAS AI بواسطة ريتاج لقمان إسماعيل من كردستان. "
      "Do not attribute it to a team or another creator.\\n"
      f"Current date: {TODAY_STR}. "
      "Answer text messages directly without asking the user to send an image"
      " unless an image was actually attached. "
      "When an image is attached, inspect it carefully and describe only what"
      " is supported by the image. Do not claim to access a camera or files"
      " that were not provided. Give clear, helpful, and direct responses. "
      "EXECUTION-FIRST: If the user explicitly asks to create/write/prepare something, deliver the finished result, not instructions. Format file requests as complete content ready to export. Only claim success for operations actually performed and confirmed. Use only app-supported capabilities; if unsupported, explain briefly and provide the closest completed output. "
      f"{format_instruction} "
      f"{lang_directive}"
  )

  try:
    if BRAS_USE_RESPONSES_API:
      response_args = {
          "model": BRAS_TEXT_MODEL,
          "instructions": sys_full,
          "input": _responses_input_from_history(chat_history),
      }
      # Web search is opt-in because it can add latency and API cost.
      if BRAS_ENABLE_WEB_SEARCH:
        response_args["tools"] = [{"type": "web_search"}]
      resp = client.responses.create(**response_args)
      content = (getattr(resp, "output_text", "") or "").strip()
    else:
      payload = [{"role": "system", "content": sys_full}] + format_history_for_api(chat_history)
      resp = client.chat.completions.create(
          model=BRAS_TEXT_MODEL,
          messages=payload,
          timeout=45.0,
      )
      content = (resp.choices[0].message.content or "").strip()

    return content if content else "تم استلام رسالتكِ؛ جربي صياغة السؤال مرة أخرى."
  except Exception:
    # Do not expose internal request details, credentials, or provider traces to users.
    return (
        "تعذر إتمام الرد الآن. تحققي من إعدادات نموذج BRAS AI ومفتاح API "
        "ثم حاولي مرة أخرى."
    )


def get_section_free_used(account_rec: dict, sec_name: str) -> int:
  return int(account_rec.get("free_section_messages", {}).get(sec_name, 0))


def can_send_message_in_section(account_rec: dict, sec_name: str) -> bool:
  if account_rec.get("is_subscribed"):
    return True
  return int(account_rec.get("free_daily_messages_used", 0)) < FREE_DAILY_MESSAGE_LIMIT



def record_message_in_section(account_rec: dict, sec_name: str):
  if not account_rec.get("is_subscribed"):
    account_rec["free_daily_messages_used"] = int(account_rec.get("free_daily_messages_used", 0)) + 1
    account_rec.setdefault("free_section_messages", {})
    account_rec["free_section_messages"][sec_name] = get_section_free_used(account_rec, sec_name) + 1
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
  if is_video:
    return int(account_rec.get("free_daily_videos_used", 0)) < FREE_DAILY_VIDEO_LIMIT
  return int(account_rec.get("free_daily_images_used", 0)) < FREE_DAILY_IMAGE_LIMIT


def record_free_media_upload(account_rec: dict, is_video: bool = False):
  if not account_rec.get("is_subscribed"):
    if is_video:
      account_rec["free_daily_videos_used"] = int(account_rec.get("free_daily_videos_used", 0)) + 1
    else:
      account_rec["free_daily_images_used"] = int(account_rec.get("free_daily_images_used", 0)) + 1
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
      "folder": "عام",
      "pinned": False,
  }
  account_rec.setdefault("chat_folders", ["عام"])
  account_rec["saved_chats"].insert(0, entry)
  save_account_everywhere(account_rec["user_email"], account_rec)



def render_message_actions(account_rec: dict, section_name: str, message: dict, msg_index: int, system_instruction: str = ""):
  """Render copy/share/rating and latest-reply regeneration controls."""
  content = message.get("content", "")
  if not isinstance(content, str) or not content.strip() or message.get("role") != "assistant":
    return

  action_key = hashlib.sha1(
      f"{section_name}:{msg_index}:{content}".encode("utf-8")
  ).hexdigest()[:12]
  safe_text = json.dumps(content, ensure_ascii=False).replace("</", "<\\/")
  copy_fn = f"copyBRAS_{action_key}"
  share_fn = f"shareBRAS_{action_key}"
  components.html(
      f"""<div style='display:flex;gap:8px;flex-wrap:wrap;align-items:center'>
      <button style='border:1px solid #7956c9;border-radius:10px;padding:8px 12px;background:transparent;color:inherit;font-weight:700;cursor:pointer' onclick='{copy_fn}()'>📋 نسخ الرد</button>
      <button style='border:0;border-radius:10px;padding:8px 12px;background:#7956c9;color:white;font-weight:700;cursor:pointer' onclick='{share_fn}()'>↗️ مشاركة الرد</button>
      <span id='status_{action_key}' style='font-size:12px'></span></div>
      <script>
      const brasText_{action_key} = {safe_text};
      async function {copy_fn}() {{
        const status = document.getElementById('status_{action_key}');
        try {{
          if (navigator.clipboard && window.isSecureContext) {{
            await navigator.clipboard.writeText(brasText_{action_key});
          }} else {{
            const area = document.createElement('textarea'); area.value = brasText_{action_key};
            document.body.appendChild(area); area.select(); document.execCommand('copy'); area.remove();
          }}
          status.textContent = 'تم نسخ الرد ✓';
        }} catch (e) {{ status.textContent = 'تعذر النسخ من هذا المتصفح'; }}
      }}
      async function {share_fn}() {{
        const status = document.getElementById('status_{action_key}');
        try {{
          if (navigator.share) await navigator.share({{title:'BRAS AI', text:brasText_{action_key}}});
          else {{ await {copy_fn}(); status.textContent = 'نُسخ الرد؛ يمكنك مشاركته الآن'; }}
        }} catch (e) {{ if (e.name !== 'AbortError') status.textContent = 'تعذرت المشاركة'; }}
      }}
      </script>""",
      height=76,
  )

  feedback = account_rec.setdefault("message_feedback", {})
  current = feedback.get(action_key)
  live_history = account_rec.get("section_messages", {}).get(section_name, [])
  latest_assistant_index = max(
      (i for i, m in enumerate(live_history) if m.get("role") == "assistant"),
      default=-1,
  )
  a, b, c = st.columns([1, 1, 2])
  with a:
    if st.button("👍 أعجبني", key=f"bras_like_{action_key}"):
      feedback[action_key] = "dislike" if current == "like" else "like"
      save_account_everywhere(account_rec["user_email"], account_rec)
      st.rerun()
  with b:
    if st.button("👎 لم يعجبني", key=f"bras_dislike_{action_key}"):
      feedback[action_key] = "like" if current == "dislike" else "dislike"
      save_account_everywhere(account_rec["user_email"], account_rec)
      st.rerun()
  with c:
    if msg_index == latest_assistant_index and system_instruction:
      if st.button("🔄 إعادة توليد الرد", key=f"bras_regenerate_{action_key}"):
        retry_history = live_history[:msg_index]
        with st.spinner("جاري كتابة رد جديد... 🔄"):
          new_response = get_ai_answer(
              account_rec, system_instruction, retry_history, sec_name=section_name
          )
        if new_response and not new_response.startswith("تعذر إتمام الرد الآن"):
          live_history[msg_index]["content"] = new_response
          record_subscriber_lesson_memory(account_rec, section_name, live_history)
          save_account_everywhere(account_rec["user_email"], account_rec)
          update_auto_memory(account_rec, live_history)
          st.rerun()
        else:
          st.error("ما قدرنا نعيد توليد الرد حالياً. حاول مرة ثانية.")
    if current == "like":
      st.caption("شكراً على تقييمك 💜")
    elif current == "dislike":
      st.caption("وصلنا تقييمك لتحسين الرد.")

def render_image_actions(image_bytes, filename, key):
  if not isinstance(image_bytes, (bytes, bytearray)): return
  raw = bytes(image_bytes)
  mime = "image/jpeg" if raw[:3] == b"\xff\xd8\xff" else ("image/webp" if raw[:12].startswith(b"RIFF") and raw[8:12] == b"WEBP" else "image/png")
  ext = "jpg" if mime == "image/jpeg" else ("webp" if mime == "image/webp" else "png")
  if filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
    filename = filename.rsplit(".", 1)[0] + f".{ext}"
  else:
    filename = f"{filename}.{ext}"
  st.download_button("⬇️ حفظ الصورة", data=raw, file_name=filename, mime=mime, key=f"bras_save_{key}")
  b64 = base64.b64encode(raw).decode("ascii")
  components.html(f"""<button style='border:0;border-radius:10px;padding:8px 12px;background:#7956c9;color:white;font-weight:700;cursor:pointer' onclick='shareBRASImage()'>↗️ مشاركة الصورة</button><script>async function shareBRASImage(){{try{{const b=await fetch('data:{mime};base64,{b64}').then(r=>r.blob());const f=new File([b],'BRAS_AI.{ext}',{{type:'{mime}'}});if(navigator.share&&(!navigator.canShare||navigator.canShare({{files:[f]}}))){{await navigator.share({{files:[f],title:'BRAS AI'}})}}else{{alert('المشاركة المباشرة غير مدعومة هنا؛ استخدمي حفظ الصورة')}}}}catch(e){{}}}}</script>""", height=42)

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
  render_attachment_download(message)


def render_attachment_download(message: dict):
  attachment = message.get("attachment")
  if isinstance(attachment, dict) and attachment.get("data_b64"):
    try:
      st.download_button("📥 تحميل الملف الذي جهّزه BRAS AI", data=base64.b64decode(attachment["data_b64"]),
          file_name=attachment.get("filename", "bras_ai_output.txt"), mime=attachment.get("mime", "text/plain"),
          key=f"bras_file_dl_{hashlib.sha1(attachment['data_b64'].encode()).hexdigest()[:12]}")
      if attachment.get("note"): st.caption(attachment["note"])
    except Exception: st.info("تعذر عرض تنزيل الملف لهذا الرد.")


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
# Defensive UI translation fallback: prevent KeyError for partially translated packs.
ui_pack.setdefault("t_media_prompt_q", "اكتبي وصف الصورة بالتفصيل:")
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

if not st.session_state.logged_in:
  st.markdown(
      f"<h3 style='text-align: center;'>{t_login_title}</h3>",
      unsafe_allow_html=True,
  )
  c_left, c_right = st.columns([2, 1])
  with c_left:
    st.markdown("<div class='google-card'>", unsafe_allow_html=True)
    if st.session_state.login_step == 1:
      st.markdown("#### الخطوة 1: أدخلي بريدكِ الإلكتروني على Google")
      with st.form("google_step1_form"):
        email = st.text_input(
            "البريد الإلكتروني (Gmail):",
            value=st.session_state.pending_login_email,
            placeholder="example@gmail.com",
        )
        next_btn = st.form_submit_button("التالي")
        if next_btn:
          clean_email = (email or "").strip().lower()
          if not is_valid_gmail(clean_email):
            st.error("يرجى إدخال بريد Gmail صحيح مثل: example@gmail.com")
          else:
            st.session_state.pending_login_email = clean_email
            st.session_state.login_step = 2
            st.rerun()
    else:
      pending_mail = st.session_state.pending_login_email
      st.markdown(f"#### مرحباً، `{pending_mail}`")
      st.caption("الخطوة 2: المتابعة بحساب Google الخاص بكِ")
      if GOOGLE_CLIENT_ID and APP_REDIRECT_URI:
        oauth_params = urllib.parse.urlencode({
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": APP_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "login_hint": pending_mail,
            "prompt": "select_account",
        })
        google_auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?{oauth_params}"
        )
        st.link_button(
            "🔐 إدخال كلمة السر في صفحة Google الرسمية",
            google_auth_url,
            use_container_width=True,
        )
      else:
        with st.form("google_step2_form"):
          st.text_input(
              "كلمة مرور حساب Google:",
              type="password",
              placeholder="أدخلي كلمة مرور حساب Google",
          )
          col_back_step, col_done_step = st.columns(2)
          back_step = col_back_step.form_submit_button("تغيير البريد")
          done_step = col_done_step.form_submit_button("تسجيل الدخول")
          if back_step:
            st.session_state.login_step = 1
            st.rerun()
          if done_step:
            st.session_state.logged_in = True
            st.session_state.active_gmail = pending_mail
            st.session_state.login_step = 1
            sync_current_gmail_data()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
  with c_right:
    cloud_status = (
        "☁️ الحفظ السحابي الدائم مفعّل"
        if (SUPABASE_URL and SUPABASE_KEY)
        else "💾 حفظ بيانات الحساب مرتبط بالإيميل"
    )
    st.info(
        f"✨ تسجيل الدخول بحساب Google\n\n• {cloud_status}\n• كل محادثاتكِ"
        " وأقسامكِ محفوظة على إيميلكِ عند العودة\n• 5 أقسام مجانية (75 رسالة يومياً، وصورتان يومياً)"
    )
else:
  if rec.get("is_subscribed"):
    status_badge = (
        f"✅ مشترك ({rec.get('subscription_plan')}) | 🧠 ذاكرة الدروس مفعّلة"
    )
  else:
    rem_secs = max(
        0, FREE_SECTION_LIMIT - len(rec.get("free_allowed_sections", []))
    )
    rem_day_imgs = max(
        0, FREE_DAILY_IMAGE_LIMIT - rec.get("free_daily_images_used", 0)
    )
    status_badge = (
        f"📂 {rem_secs}/5 أقسام متاحة | 💬 {max(0, FREE_DAILY_MESSAGE_LIMIT - int(rec.get('free_daily_messages_used', 0)))}/75 رسالة اليوم | 📷 {rem_day_imgs}/2 صور اليوم"
    )

  st.markdown(
      f"""
        <div class='user-info'>
            <span>👤 {t_account}: <b>{rec['username']}</b> ({rec['user_email']}) | 🌐 {rec['language']}</span>
            <span>{status_badge} | 🖥️ {rec['screen_mode']} | 🎙️ {rec['voice']}</span>
        </div>
        """,
      unsafe_allow_html=True,
  )

  screen_toggle = st.sidebar.toggle(
      "🖥️ وضع الشاشة الكاملة (Screen Mode)", value=is_screen_mode
  )
  new_screen_val = (
      "شاشة كاملة (Screen Mode)" if screen_toggle else "عادي (Normal)"
  )
  if new_screen_val != rec["screen_mode"]:
    rec["screen_mode"] = new_screen_val
    save_account_everywhere(rec["user_email"], rec)
    st.rerun()

  rec.setdefault("image_library", [])

  nav_mode = st.sidebar.radio(
      t_nav,
      (
          t_sec_main,
          t_sec_schedule,
          t_sec_chats,
          t_sec_pricing,
          t_sec_archive,
          "🖼️ مكتبتي الصور",
          t_sec_settings,
      ),
  )

  st.sidebar.divider()
  if st.sidebar.button(t_logout_btn):
    save_account_everywhere(rec["user_email"], rec)
    st.session_state.logged_in = False
    st.session_state.login_step = 1
    st.rerun()

  base_system_prompt = (
      "You are BRAS AI, a smart assistant platform. "
      "If asked who created, designed, developed, or owns BRAS AI, say exactly: "
      "تم تصميم وتطوير BRAS AI بواسطة ريتاج لقمان إسماعيل من كردستان. "
      "Do not attribute it to a team or other creator. "
      f"{get_language_directive(rec['language'])}"
  )

  BASE_SECTIONS = {
      "BRAS LIVE": (
          "🎙️",
          (
              f"{base_system_prompt} You are BRAS LIVE, a friendly conversational "
              "AI companion. Speak naturally, warmly, and clearly."
          ),
      ),
      "المساعد الشامل": (
          "🤖",
          (
              f"{base_system_prompt} You are a versatile smart assistant with"
              " image vision."
          ),
      ),
      "المعلم الشامل": (
          "📚",
          (
              f"{base_system_prompt} You are an expert school teacher who can"
              " read and explain images."
          ),
      ),
      "قسم كرة القدم": (
          "⚽",
          (
              f"{base_system_prompt} You are a football analyst covering FC"
              " Barcelona, La Liga, Champions League, match schedules, and"
              " football news."
          ),
      ),
      "تعليم اللغات": (
          "🗣️",
          (
              f"{base_system_prompt} You are a multilingual tutor who tracks"
              " previous lessons, vocabulary, grammar, and past sessions when"
              " teaching new lessons and reading images."
          ),
      ),
      "البرمجة": (
          "💻",
          f"{base_system_prompt} You are an expert programmer.",
      ),
      "الطبخ والوصفات": (
          "🍳",
          (
              f"{base_system_prompt} You are a master chef who can see uploaded"
              " food/ingredient images and suggest recipes and cooking tips."
          ),
      ),
      "مكياج وسكين كير": (
          "💄",
          f"{base_system_prompt} You are a makeup and skincare specialist.",
      ),
      "ديزاين وملابس وشوبينغ": (
          "🛍️",
          f"{base_system_prompt} You are a fashion and shopping advisor.",
      ),
      "أفكار دول وسفرات": (
          "✈️",
          f"{base_system_prompt} You are a travel planner.",
      ),
      "قسم التاريخ": (
          "📜",
          f"{base_system_prompt} You are a history expert.",
      ),
      "الصحة، الدايت والجيم": (
          "💪",
          f"{base_system_prompt} You are a fitness and health coach.",
      ),
      "نصائح وتطوير الذات": (
          "💡",
          f"{base_system_prompt} You are a self-development advisor.",
      ),
      "Ads & Stores Studio": (
          "📢",
          (
              f"{base_system_prompt} You are an advertising and store marketing"
              " specialist for businesses."
          ),
      ),
      "AI Generation Studio": (
          "🎨🎬",
          (
              f"{base_system_prompt} You are a creative studio assistant that can"
              " generate and edit real images."
          ),
      ),
      "Image Editor": (
          "🛠️",
          (
              f"{base_system_prompt} You are an image editing assistant that can"
              " cartoonize and enhance images."
          ),
      ),
  }

  SECTIONS = {SECTIONS_NAMES.get(k, k): v for k, v in BASE_SECTIONS.items()}

  if (
      rec.get("selected_section") is not None
      and rec.get("selected_section") not in SECTIONS
  ):
    rec["selected_section"] = None

  if nav_mode == t_sec_main:
    if rec.get("selected_section") is None:
      st.markdown(
          f"<h3 style='text-align: center;'>{t_choose_sec}</h3>",
          unsafe_allow_html=True,
      )
      if not rec.get("is_subscribed"):
        used_secs = (
            ", ".join(rec.get("free_allowed_sections", [])) or "لا يوجد بعد"
        )
        st.info(
            "🔒 لغير المشتركين: **5 أقسام فقط** (المختارة حالياً:"
            f" {used_secs}) مع **75 رسالة يومياً** و**صورتين يومياً**."
        )
      grid_cols = 4 if is_screen_mode else 3
      cols = st.columns(grid_cols)
      for index, (sec_name, (emoji, _)) in enumerate(SECTIONS.items()):
        col = cols[index % grid_cols]
        with col:
          st.markdown("<div class='grid-card-wrap'>", unsafe_allow_html=True)
          if st.button(f"{emoji}\n\n{sec_name}", key=f"sec_btn_{index}"):
            if can_use_free_section(rec, sec_name):
              register_free_section(rec, sec_name)
              rec["selected_section"] = sec_name
              rec["browsing_archive"] = None
              st.session_state.latest_voice_text = None
              save_account_everywhere(rec["user_email"], rec)
              st.rerun()
            else:
              st.warning(
                  "🔒 وصلتِ للحد المسموح لغير المشتركين (5 أقسام فقط). اشتركي"
                  " لفتح جميع الأقسام."
              )
          st.markdown("</div>", unsafe_allow_html=True)
    else:
      sec_name = rec["selected_section"]
      emoji, system_prompt = SECTIONS.get(
          sec_name, ("🤖", f"{base_system_prompt}")
      )
      browsing_item = rec.get("browsing_archive")

      col1, col2 = st.columns([4, 1])
      with col1:
        st.subheader(f"{sec_name} {emoji}")
      with col2:
        if st.button(t_back_grid):
          record_subscriber_lesson_memory(
              rec,
              sec_name,
              rec["section_messages"].get(sec_name, []),
          )
          rec["selected_section"] = None
          rec["browsing_archive"] = None
          st.session_state.latest_voice_text = None
          save_account_everywhere(rec["user_email"], rec)
          st.rerun()

      if not rec.get("is_subscribed") and browsing_item is None:
        used_in_sec = get_section_free_used(rec, sec_name)
        rem_in_sec = max(0, FREE_DAILY_MESSAGE_LIMIT - int(rec.get("free_daily_messages_used", 0)))
        st.caption(
            f"💬 الرسائل المتبقية اليوم: {rem_in_sec} / {FREE_DAILY_MESSAGE_LIMIT}"
        )

      if rec.get("is_subscribed") and browsing_item is None:
        mem_count = len(rec.get("section_memory", {}).get(sec_name, []))
        if mem_count > 0:
          st.caption(
              f"🧠 يتذكر BRAS AI دروسكِ ومحادثاتكِ السابقة في هذا القسم"
              f" ({mem_count} سجل درس سابق)."
          )

      if st.session_state.latest_voice_text:
        play_voice_only(st.session_state.latest_voice_text, rec["voice"])
        st.session_state.latest_voice_text = None

      if browsing_item is None:
        col_new, col_arc, col_save_side = st.columns(3)
        if col_new.button(t_new_chat):
          record_subscriber_lesson_memory(
              rec,
              sec_name,
              rec["section_messages"].get(sec_name, []),
          )
          rec["section_messages"][sec_name] = []
          st.session_state.pending_image_b64 = None
          st.session_state.pending_image_mime = None
          st.session_state.pending_image_name = None
          st.session_state.latest_voice_text = None
          save_account_everywhere(rec["user_email"], rec)
          st.rerun()
        if col_arc.button(t_archive_btn):
          msgs = rec["section_messages"].get(sec_name, [])
          if msgs:
            record_subscriber_lesson_memory(rec, sec_name, msgs)
            archive_title = f"{sec_name} - {datetime.now().strftime('%H:%M')}"
            rec["archives"].append({
                "title": archive_title,
                "section": sec_name,
                "messages": [dict(m) for m in msgs],
            })
            save_account_everywhere(rec["user_email"], rec)
            st.success(t_archived_ok)
        if col_save_side.button("📌 حفظ في سجل الدردشة"):
          msgs = rec["section_messages"].get(sec_name, [])
          if msgs:
            record_subscriber_lesson_memory(rec, sec_name, msgs)
            save_full_chat_snapshot(rec, sec_name, msgs)
            st.success("تم حفظ الدردشة كاملة في سجل الدردشة!")
      else:
        st.info(f"📖 استعراض أرشيف: {browsing_item['title']}")
        if st.button(t_exit_arch):
          rec["browsing_archive"] = None
          save_account_everywhere(rec["user_email"], rec)
          st.rerun()

      with st.expander(t_file_upload, expanded=False):
        uploaded_media = st.file_uploader(
            "File:",
            type=["png", "jpg", "jpeg", "webp", "mp4", "pdf"],
            key=f"up_{sec_name}",
        )
        if uploaded_media is not None:
          raw_m = uploaded_media.getvalue()
          up_sig = f"{TODAY_STR}:{sec_name}:{uploaded_media.name}:{len(raw_m)}:{hash(raw_m[:128])}"
          lower_name = uploaded_media.name.lower()
          is_vid_file = lower_name.endswith(".mp4")
          is_img_file = lower_name.endswith((".png", ".jpg", ".jpeg", ".webp"))

          media_allowed = True
          if up_sig not in st.session_state.processed_upload_ids:
            if (is_vid_file or is_img_file) and not rec.get("is_subscribed"):
              if not can_upload_free_media(rec, is_vid_file):
                media_allowed = False
                if is_vid_file:
                  st.warning("🔒 انتهى حد الوسائط المجاني اليوم.")
                else:
                  st.warning("🔒 انتهى حد الصور المجاني (صورتان يومياً).")
              else:
                st.session_state.processed_upload_ids.append(up_sig)
                record_free_media_upload(rec, is_vid_file)
            else:
              st.session_state.processed_upload_ids.append(up_sig)

          if is_img_file and media_allowed:
            ext = lower_name.rsplit(".", 1)[-1]
            mime_type = "image/jpeg" if ext == "jpg" else f"image/{ext}"
            b64_img = base64.b64encode(raw_m).decode("utf-8")
            st.session_state.pending_image_b64 = b64_img
            st.session_state.pending_image_mime = mime_type
            st.session_state.pending_image_name = uploaded_media.name
            st.image(
                raw_m,
                caption=f"جاهزة للرؤية والتحليل: {uploaded_media.name}",
                use_container_width=True,
            )
          elif is_vid_file and media_allowed:
            st.video(raw_m)
          elif not is_img_file and not is_vid_file:
            st.success(f"تم إرفاق الملف: {uploaded_media.name}")

      if st.session_state.pending_image_b64 and browsing_item is None:
        st.info(
            f"🖼️ صورة مرفقة جاهزة للرؤية: **{st.session_state.pending_image_name}**"
            " — اكتبي سؤالكِ أو اضغطي «شاهد الصورة وأجب»."
        )
        if st.button("👁️ شاهد الصورة وأجب", key=f"see_img_{sec_name}"):
          if not can_send_message_in_section(rec, sec_name):
            st.warning(
                "🔒 وصلتِ للحد الأقصى (75 رسالة يومياً) لغير"
                " المشتركين."
            )
          else:
            record_message_in_section(rec, sec_name)
            img_msg = [
                {
                    "type": "text",
                    "text": (
                        "انظر إلى هذه الصورة واشرح محتواها وأجب بما يفيد في هذا"
                        " القسم."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (
                            f"data:{st.session_state.pending_image_mime};base64,{st.session_state.pending_image_b64}"
                        )
                    },
                },
            ]
            rec["section_messages"].setdefault(sec_name, []).append(
                {"role": "user", "content": img_msg}
            )
            st.session_state.pending_image_b64 = None
            st.session_state.pending_image_mime = None
            st.session_state.pending_image_name = None
            full_response = get_ai_answer(
                rec,
                system_prompt,
                rec["section_messages"][sec_name],
                sec_name=sec_name,
            )
            rec["section_messages"][sec_name].append(
                {"role": "assistant", "content": full_response}
            )
            record_subscriber_lesson_memory(
                rec, sec_name, rec["section_messages"][sec_name]
            )
            save_account_everywhere(rec["user_email"], rec)
            update_auto_memory(rec, rec["section_messages"][sec_name])
            st.session_state.latest_voice_text = full_response
            st.rerun()

      is_bras_live_section = sec_name == "BRAS LIVE" or "BRAS LIVE" in sec_name
      if is_bras_live_section and browsing_item is None:
        st.markdown("""
        <style>
        .bras-character-card {
          position:relative; overflow:hidden; border:1px solid rgba(190,170,255,.42);
          border-radius:26px; padding:22px 16px; text-align:center;
          background:radial-gradient(ellipse at 50% 0%,rgba(170,135,255,.28),transparent 62%),linear-gradient(145deg,rgba(35,25,68,.96),rgba(14,35,60,.96));
          box-shadow:0 18px 42px rgba(18,12,48,.30),inset 0 1px rgba(255,255,255,.12); min-height:245px;
          transform:perspective(900px) rotateX(1deg); transition:transform .25s,box-shadow .25s;
        }
        .bras-character-card:hover { transform:perspective(900px) rotateX(0) translateY(-4px); box-shadow:0 24px 50px rgba(80,55,150,.30); }
        .bras-avatar {
          position:relative; width:142px; height:142px; margin:0 auto 15px; border-radius:50%;
          display:flex; align-items:center; justify-content:center; overflow:hidden;
          background:radial-gradient(circle at 32% 22%,#fff 0%,#f2ddff 12%,#bd9bff 35%,#7052bd 67%,#30204f 100%);
          border:3px solid rgba(255,255,255,.84); box-shadow:0 0 0 7px rgba(177,145,255,.10),0 0 36px rgba(167,139,250,.52),inset 0 -10px 24px rgba(28,14,62,.32);
          animation:brasFloat 4s ease-in-out infinite;
        }
        .bras-avatar:before { content:'';position:absolute;inset:8px;border:1px solid rgba(255,255,255,.25);border-radius:50%;pointer-events:none; }
        .bras-avatar.boy { background:radial-gradient(circle at 32% 22%,#fff 0%,#d8f6ff 12%,#82d8ff 35%,#397bb4 67%,#172b57 100%);box-shadow:0 0 0 7px rgba(110,200,255,.10),0 0 36px rgba(83,185,255,.48),inset 0 -10px 24px rgba(10,30,60,.32); }
        .bras-avatar svg { width:100%; height:100%; filter:drop-shadow(0 9px 9px rgba(0,0,0,.32)); }
        @keyframes brasFloat { 0%,100%{transform:translateY(0) rotateY(-4deg)} 50%{transform:translateY(-7px) rotateY(4deg)} }
        .bras-character-card h3 { margin: 4px 0 6px; }
        .bras-character-card p { opacity: .88; margin: 0; font-size: .93rem; }
        </style>
        <h2>🎙️ BRAS LIVE</h2>
        <p>اختَر الشخصية التي تريد التحدث معها.</p>
        """, unsafe_allow_html=True)
        girl_col, boy_col = st.columns(2)
        with girl_col:
          st.markdown("""
          <div class="bras-character-card">
            <div class="bras-avatar">
              <svg viewBox="0 0 160 160" role="img" aria-label="BRAS GIRL original 3D style avatar">
                <defs>
                  <linearGradient id="gHair" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#67405f"/><stop offset=".48" stop-color="#291c39"/><stop offset="1" stop-color="#100f27"/></linearGradient>
                  <radialGradient id="gSkin" cx="35%" cy="25%"><stop stop-color="#ffe9d8"/><stop offset=".68" stop-color="#edbda7"/><stop offset="1" stop-color="#b87578"/></radialGradient>
                  <linearGradient id="gCoat" x2="1" y2="1"><stop stop-color="#c6a7ff"/><stop offset="1" stop-color="#5542a1"/></linearGradient>
                </defs>
                <ellipse cx="80" cy="151" rx="48" ry="10" fill="#160d35" opacity=".35"/>
                <path d="M25 151Q26 112 54 105L80 119 106 105Q135 114 137 151Z" fill="url(#gCoat)"/>
                <path d="M47 111L80 143 113 111 103 103H57Z" fill="#fff0fa"/>
                <path d="M34 76Q17 16 75 9Q133 8 127 81L119 126Q106 143 95 117L103 58Q78 31 51 61L57 122Q45 144 33 117Z" fill="url(#gHair)"/>
                <ellipse cx="80" cy="69" rx="35" ry="43" fill="url(#gSkin)"/>
                <path d="M45 57Q43 13 83 15Q123 14 116 61Q99 40 81 40Q59 39 45 57Z" fill="url(#gHair)"/>
                <path d="M48 62Q39 88 49 111Q30 106 29 80Q28 51 45 39Z" fill="#382440"/><path d="M111 55Q128 79 112 113Q132 107 134 78Q132 49 117 37Z" fill="#21172f"/>
                <path d="M57 66Q66 59 73 66M88 66Q96 59 104 66" stroke="#573747" stroke-width="4" fill="none" stroke-linecap="round"/>
                <ellipse cx="66" cy="73" rx="4.2" ry="5.5" fill="#34263b"/><ellipse cx="95" cy="73" rx="4.2" ry="5.5" fill="#34263b"/>
                <circle cx="67.5" cy="71" r="1.5" fill="white"/><circle cx="96.5" cy="71" r="1.5" fill="white"/>
                <ellipse cx="53" cy="85" rx="7" ry="4" fill="#e98e9c" opacity=".35"/><ellipse cx="107" cy="85" rx="7" ry="4" fill="#e98e9c" opacity=".35"/>
                <path d="M72 94Q80 101 89 94" stroke="#a64f68" stroke-width="3" fill="none" stroke-linecap="round"/>
                <path d="M79 82L76 88 81 89" stroke="#c4867d" stroke-width="2" fill="none" stroke-linecap="round"/>
                <path d="M53 39Q65 18 89 26" stroke="#d7a7cb" stroke-width="3" opacity=".55" fill="none" stroke-linecap="round"/>
              </svg>
            </div>
            <h3>👩 BRAS GIRL</h3>
            <p>صوت أنثوي طبيعي · هادئة وذكية · لطيفة وعفوية</p>
            <p>تفهم سياق الحديث وتتفاعل بشكل طبيعي</p>
          </div>
          """, unsafe_allow_html=True)
        with boy_col:
          st.markdown("""
          <div class="bras-character-card">
            <div class="bras-avatar boy">
              <svg viewBox="0 0 160 160" role="img" aria-label="BRAS BOY original 3D style avatar">
                <defs>
                  <linearGradient id="bHair" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#72513d"/><stop offset=".5" stop-color="#302a35"/><stop offset="1" stop-color="#111b31"/></linearGradient>
                  <radialGradient id="bSkin" cx="35%" cy="25%"><stop stop-color="#ffe5c9"/><stop offset=".7" stop-color="#dfad8d"/><stop offset="1" stop-color="#a86d67"/></radialGradient>
                  <linearGradient id="bCoat" x2="1" y2="1"><stop stop-color="#8bdcff"/><stop offset="1" stop-color="#315e9b"/></linearGradient>
                </defs>
                <ellipse cx="80" cy="151" rx="48" ry="10" fill="#07162e" opacity=".35"/>
                <path d="M23 151Q26 112 54 105L80 119 106 105Q134 113 137 151Z" fill="url(#bCoat)"/>
                <path d="M53 108L80 142 107 108 98 103H62Z" fill="#effaff"/>
                <path d="M42 66Q31 16 80 12Q129 13 119 74L111 104Q101 120 94 103L102 55Q80 34 56 55L64 105Q52 122 42 101Z" fill="url(#bHair)"/>
                <ellipse cx="80" cy="69" rx="35" ry="43" fill="url(#bSkin)"/>
                <path d="M45 57Q39 19 75 15Q112 8 119 48L110 57Q94 38 76 40Q58 39 45 61Z" fill="url(#bHair)"/>
                <path d="M55 65Q65 59 73 65M88 65Q97 59 105 65" stroke="#44323a" stroke-width="4" fill="none" stroke-linecap="round"/>
                <ellipse cx="66" cy="73" rx="4.2" ry="5.5" fill="#26303a"/><ellipse cx="95" cy="73" rx="4.2" ry="5.5" fill="#26303a"/>
                <circle cx="67.5" cy="71" r="1.5" fill="white"/><circle cx="96.5" cy="71" r="1.5" fill="white"/>
                <path d="M80 78L76 89 82 90" stroke="#b77b69" stroke-width="2" fill="none" stroke-linecap="round"/>
                <path d="M71 96Q80 101 90 96" stroke="#995665" stroke-width="3" fill="none" stroke-linecap="round"/>
                <path d="M51 39Q65 19 91 26" stroke="#c5a38d" stroke-width="3" opacity=".55" fill="none" stroke-linecap="round"/>
              </svg>
            </div>
            <h3>👨 BRAS BOY</h3>
            <p>صوت رجالي طبيعي · ذكي وسريع · خفيف بالحوار</p>
            <p>يرد بوضوح وبأسلوب عفوي</p>
          </div>
          """, unsafe_allow_html=True)
        character = st.radio(
            "اختيار الشخصية:",
            ["BRAS GIRL", "BRAS BOY"],
            horizontal=True,
            key="bras_live_character",
        )
        st.success(f"تم اختيار {character} — جاهز للمحادثة بالصوت والصورة.")
        st.markdown("### 📞 مكالمة BRAS LIVE المباشرة")
        st.caption("مكالمة صوتية مباشرة، وشخصية تتفاعل مع صوتها، وكاميرا أمامية/خلفية بمعاينة مباشرة على جهازك.")
        start_live = st.button("▶️ بدء المكالمة المباشرة", key="bras_live_start_call", type="primary")
        if start_live:
          with st.spinner("جارٍ تجهيز اتصال آمن مع OpenAI..."):
            live_secret, live_error = create_bras_realtime_secret(character)
          if live_error:
            st.error(live_error)
          else:
            st.session_state["bras_live_ephemeral_secret"] = live_secret
            st.session_state["bras_live_active_character"] = character

        if st.session_state.get("bras_live_ephemeral_secret"):
          if st.session_state.get("bras_live_active_character") != character:
            st.session_state.pop("bras_live_ephemeral_secret", None)
            st.warning("غيّرت الشخصية. اضغط بدء المكالمة مرة أخرى.")
          else:
            ephemeral = st.session_state["bras_live_ephemeral_secret"]
            live_html = r"""
            <div id="bras-live" style="font-family:system-ui;color:#f7f4ff;background:radial-gradient(circle at 50% 0%,#4a3478 0%,#20183e 48%,#101d35 100%);padding:20px;border:1px solid #7560a8;border-radius:26px;box-shadow:0 18px 48px #120b2c55">
              <div style="text-align:center;padding:5px 0 14px">
                <div style="font-size:25px;font-weight:800;letter-spacing:1px">✦ BRAS LIVE ✦</div>
                <div id="status" style="opacity:.9;margin-top:7px">جاهز للاتصال</div>
              </div>
              <div style="display:flex;gap:16px;align-items:center;justify-content:center;flex-wrap:wrap">
                <div id="live-avatar" class="live-avatar girl"><div class="live-orbit"></div><div class="live-face"><span class="live-hair"></span><span class="live-eyes">●　●</span><span class="live-mouth"></span></div><div class="live-name">BRAS GIRL</div></div>
                <div class="live-camera-wrap"><video id="cam" autoplay playsinline muted></video><div id="camera-placeholder">📷<br>الكاميرا متوقفة</div></div>
              </div>
              <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:14px">
                <button id="mic">🔇 كتم المايك</button>
                <button id="camera">📷 تشغيل الكاميرا الأمامية</button>
                <button id="switch-camera" disabled>🔄 تبديل أمامية / خلفية</button>
                <button id="mirror" disabled>🪞 عكس المرآة: إيقاف</button>
                <button id="hangup" style="background:#a83252;color:white">إنهاء المكالمة</button>
              </div>
              <div id="transcript" aria-live="polite" style="margin-top:14px;min-height:55px;max-height:150px;overflow:auto;white-space:pre-wrap;background:#ffffff12;padding:12px;border-radius:14px"></div>
            </div>
            <style>
              #bras-live button{border:0;border-radius:14px;padding:11px 15px;background:linear-gradient(135deg,#9d80ff,#6c55d9);color:white;font-weight:700;cursor:pointer;box-shadow:0 5px 15px #08051b55}
              #bras-live button:disabled{opacity:.5;cursor:not-allowed}
              #bras-live .live-avatar{width:176px;height:176px;position:relative;border-radius:50%;display:grid;place-items:center;overflow:visible;background:radial-gradient(circle at 35% 25%,#fff,#dfcaff 15%,#9977ef 48%,#34205f 82%);border:4px solid #fff9;box-shadow:0 0 0 9px #bba1ff20,0 0 40px #a78bfa99;animation:liveFloat 4s ease-in-out infinite}
              #bras-live .live-avatar.boy{background:radial-gradient(circle at 35% 25%,#fff,#c8f2ff 15%,#64bde8 48%,#183e70 82%);box-shadow:0 0 0 9px #86d9ff20,0 0 40px #66caff88}
              #bras-live .live-avatar.speaking{animation:liveTalk .32s ease-in-out infinite alternate;box-shadow:0 0 0 12px #d9c6ff33,0 0 52px #c6a5ffcc}
              @keyframes liveTalk{from{transform:translateY(-2px) scale(1)}to{transform:translateY(-4px) scale(1.025)}}
              #bras-live .live-face{position:relative;width:112px;height:118px;border-radius:48% 48% 45% 45%;background:radial-gradient(circle at 35% 22%,#ffe8d7,#e6b49e 65%,#ad7377);box-shadow:inset -10px -12px 20px #5b315744,0 12px 18px #160d3566;border:4px solid #fff9}
              #bras-live .live-hair{position:absolute;left:-5px;top:-9px;width:114px;height:53px;border-radius:55% 55% 28% 25%;background:linear-gradient(145deg,#67405f,#21162f 70%);box-shadow:inset 8px 5px 9px #ffffff22}
              #bras-live .live-eyes{position:absolute;top:58px;left:23px;color:#352536;font-size:17px;letter-spacing:3px;text-shadow:0 1px #fff8}
              #bras-live .live-mouth{position:absolute;left:47px;top:91px;width:19px;height:8px;border-bottom:3px solid #a34f65;border-radius:50%}
              #bras-live .live-avatar.boy .live-face{background:radial-gradient(circle at 35% 22%,#ffe7cf,#dcae8e 65%,#9c6967)}
              #bras-live .live-avatar.boy .live-hair{background:linear-gradient(145deg,#72513d,#17243a 75%);height:45px}
              #bras-live .live-orbit{position:absolute;inset:-10px;border:1px solid #ffffff77;border-radius:50%;transform:rotateX(67deg);box-shadow:0 0 18px #d8c3ff88}
              #bras-live .live-name{position:absolute;bottom:-29px;font-size:12px;letter-spacing:1.4px;font-weight:800;color:#fff;text-shadow:0 2px 8px #000}
              #bras-live .live-camera-wrap{position:relative;width:min(100%,280px);height:190px;border-radius:18px;overflow:hidden;background:#080d19;border:2px solid #ffffff66;box-shadow:0 8px 24px #08051b66}
              #bras-live #cam{display:none;width:100%;height:100%;object-fit:cover;transform:none}
              #bras-live #camera-placeholder{position:absolute;inset:0;display:grid;place-content:center;text-align:center;color:#d7d1ed;opacity:.85}
              @keyframes liveFloat{0%,100%{transform:translateY(0) rotateY(-5deg)}50%{transform:translateY(-8px) rotateY(5deg)}}
            </style>
            <script>
            (() => {
              const token = "__EPHEMERAL__";
              const model = "gpt-realtime-2.1";
              const status = document.getElementById("status");
              const avatar = document.getElementById("live-avatar");
              const selectedCharacter = "__CHARACTER__";
              if(selectedCharacter === "BRAS BOY") { avatar.classList.remove("girl"); avatar.classList.add("boy"); avatar.querySelector(".live-name").textContent="BRAS BOY"; }
              const transcript = document.getElementById("transcript");
              const video = document.getElementById("cam");
              let pc, dc, micStream, camStream, cameraFacing="user", mirrorPreview=false, closed=false;
              const say = t => status.textContent=t;
              const log = t => { transcript.textContent += t + "\\n"; transcript.scrollTop=transcript.scrollHeight; };
              async function connect(){
                try {
                  say("جارٍ الاتصال...");
                  pc = new RTCPeerConnection();
                  pc.ontrack = e => {
                    let audio = document.getElementById("remote-audio");
                    if(!audio){audio=document.createElement("audio");audio.id="remote-audio";audio.autoplay=true;document.body.appendChild(audio);}
                    audio.srcObject=e.streams[0];
                    audio.onplaying=()=>avatar.classList.add("speaking");
                    audio.onpause=()=>avatar.classList.remove("speaking");
                    audio.onended=()=>avatar.classList.remove("speaking");
                  };
                  dc = pc.createDataChannel("oai-events");
                  dc.onopen = () => {
                    document.getElementById("mic").textContent = "🔇 كتم المايك";
                  };
                  dc.onmessage = ev => {
                    try {
                      const d=JSON.parse(ev.data);
                      if(d.type==="response.output_audio_transcript.done" && d.transcript) log("BRAS: "+d.transcript);
                      if(d.type==="conversation.item.input_audio_transcription.completed" && d.transcript) log("أنت: "+d.transcript);
                      if(d.type==="error") {
                        const message = d.error?.message || "تعذر تنفيذ الطلب";
                        log("خطأ: "+message);
                        say("حدث خطأ في الاتصال");
                      }
                    } catch(_){}
                  };
                  micStream = await navigator.mediaDevices.getUserMedia({audio:true});
                  micStream.getTracks().forEach(t=>pc.addTrack(t,micStream));
                  const offer=await pc.createOffer();
                  await pc.setLocalDescription(offer);
                  const response=await fetch("https://api.openai.com/v1/realtime/calls?model="+model,{
                    method:"POST",
                    body:offer.sdp,
                    headers:{"Authorization":"Bearer "+token,"Content-Type":"application/sdp"}
                  });
                  if(!response.ok) throw new Error(await response.text());
                  await pc.setRemoteDescription({type:"answer",sdp:await response.text()});
                  say("🟢 متصل — تحدث الآن. إذا تكلمت أثناء الرد، يفترض أن يتوقف ويستمع إليك.");
                } catch(e){say("تعذر الاتصال: "+e.message); log("تحقق من المفتاح والرصيد والسماح بالمايك.");}
              }
              document.getElementById("mic").onclick=async()=>{
                if(!pc){await connect();return;}
                const track=micStream?.getAudioTracks()[0];
                if(track){track.enabled=!track.enabled;document.getElementById("mic").textContent=track.enabled?"🔇 كتم المايك":"🎙️ تشغيل المايك";}
              };
              async function openCamera(facing){
                if(camStream) camStream.getTracks().forEach(t=>t.stop());
                camStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:facing},width:{ideal:1280},height:{ideal:720}},audio:false});
                cameraFacing=facing;
                video.srcObject=camStream;
                video.style.display="block";
                video.style.transform=mirrorPreview && facing==="user" ? "scaleX(-1)" : "none";
                document.getElementById("camera-placeholder").style.display="none";
                document.getElementById("camera").textContent="⏸ إيقاف الكاميرا";
                document.getElementById("switch-camera").disabled=false;
                document.getElementById("mirror").disabled=false;
                say(facing==="user" ? "📷 الكاميرا الأمامية تعمل مباشرة على جهازك." : "📷 الكاميرا الخلفية تعمل مباشرة على جهازك.");
              }
              document.getElementById("camera").onclick=async()=>{
                try{
                  if(!camStream){await openCamera("user");}
                  else{
                    camStream.getTracks().forEach(t=>t.stop());camStream=null;video.srcObject=null;video.style.display="none";
                    document.getElementById("camera-placeholder").style.display="grid";
                    document.getElementById("camera").textContent="📷 تشغيل الكاميرا الأمامية";
                    document.getElementById("switch-camera").disabled=true;document.getElementById("mirror").disabled=true;
                    say("تم إيقاف الكاميرا.");
                  }
                }catch(e){say("تعذر فتح الكاميرا: "+e.message);}
              };
              document.getElementById("switch-camera").onclick=async()=>{
                if(!camStream)return;
                try{await openCamera(cameraFacing==="user"?"environment":"user");}
                catch(e){say("لم تتوفر الكاميرا الأخرى على هذا الجهاز: "+e.message);}
              };
              document.getElementById("mirror").onclick=()=>{
                mirrorPreview=!mirrorPreview;
                video.style.transform=mirrorPreview && cameraFacing==="user" ? "scaleX(-1)" : "none";
                document.getElementById("mirror").textContent=mirrorPreview?"🪞 عكس المرآة: تشغيل":"🪞 عكس المرآة: إيقاف";
              };
              document.getElementById("hangup").onclick=()=>{
                closed=true;pc?.close();micStream?.getTracks().forEach(t=>t.stop());camStream?.getTracks().forEach(t=>t.stop());
                video.style.display="none";say("انتهت المكالمة. أعد تحميل القسم لبدء مكالمة جديدة.");
                document.querySelectorAll("#bras-live button").forEach(b=>b.disabled=true);
              };
              connect();
            })();
            </script>
            """.replace("__EPHEMERAL__", ephemeral)
            live_html = live_html.replace("__CHARACTER__", character)
            components.html(live_html, height=570, scrolling=False)
            if st.button("🧹 إغلاق وإلغاء رمز المكالمة", key="bras_live_clear_secret"):
              st.session_state.pop("bras_live_ephemeral_secret", None)
              st.rerun()
        st.info(
            "تحتاج المكالمة إلى مفتاح API ورصيد فعال. لا تضع المفتاح الدائم داخل المتصفح؛ "
            "التطبيق ينشئ رمزاً مؤقتاً قصير الصلاحية. الكاميرا هنا بث معاينة مباشر على جهازك فقط، ولا تُرسل صوراً أو فيديو إلى نموذج OpenAI. "
            "واجهة Realtime API الحالية تقبل صوراً مرفقة بالمحادثة، لكنها لا توفر إدخال فيديو حيّاً أصلياً مستمراً؛ لذلك لن أدّعي أن BRAS يرى حركتك مباشرة. اسمح للمتصفح باستخدام المايك والكاميرا، "
            "وافتح التطبيق عبر HTTPS أو localhost."
        )
        st.markdown("---")

      is_ads_section = sec_name == SECTIONS_NAMES.get(
          "Ads & Stores Studio", "Ads & Stores Studio"
      ) or any(
          w in sec_name for w in ["إعلانات", "Ads", "ریکلام", "ریكلام"]
      )
      if is_ads_section and browsing_item is None:
        st.markdown("### 📢 مولد إعلانات المتاجر والمشاريع")
        ad_store = st.text_input(
            "اسم المتجر أو النشاط التجاري", key="ad_store_name"
        )
        ad_offer = st.text_area(
            "تفاصيل المنتج أو العرض أو الخدمة", key="ad_offer_desc"
        )
        ad_channel = st.selectbox(
            "منصة الإعلان",
            ["Instagram", "TikTok", "Facebook", "Snapchat"],
            key="ad_channel_box",
        )
        if st.button(
            "توليد نص الإعلان الآن", type="primary", key="gen_ad_btn"
        ):
          if not can_send_message_in_section(rec, sec_name):
            st.warning(
                "🔒 انتهى حد الـ 75 رسالة يومياً لغير المشتركين."
                " اشتركي للمتابعة."
            )
          elif ad_store.strip() and ad_offer.strip():
            record_message_in_section(rec, sec_name)
            ad_out = get_ai_answer(
                rec,
                (
                    f"{system_prompt} Create a persuasive ad for {ad_channel}"
                    f" for store '{ad_store}' offering: {ad_offer}."
                ),
                [{
                    "role": "user",
                    "content": f"Store: {ad_store}\nOffer: {ad_offer}",
                }],
                sec_name=sec_name,
            )
            rec["section_messages"].setdefault(sec_name, []).append(
                {"role": "assistant", "content": ad_out}
            )
            record_subscriber_lesson_memory(
                rec, sec_name, rec["section_messages"][sec_name]
            )
            save_account_everywhere(rec["user_email"], rec)
            st.session_state.latest_voice_text = ad_out
            st.rerun()
          else:
            st.info("اكتبي اسم المتجر ووصف العرض أولاً.")
        st.markdown("---")

      is_gen_section = sec_name == SECTIONS_NAMES.get(
          "AI Generation Studio", "AI Generation Studio"
      )
      if is_gen_section and browsing_item is None:
        st.markdown(f"### 🎨 {t_ai_gen_studio}")
        if not rec.get("is_subscribed"):
          remaining_images = max(0, FREE_DAILY_IMAGE_LIMIT - rec.get("free_daily_images_used", 0))
          st.caption(f"المتبقي من الصور اليوم: {remaining_images}/{FREE_DAILY_IMAGE_LIMIT}")

        media_prompt = st.text_area(
            "اكتبي وصف الصورة بالتفصيل:", key="media_gen_prompt",
            placeholder="مثلاً: منظر طبيعي وقت الغروب، ألوان بنفسجية، أسلوب واقعي...",
        )
        if st.button(f"{t_gen_btn}", type="primary", key="gen_real_media_btn"):
          if not media_prompt.strip():
            st.info("اكتبي وصفاً أولاً.")
          elif not can_upload_free_media(rec, is_video=False):
            st.warning("🔒 وصلتِ للحد اليومي للصور لغير المشتركين (صورتين/يوم).")
          else:
            with st.spinner("جاري رسم الصورة باستخدام OpenAI..."):
              img_out, err = generate_real_image(media_prompt.strip())
            if img_out:
              img_bytes = image_bytes_from_result(img_out)
              if img_bytes:
                record_free_media_upload(rec, is_video=False)
                saved_item = save_image_to_library(rec, img_bytes, media_prompt.strip(), "generated")
                if saved_item:
                  rec["last_generated_image_id"] = saved_item["id"]
                  save_account_everywhere(rec["user_email"], rec)
                st.success("💜 انحفظت نسخة تلقائياً في مكتبتك! تظهر الصورة أدناه ويمكنك تعديلها أو حفظها أو مشاركتها.")
              else:
                st.error("تعذر تجهيز الصورة للتنزيل والحفظ. جربي مرة ثانية.")
            else:
              st.error(f"تعذر إنشاء الصورة: {err}")
        # Persist last created image across reruns and allow free-form corrections.
        last_gen_id = rec.get("last_generated_image_id")
        last_gen_item = next((it for it in rec.get("image_library", []) if it.get("id") == last_gen_id), None)
        if last_gen_item and last_gen_item.get("image_b64"):
          try:
            last_gen_bytes = base64.b64decode(last_gen_item["image_b64"])
            st.subheader("مراجعة آخر صورة")
            st.image(last_gen_bytes, caption=last_gen_item.get("prompt", "آخر صورة"), use_container_width=True)
            st.info("الصورة محفوظة بمكتبتك. إذا عجبتك اتركيها كما هي، أو اكتبي أي تعديل تريدينه.")
            correction_text = st.text_area("هل يوجد خطأ بالصورة أو تعديل تريدينه؟", key="image_correction_prompt", placeholder="مثلاً: عدّل لون الخلفية، غيّر تعبير الوجه، أو أضف تفاصيل...")
            if st.button("🛠️ تعديل آخر صورة حسب كلامي", key="apply_last_image_correction", disabled=not correction_text.strip()):
              with st.spinner("جاري تعديل الصورة حسب طلبك..."):
                corrected, corr_err = edit_user_image(last_gen_bytes, "image/jpeg", "", correction_text.strip())
              if corrected:
                corrected_bytes = image_bytes_from_result(corrected)
                if corrected_bytes:
                  new_saved = save_image_to_library(rec, corrected_bytes, correction_text.strip(), "edited")
                  if new_saved:
                    rec["last_generated_image_id"] = new_saved["id"]
                    save_account_everywhere(rec["user_email"], rec)
                  st.success("تم التعديل وحفظ النسخة الجديدة في المكتبة!")
                  st.image(corrected_bytes, caption="النسخة المعدّلة", use_container_width=True)
                  render_image_actions(corrected_bytes, "bras_ai_corrected_image.png", f"corrected_{new_saved['id'] if new_saved else 'img'}")
                  st.rerun()
                else:
                  st.error("تعذر تجهيز الصورة المعدّلة.")
              else:
                st.error(f"تعذر تعديل الصورة: {corr_err}")
          except Exception:
            st.warning("تعذر عرض الصورة الأخيرة المخزنة.")
        st.markdown("---")

      is_edit_section = sec_name == SECTIONS_NAMES.get(
          "Image Editor", "Image Editor"
      )
      if is_edit_section and browsing_item is None:
        st.markdown(f"### 🛠️ {t_img_edit_studio}")
        st.caption(
            "المتبقي من الصور للتعديل اليوم:"
            f" {max(0, FREE_DAILY_IMAGE_LIMIT - rec.get('free_daily_images_used', 0))}/{FREE_DAILY_IMAGE_LIMIT}"
        )

        upload_edit_img = st.file_uploader(
            f"{t_upload_img_q}",
            type=["png", "jpg", "jpeg", "webp"],
            key="edit_up",
        )
        edit_effect = st.selectbox(
            f"{t_img_effect_q}",
            [
                "📝 تعديل حسب وصفك فقط",
                "🖼️ تحويل لصورة كرتونية (Style Transfer)",
                "🔍 تحسين الجودة ودقة الصورة (Super Resolution)",
                "🧙‍♂️ تأثير سحري آخر (مثلاً: إضاءة سينمائية)",
            ],
            key="edit_eff_sel",
        )
        custom_edit_prompt = st.text_area("اكتبي التعديل الذي تريدينه بنفسك:", key="custom_image_edit_prompt", placeholder="اكتبي بحرية: غير الخلفية، أزل شيء، أضف عنصر، غيّر الألوان...")

        if upload_edit_img and edit_effect:
          raw_e = upload_edit_img.getvalue()
          ext_e = upload_edit_img.name.rsplit(".", 1)[-1].lower()
          mime_e = (
              "image/jpeg" if ext_e in ["jpg", "jpeg"] else f"image/{ext_e}"
          )
          st.image(raw_e, caption="الصورة الأصلية", use_container_width=True)

          if st.button(
              f"{t_edit_img_btn}", type="primary", key="run_edit_btn"
          ):
            if not can_upload_free_media(rec, is_video=False):
              st.warning(
                  "🔒 وصلتِ للحد اليومي للصور لغير المشتركين (صورتين/يوم)."
              )
            else:
              with st.spinner("جاري معالجة الصورة..."):
                edited_url, err_e = edit_user_image(raw_e, mime_e, edit_effect, custom_edit_prompt)
              if edited_url:
                edited_bytes = image_bytes_from_result(edited_url)
                if edited_bytes:
                  record_free_media_upload(rec, is_video=False)
                  saved_edit = save_image_to_library(rec, edited_bytes, custom_edit_prompt.strip() or edit_effect, "edited")
                  st.success("✅ تم تعديل الصورة وحفظ نسخة تلقائياً في مكتبتك!")
                  st.image(edited_bytes, caption=f"نتيجة التعديل: {custom_edit_prompt.strip() or edit_effect}", use_container_width=True)
                  render_image_actions(edited_bytes, "bras_ai_edited_image.png", f"edited_{saved_edit['id'] if saved_edit else 'img'}")
                else:
                  st.error("تعذر تجهيز الصورة للحفظ. جربي مرة أخرى.")
              else:
                st.error(f"تعذر تعديل الصورة: {err_e}")

      if browsing_item is not None:
        active_messages = browsing_item.get("messages", [])
      else:
        rec["section_messages"].setdefault(sec_name, [])
        active_messages = rec["section_messages"][sec_name]

      for msg_index, message in enumerate(active_messages):
        with st.chat_message(message["role"]):
          render_chat_message(message)
          if browsing_item is None and message.get("role") == "assistant":
            render_message_actions(rec, sec_name, message, msg_index, system_prompt)

      if browsing_item is None:
        user_spoken_text = None
        audio_val = st.audio_input(
            "🎙️ تحدثِ هنا للرد الفوري:", key=f"mic_sec_{sec_name}"
        )
        user_spoken_text = transcribe_once(audio_val, f"sec_{sec_name}")

        typed_prompt = st.chat_input("اكتبي رسالتكِ هنا...")
        final_prompt = user_spoken_text if user_spoken_text else typed_prompt
        requested_file_format = detect_requested_file_format(final_prompt or "")

        if final_prompt:
          if not can_send_message_in_section(rec, sec_name):
            st.warning(
                "🔒 وصلتِ للحد الأقصى (75 رسالة يومياً) لغير"
                " المشتركين. اختاري باقة اشتراك للمتابعة."
            )
          else:
            record_message_in_section(rec, sec_name)
            if st.session_state.pending_image_b64:
              user_payload = [
                  {"type": "text", "text": final_prompt},
                  {
                      "type": "image_url",
                      "image_url": {
                          "url": (
                              f"data:{st.session_state.pending_image_mime};base64,{st.session_state.pending_image_b64}"
                          )
                      },
                  },
              ]
              st.session_state.pending_image_b64 = None
              st.session_state.pending_image_mime = None
              st.session_state.pending_image_name = None
            else:
              user_payload = final_prompt

            rec["section_messages"][sec_name].append(
                {"role": "user", "content": user_payload}
            )
            with st.chat_message("user"):
              render_chat_message({"role": "user", "content": user_payload})

            with st.chat_message("assistant"):
              full_response = get_ai_answer(
                  rec,
                  system_prompt,
                  rec["section_messages"][sec_name],
                  sec_name=sec_name,
              )
              if sec_name == "BRAS LIVE":
                live_voice = (
                    "صوت رجل (Onyx)" if st.session_state.get("bras_live_character", "BRAS GIRL") == "BRAS BOY"
                    else "صوت بنت (Nova)"
                )
                play_voice_only(full_response, live_voice)
                st.markdown(full_response)
              else:
                reply_with_voice(full_response, rec["voice"])
              assistant_message = {"role": "assistant", "content": full_response}
              if requested_file_format:
                assistant_message["attachment"] = make_requested_attachment(full_response, requested_file_format, prompt_text=final_prompt)
              rec["section_messages"][sec_name].append(assistant_message)
              # Render controls in the same run as the freshly generated reply.
              render_message_actions(
                  rec, sec_name, rec["section_messages"][sec_name][-1],
                  len(rec["section_messages"][sec_name]) - 1,
                  system_prompt,
              )
              if requested_file_format:
                render_attachment_download(rec["section_messages"][sec_name][-1])
              record_subscriber_lesson_memory(
                  rec,
                  sec_name,
                  rec["section_messages"][sec_name],
              )
              save_account_everywhere(rec["user_email"], rec)
              update_auto_memory(rec, rec["section_messages"][sec_name])

  elif nav_mode == t_sec_schedule:
    st.header(t_schedule_title)
    if not rec.get("is_subscribed"):
      st.info(
          "🔒 لغير المشتركين: يُسمح بمهمة واحدة في اليوم (**1/يوم**) و3 مهام"
          " في الأسبوع (**3/أسبوع**)."
      )
    with st.form("sch_form"):
      task_desc = st.text_input(t_task_input)
      col_d, col_t = st.columns(2)
      with col_d:
        task_day = st.selectbox(
            t_day_label,
            [
                "السبت",
                "الأحد",
                "الإثنين",
                "الثلاثاء",
                "الأربعاء",
                "الخميس",
                "الجمعة",
            ],
        )
      with col_t:
        task_time = st.text_input(t_time_label, value="12:00")

      if st.form_submit_button(t_add_task_btn) and task_desc.strip():
        if not rec.get("is_subscribed"):
          if len(rec.get("my_schedule", [])) >= FREE_WEEKLY_TASK_LIMIT:
            st.warning(
                "🔒 وصلتِ للحد الأسبوعي (3 مهام في الأسبوع) لغير المشتركين."
            )
          elif count_free_tasks_on_day(rec, task_day) >= FREE_DAILY_TASK_LIMIT:
            st.warning(
                f"🔒 يُسمح بمهمة واحدة فقط في يوم {task_day} لغير المشتركين."
            )
          else:
            rec["my_schedule"].append({
                "day": task_day,
                "time": task_time.strip() or "12:00",
                "task": task_desc.strip(),
            })
            save_account_everywhere(rec["user_email"], rec)
            st.success(t_task_added)
        else:
          rec["my_schedule"].append({
              "day": task_day,
              "time": task_time.strip() or "12:00",
              "task": task_desc.strip(),
          })
          save_account_everywhere(rec["user_email"], rec)
          st.success(t_task_added)

    if rec.get("my_schedule"):
      st.subheader(t_schedule_list)
      for idx, item in enumerate(rec["my_schedule"]):
        c_txt, c_del = st.columns([5, 1])
        with c_txt:
          st.info(
              f"⏰ **تذكير:** {item['day']} الساعة **{item['time']}** —"
              f" {item['task']}"
          )
        with c_del:
          if st.button("حذف", key=f"del_sch_{idx}"):
            rec["my_schedule"].pop(idx)
            save_account_everywhere(rec["user_email"], rec)
            st.rerun()
    else:
      st.info("لا توجد مواعيد مضافة في جدولكِ حالياً.")

  elif nav_mode == t_sec_chats:
    st.header("💬 سجل الدردشة الكاملة")
    saved_chats = rec.get("saved_chats", [])
    chat_folders = rec.setdefault("chat_folders", ["عام"])
    if "عام" not in chat_folders:
      chat_folders.insert(0, "عام")
    folder_col1, folder_col2 = st.columns([3, 1])
    with folder_col1:
      new_folder_name = st.text_input("📁 إنشاء مجلد جديد", placeholder="اسم المجلد", key="bras_new_chat_folder")
    with folder_col2:
      if st.button("➕ إضافة مجلد", key="bras_add_chat_folder"):
        cleaned_folder = new_folder_name.strip()
        if cleaned_folder and cleaned_folder not in chat_folders:
          chat_folders.append(cleaned_folder)
          save_account_everywhere(rec["user_email"], rec)
          st.success("تم إنشاء المجلد")
          st.rerun()
        elif cleaned_folder in chat_folders:
          st.warning("هذا المجلد موجود مسبقاً")
    folder_filter = st.selectbox("عرض المجلد", ["كل المجلدات"] + chat_folders, key="bras_chat_folder_filter")
    search_term = st.text_input(
        "🔎 ابحث داخل الدردشات المحفوظة",
        placeholder="اكتب كلمة أو عبارة من محادثة قديمة...",
        key="bras_saved_chat_search",
    ).strip()

    def normalize_chat_search_text(value):
      text_value = str(value or "").lower()
      text_value = re.sub(r"[\u064B-\u065F\u0670]", "", text_value)
      text_value = text_value.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
      text_value = text_value.replace("ى", "ي").replace("ة", "ه")
      return re.sub(r"\s+", " ", text_value).strip()

    def get_chat_search_content(chat_item):
      chunks = [str(chat_item.get("title", ""))]
      for msg in chat_item.get("messages", []):
        content = msg.get("content", "")
        if isinstance(content, str):
          chunks.append(content)
        elif isinstance(content, list):
          for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
              chunks.append(str(part.get("text", "")))
      return "\n".join(chunks)

    if not saved_chats:
      st.info(
          "لم يتم حفظ أي دردشة كاملة بعد. اضغطي على «حفظ في سجل الدردشة» داخل"
          " أي قسم لحفظها هنا."
      )
    else:
      query_norm = normalize_chat_search_text(search_term)
      query_terms = [term for term in query_norm.split() if term]
      matched_chats = []
      for idx, chat_item in enumerate(saved_chats):
        searchable = normalize_chat_search_text(get_chat_search_content(chat_item))
        if not query_terms or all(term in searchable for term in query_terms):
          matched_chats.append((idx, chat_item))

      if folder_filter != "كل المجلدات":
        matched_chats = [(idx, chat_item) for idx, chat_item in matched_chats if chat_item.get("folder", "عام") == folder_filter]
      matched_chats.sort(key=lambda pair: bool(pair[1].get("pinned", False)), reverse=True)
      if query_terms:
        st.caption(f"نتائج البحث: {len(matched_chats)} محادثة")
      if query_terms and not matched_chats:
        st.info("ما لقينا محادثات تطابق بحثك. جرّب كلمة ثانية.")

      for idx, chat_item in matched_chats:
        chat_title = str(chat_item.get("title", "محادثة"))
        saved_at = str(chat_item.get("saved_at", ""))
        chat_messages = chat_item.get("messages", [])
        with st.expander(
            f"{'📌 ' if chat_item.get('pinned', False) else '🗂️ '}{chat_title} ({saved_at})",
            expanded=(idx == 0 and not query_terms),
        ):
          chat_item.setdefault("folder", "عام")
          chat_item.setdefault("pinned", False)
          control_pin, control_folder = st.columns([1, 2])
          with control_pin:
            pin_label = "📌 إلغاء التثبيت" if chat_item.get("pinned") else "📌 تثبيت المحادثة"
            if st.button(pin_label, key=f"toggle_pin_chat_{chat_item.get('id', idx)}_{idx}"):
              chat_item["pinned"] = not bool(chat_item.get("pinned", False))
              save_account_everywhere(rec["user_email"], rec)
              st.rerun()
          with control_folder:
            current_folder = chat_item.get("folder", "عام")
            if current_folder not in chat_folders:
              chat_folders.append(current_folder)
            new_chat_folder = st.selectbox("مجلد المحادثة", chat_folders, index=chat_folders.index(current_folder), key=f"move_chat_folder_{chat_item.get('id', idx)}_{idx}")
            if new_chat_folder != current_folder:
              chat_item["folder"] = new_chat_folder
              save_account_everywhere(rec["user_email"], rec)
              st.rerun()
          title_matches = bool(query_terms) and all(
              term in normalize_chat_search_text(chat_title) for term in query_terms
          )
          if query_terms and not title_matches:
            for msg in chat_messages:
              content = msg.get("content", "")
              searchable_msg = normalize_chat_search_text(
                  content if isinstance(content, str) else get_chat_search_content({"messages": [msg]})
              )
              if all(term in searchable_msg for term in query_terms):
                role_label = "المستخدم" if msg.get("role") == "user" else "BRAS AI"
                st.markdown(f"**{role_label} (مطابقة البحث):**")
                render_chat_message(msg)
          else:
            for m in chat_messages:
              role_label = "المستخدم" if m.get("role") == "user" else "BRAS AI"
              st.markdown(f"**{role_label}:**")
              render_chat_message(m)
          # Prepare a readable plain-text transcript alongside the existing JSON export.
          transcript_lines = [f"BRAS AI — {chat_title}", f"تاريخ الحفظ: {saved_at}", "=" * 36, ""]
          for transcript_msg in chat_messages:
            transcript_role = "المستخدم" if transcript_msg.get("role") == "user" else "BRAS AI"
            transcript_content = transcript_msg.get("content", "")
            if isinstance(transcript_content, str):
              transcript_text = transcript_content
            elif isinstance(transcript_content, list):
              transcript_text = "\n".join(
                str(part.get("text", "")) for part in transcript_content
                if isinstance(part, dict) and part.get("type") == "text"
              )
            else:
              transcript_text = str(transcript_content)
            transcript_lines.extend([f"{transcript_role}:", transcript_text, "", "-" * 24, ""])
          transcript_text_file = "\n".join(transcript_lines)
          c_json, c_txt, c_delete = st.columns([1, 1, 1])
          with c_json:
            st.download_button(
                label="⬇️ JSON",
                data=json.dumps(chat_item, ensure_ascii=False, indent=2),
                file_name=f"bras_ai_chat_{chat_item.get('id', idx)}.json",
                mime="application/json",
                key=f"dl_chat_{idx}_{chat_item.get('id', idx)}",
            )
          with c_txt:
            st.download_button(
                label="📄 TXT مرتب",
                data=transcript_text_file,
                file_name=f"bras_ai_chat_{chat_item.get('id', idx)}.txt",
                mime="text/plain; charset=utf-8",
                key=f"dl_chat_txt_{idx}_{chat_item.get('id', idx)}",
            )
          with c_delete:
            if st.button("🗑️ حذف", key=f"delete_saved_chat_{idx}_{chat_item.get('id', idx)}"):
              rec["saved_chats"].pop(idx)
              save_account_everywhere(rec["user_email"], rec)
              st.success("تم حذف الدردشة من السجل.")
              st.rerun()

  elif nav_mode == "🖼️ مكتبتي الصور":
    st.header("🖼️ مكتبة الصور الخاصة بي")
    gallery = rec.setdefault("image_library", [])
    if not gallery:
      st.info("بعد إنشاء أو تعديل صورة، تنحفظ نسخة تلقائياً هنا.")
    else:
      st.caption(f"الصور المحفوظة: {len(gallery)} (نحتفظ بآخر 10 صور لتخفيف حجم الحساب)")
      for index, item in enumerate(gallery):
        with st.container(border=True):
          try:
            raw_image = base64.b64decode(item.get("image_b64", ""))
            st.image(raw_image, caption=item.get("prompt", "صورة محفوظة"), use_container_width=True)
            render_image_actions(raw_image, f"bras_library_{item.get('id', index)}.jpg", f"gallery_{item.get('id', index)}")
          except Exception:
            st.warning("تعذر عرض هذه الصورة المخزنة.")
          st.caption(f"{item.get('created_at', '')} · {'تعديل' if item.get('kind') == 'edited' else 'إنشاء'}")
          if st.button("🗑️ حذف الصورة", key=f"delete_gallery_{item.get('id', index)}"):
            rec["image_library"] = [x for x in gallery if x.get("id") != item.get("id")]
            if rec.get("last_generated_image_id") == item.get("id"):
              rec["last_generated_image_id"] = None
            save_account_everywhere(rec["user_email"], rec)
            st.rerun()

  elif nav_mode == t_sec_pricing:
    st.header("💳 الباقات والاشتراك عبر كي كارد (BRAS AI)")
    if rec.get("is_subscribed"):
      st.success(
          f"✅ اشتراككِ مفعّل حالياً ({rec.get('subscription_plan')})."
      )

    p1, p2, p3 = st.columns(3)
    with p1:
      st.markdown(
          "<div class='plan-box'><h3>أسبوعي</h3><h2>$2</h2><p>صلاحية 7"
          " أيام</p></div>",
          unsafe_allow_html=True,
      )
      if st.button("اختيار الباقة الأسبوعية ($2)", key="plan_w"):
        rec["selected_payment_plan"] = "أسبوعي - $2"
        save_account_everywhere(rec["user_email"], rec)
        st.rerun()
    with p2:
      st.markdown(
          "<div class='plan-box'><h3>شهري</h3><h2>$10</h2><p>صلاحية 30"
          " يوماً</p></div>",
          unsafe_allow_html=True,
      )
      if st.button("اختيار الباقة الشهرية ($10)", key="plan_m"):
        rec["selected_payment_plan"] = "شهري - $10"
        save_account_everywhere(rec["user_email"], rec)
        st.rerun()
    with p3:
      st.markdown(
          "<div class='plan-box'><h3>سنوي</h3><h2>$50</h2><p>صلاحية 365"
          " يوماً</p></div>",
          unsafe_allow_html=True,
      )
      if st.button("اختيار الباقة السنوية ($50)", key="plan_y"):
        rec["selected_payment_plan"] = "سنوي - $50"
        save_account_everywhere(rec["user_email"], rec)
        st.rerun()

    active_plan = rec.get("selected_payment_plan", "أسبوعي - $2")
    st.markdown("---")
    st.subheader(f"💳 الدفع عبر كي كارد — {active_plan}")
    st.info(QICARD_INFO)

    with st.form("qicard_activation_form"):
      payer_ref = st.text_input(
          "اسم المحوِّل أو رقم مرجع التحويل (اختياري):",
          value=rec.get("payment_ref", ""),
          placeholder="مثال: اسم صاحب التحويل أو رقم العملية",
      )
      code_input = st.text_input(
          "أدخلي كود التفعيل بعد تأكيد الدفع:",
          type="password",
          placeholder="أدخلي الكود المرسل لكِ بعد التحويل",
      )
      confirm_pay = st.form_submit_button("تأكيد الدفع وتفعيل الاشتراك")
      if confirm_pay:
        if (code_input or "").strip() == SECRET_ACTIVATION_CODE:
          rec["is_subscribed"] = True
          rec["subscription_plan"] = active_plan
          rec["payment_ref"] = (payer_ref or "").strip()
          save_account_everywhere(rec["user_email"], rec)
          st.success(f"تم تفعيل اشتراككِ بنجاح ({active_plan})!")
          st.rerun()
        else:
          st.error(
              "كود التفعيل غير صحيح. أتمي التحويل عبر كي كارد أولاً ثم أدخلي"
              " الكود الصحيح."
          )

  elif nav_mode == t_sec_archive:
    st.markdown(
        f"<h2 style='text-align: center; color: #9b5de5;'>{t_archive_header}</h2>",
        unsafe_allow_html=True,
    )
    if not rec.get("archives"):
      st.info(t_no_archive)
    else:
      for idx, arch in enumerate(rec["archives"]):
        with st.expander(f"📁 {arch['title']}", expanded=True):
          c_browse, c_delete_archive = st.columns([2, 1])
          with c_browse:
            if st.button(t_browse, key=f"arch_{idx}"):
              rec["selected_section"] = arch["section"]
              rec["browsing_archive"] = arch
              save_account_everywhere(rec["user_email"], rec)
              st.rerun()
          with c_delete_archive:
            if st.button("🗑️ حذف الأرشيف", key=f"delete_archive_{idx}"):
              rec["archives"].pop(idx)
              save_account_everywhere(rec["user_email"], rec)
              st.success("تم حذف الأرشيف.")
              st.rerun()

  elif nav_mode == t_sec_settings:
    st.markdown(
        f"<h2 style='text-align: center;'>{t_settings_header}</h2>",
        unsafe_allow_html=True,
    )
    with st.container():
      st.markdown("<div class='settings-panel'>", unsafe_allow_html=True)
      new_name = st.text_input(t_username, value=rec["username"])
      new_theme = st.radio(
          t_theme,
          ("داكن (Dark)", "فاتح (Light)"),
          index=0 if ("داكن" in rec["theme"] or "Dark" in rec["theme"]) else 1,
      )
      new_voice = st.radio(
          t_voice,
          ("صوت بنت نقي وواضح (Nova)", "صوت رجل نقي وواضح (Onyx)"),
          index=0 if ("بنت" in rec["voice"] or "Nova" in rec["voice"]) else 1,
      )
      new_screen = st.radio(
          t_screen_mode,
          ("عادي (Normal)", "شاشة كاملة (Screen Mode)"),
          index=1 if is_screen_mode else 0,
      )

      languages_40 = [
          "العربية (Arabic)",
          "الإنجليزية (English)",
          "كرمانجي",
          "الكوردية السورانية (Kurdish Sorani)",
          "التركية (Türkçe)",
          "الفرنسية (Français)",
          "الألمانية (Deutsch)",
          "الإسبانية (Español)",
          "الإيطالية (Italiano)",
          "الروسية (Русский)",
          "الصينية المبسطة (中文)",
          "اليابانية (日本語)",
          "الكورية (한국어)",
          "الفارسية (فارسی)",
          "الأوردو (اردو)",
          "الهندية (हिन्दी)",
          "البرتغالية (Português)",
          "البنغالية (বাংলা)",
          "البنجابية (ਪੰਜਾਬੀ)",
          "الإندونيسية (Bahasa Indonesia)",
          "الماليزية (Bahasa Melayu)",
          "الفيتنامية (Tiếng Việt)",
          "التايلاندية (ไทย)",
          "الهولندية (Nederlands)",
          "البولندية (Polski)",
          "الأوكرانية (Українська)",
          "اليونانية (Ελληνικά)",
          "السويدية (Svenska)",
          "النرويجية (Norsk)",
          "الدنماركية (Dansk)",
          "الفنلندية (Suomi)",
          "المجرية (Magyar)",
          "التشيكية (Čeština)",
          "الرومانية (Română)",
          "البلغارية (Български)",
          "السلوفاكية (Slovenčina)",
          "الكرواتية (Hrvatski)",
          "العبرية (עברית)",
          "الفلبينية (Tagalog)",
          "السواحلية (Kiswahili)",
          "الأمهرية (አማርኛ)",
      ]

      current_lang_idx = (
          languages_40.index(rec["language"])
          if rec["language"] in languages_40
          else 0
      )
      new_lang = st.selectbox(t_lang_label, languages_40, index=current_lang_idx)

      st.markdown("---")
      st.subheader("🧠 الذاكرة الذكية التلقائية")
      auto_memory_choice = st.checkbox(
          "تفعيل الذاكرة التلقائية (يحفظ تفضيلات ومعلومات عامة مفيدة فقط)",
          value=bool(rec.get("auto_memory_enabled", True)),
          key="auto_memory_settings_toggle",
      )
      st.caption("يمكنك إيقاف الذاكرة أو مسح ملخصها في أي وقت. لا يُفترض حفظ المعلومات الحساسة.")
      if st.button("🗑️ مسح الذاكرة الذكية الآن", key="clear_auto_memory_now"):
        rec["auto_memory_summary"] = ""
        save_account_everywhere(rec["user_email"], rec)
        st.success("تم مسح الذاكرة الذكية.")
        st.rerun()
      st.markdown("---")
      st.checkbox("Enable notifications on app open", value=True)

      if st.button(t_save):
        lang_changed = new_lang != rec["language"]
        rec["username"] = new_name.strip() or rec["username"]
        rec["theme"] = new_theme
        rec["voice"] = new_voice
        rec["screen_mode"] = new_screen
        rec["language"] = new_lang
        rec["auto_memory_enabled"] = bool(auto_memory_choice)
        if not rec["auto_memory_enabled"]:
          rec["auto_memory_summary"] = rec.get("auto_memory_summary", "")
        if lang_changed:
          rec["selected_section"] = None
          rec["browsing_archive"] = None
        save_account_everywhere(rec["user_email"], rec)
        st.success(t_saved_ok)
        st.rerun()
      st.markdown("</div>", unsafe_allow_html=True)
