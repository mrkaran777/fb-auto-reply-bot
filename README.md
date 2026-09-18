# Facebook Page AI Comment Reply Automation 🚀

Yeh project Facebook Page ke naye comments par automatically AI-powered (Google Gemini) ya custom replies post karta hai via official **Meta Graph API** aur **Facebook Webhooks**.

---

## 🌟 Features
- **Official & Ban-Safe**: Meta ke official Graph API aur Webhooks par based.
- **Smart AI Replies**: Google Gemini AI (1.5 Flash / Pro) se natural, polite aur multilingual (Hindi, Hinglish, English) reply generation.
- **Auto-Like**: Comment ka reply karne se pehle use automatically like karne ka option.
- **Loop & Spam Prevention**:
  - Apne hi page ke comments ko auto-skip karta hai taaki infinite loop na bane.
  - Webhook retry duplication cache.
- **Fast & Async**: FastAPI BackgroundTasks use karta hai taaki Facebook Webhooks timeout na ho.

---

## 📁 Project Structure

```
facebook_bot/
├── main.py              # FastAPI server (GET/POST /webhook, /test-reply)
├── config.py            # Environment configuration loader
├── facebook_service.py  # Meta Graph API client & Webhook parser
├── ai_service.py        # Google Gemini AI integration
├── test_simulation.py   # Offline test & simulation script
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # Setup guide
```

---

## 🛠️ Step-by-Step Setup Guide

### 1. Requirements Install Karein
```bash
pip install -r requirements.txt
```

### 2. Environment Variables (.env) Setup
`.env.example` ko copy karke `.env` banayein:
```bash
cp .env.example .env
```
Aur usme apni details bharein:
- `PAGE_ACCESS_TOKEN`: Facebook Page ka access token.
- `PAGE_ID`: Apne Facebook Page ki Numeric ID.
- `VERIFY_TOKEN`: Koi bhi secret word (e.g. `my_fb_secret_token_123`).
- `APP_SECRET`: Meta App Dashboard se App Secret (Settings > Basic).
- `GEMINI_API_KEY`: Google AI Studio se free API key ([aistudio.google.com](https://aistudio.google.com/)).

---

### 3. Meta (Facebook) Developer Portal Setup

1. **Meta Developer Account**:
   - [developers.facebook.com](https://developers.facebook.com/) par jayein aur **My Apps** > **Create App** par click karein.
   - App Type: **Business** ya **Other** chunein.

2. **Required Permissions (Graph API Explorer me)**:
   - [Graph API Explorer](https://developers.facebook.com/tools/explorer/) kholein.
   - Apni App aur **Page** select karein.
   - Permissions add karein:
     - `pages_show_list`
     - `pages_read_engagement`
     - `pages_manage_posts`
     - `pages_read_user_content`
   - **Generate Access Token** par click karein.
   - **Note**: Permanent Page Access Token ke liye Meta App review ya System User token recommend kiya jata hai.

3. **Page ID prapt karein**:
   - Apne Facebook Page ke *About* section me scroll karein, wahan **Page ID** mil jayegi.

---

### 4. Local Server Run Karein & Webhook URL Expose Karein

1. **Bot server start karein**:
```bash
python main.py
# ya
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

2. **ngrok se public HTTPS URL banayein**:
Facebook Webhooks ke liye valid HTTPS URL zaroori hota hai:
```bash
ngrok http 8000
```
Aapko ek public URL milega, jaise: `https://xyz123.ngrok-free.app`

---

### 5. Facebook Webhook Configure Karein

1. Meta Developer Dashboard me jayein -> **Add Product** -> **Webhooks** par click karein.
2. Dropdown se **Page** select karein aur **Subscribe to this object** par click karein.
3. Form me bharein:
   - **Callback URL**: `https://xyz123.ngrok-free.app/webhook`
   - **Verify Token**: Jo aapne `.env` me `VERIFY_TOKEN` set kiya tha (e.g. `my_fb_secret_token_123`).
4. **Verify and Save** par click karein.
5. Subscription fields me **`feed`** ko dhundhein aur **Subscribe** par click karein.
6. Apne Page ko Webhook se link karein:
   - Graph API Explorer me POST request karein:
     `/{PAGE_ID}/subscribed_apps?subscribed_fields=feed&access_token={PAGE_ACCESS_TOKEN}`

---

## 🧪 Testing

### 1. Offline Simulation Test (Bina Facebook credentials ke):
```bash
python test_simulation.py
```
Yeh script webhook parser, loop prevention, signature validation aur AI fallback ko test karegi.

### 2. Direct AI Test API:
Server chalne ke baad aap direct API se AI reply test kar sakte hain:
```bash
curl -X POST http://127.0.0.1:8000/test-reply \
  -H "Content-Type: application/json" \
  -d '{"comment_text": "Kya price hai iska?", "sender_name": "Rahul"}'
```

---

## ⚙️ Customization (AI Personality)

Aap `.env` file me `AI_SYSTEM_PROMPT` change karke bot ka tone badal sakte hain:
```env
AI_SYSTEM_PROMPT="Aap ek professional customer support agent hain. Comments ka jawab hamesha namaste keh kar aur vinamra bhasha me dein."
```
