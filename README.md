Bras AI starter (Streamlit)

Files:
- app.py: starter UI with text chat, recorded-audio transcription, spoken replies, language selector, Google login hook, and a notifications placeholder.
- requirements.txt: Python dependencies.


IMPORTANT SETUP
1. Create a Streamlit project and place app.py in it.
2. Install dependencies from requirements.txt.
3. Add secrets to Streamlit's secrets manager (do not paste API keys into code):
   OPENAI_API_KEY = "your-api-key"
4. Configure Google OIDC in Streamlit secrets using the current Streamlit authentication documentation.
   The Google OAuth client must use the app's correct redirect URL; never share the client secret.
5. The Google login button is only functional after OIDC is configured.
6. Notification reading is not implemented in this web starter. Actual phone notifications require a companion native Android app and permissions, and later testing on a suitable device.

