import logging
import requests
from config import settings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.system_prompt = settings.AI_SYSTEM_PROMPT
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def generate_reply(self, comment_text: str, sender_name: str = "") -> str:
        """
        Generate a contextual, polite reply to a Facebook comment using Google Gemini AI.
        """
        if not settings.ENABLE_AI_REPLIES or not self.api_key:
            logger.info("AI replies disabled or GEMINI_API_KEY not configured. Using fallback reply.")
            return settings.FALLBACK_REPLY

        url = f"{self.base_url}?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        prompt = (
            f"Facebook post comment received.\n"
            f"Commenter Name: {sender_name if sender_name else 'A user'}\n"
            f"Comment: \"{comment_text}\"\n\n"
            f"Generate a friendly, concise, and helpful reply for Facebook:"
        )

        payload = {
            "system_instruction": {
                "parts": [{"text": self.system_prompt}]
            },
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 150
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    reply_parts = candidates[0].get("content", {}).get("parts", [])
                    if reply_parts:
                        reply_text = reply_parts[0].get("text", "").strip()
                        if reply_text:
                            logger.info(f"AI generated reply: {reply_text}")
                            return reply_text
            else:
                logger.error(f"Gemini API returned error {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Exception during Gemini AI reply generation: {e}")

        return settings.FALLBACK_REPLY

ai_service = AIService()

