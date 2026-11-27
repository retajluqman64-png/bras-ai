# BRAS AI — Upgrade Pack 2.0

## Implemented in this build
- Configurable text model through `BRAS_TEXT_MODEL` (defaults to `gpt-4o-mini` for compatibility).
- Optional Responses API mode with text/image conversation-history conversion.
- Optional built-in web search in Responses API mode.
- OpenAI client timeout and retry configuration.
- Safer user-facing API error handling; provider exceptions are not displayed to users.

## Streamlit secrets
Configure these in Streamlit's secret manager (or a local `.streamlit/secrets.toml`):

```toml
OPENAI_API_KEY = "YOUR_SERVER_SIDE_KEY"
BRAS_TEXT_MODEL = "gpt-4o-mini"
BRAS_USE_RESPONSES_API = "false"
BRAS_ENABLE_WEB_SEARCH = "false"

SUPABASE_URL = ""
SUPABASE_KEY = ""
GOOGLE_CLIENT_ID = ""
GOOGLE_CLIENT_SECRET = ""
APP_REDIRECT_URI = ""
```

To enable Responses API, first set `BRAS_USE_RESPONSES_API = "true"` and test text, image, and multi-turn chats with a private test account. Keep web search off until the Responses API path is confirmed. Then optionally set `BRAS_ENABLE_WEB_SEARCH = "true"`; this may add latency and API costs.

## Install
```bash
pip install -r requirements-bras.txt
streamlit run BRAS_AI_2_0.py
```

## Production blockers before public launch
This is a first engineering pass, not a certification that the app is ready for public launch or sale.

- Replace local JSON account persistence with a properly configured database and row-level security. Verify RLS policies for every table; never expose a service-role key in browser code.
- Add OAuth `state` validation and robust session handling.
- Add server-side authorization checks for every paid feature. A client-side `is_subscribed` flag is not payment verification.
- Integrate payments with signed webhook verification; never activate plans only from a user-entered reference or shared activation code.
- Add per-user rate limits, abuse controls, usage metering, spending alerts, and hard budget limits.
- Add automated tests, backups, structured logs, monitoring, privacy policy, terms, and a data deletion process.
- Audit media-generation model identifiers and endpoints against models enabled for the API project.

## Valuation
No code change guarantees a $100,000 valuation. A buyer normally needs evidence of recurring revenue, active and retained users, low operating costs, clean ownership/IP records, security, documentation, and repeatable deployment.
