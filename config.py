import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

class Settings(BaseSettings):
    # Meta / Facebook Configuration
    PAGE_ACCESS_TOKEN: str = os.getenv("PAGE_ACCESS_TOKEN", "")
    PAGE_ID: str = os.getenv("PAGE_ID", "")
    VERIFY_TOKEN: str = os.getenv("VERIFY_TOKEN", "my_secure_fb_webhook_verify_token_2024")
    APP_SECRET: Optional[str] = os.getenv("APP_SECRET", None)
    GRAPH_API_VERSION: str = os.getenv("GRAPH_API_VERSION", "v20.0")

    # Gemini AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    AI_SYSTEM_PROMPT: str = os.getenv(
        "AI_SYSTEM_PROMPT",
        "You are a friendly, helpful, and professional social media assistant replying to comments on our Facebook Page. "
        "Keep replies concise (1-3 sentences), polite, and engaging. "
        "Reply in the same language as the user comment (English, Hindi, or Hinglish). "
        "Include friendly emojis when suitable."
    )

    # Behavior
    AUTO_LIKE_COMMENTS: bool = os.getenv("AUTO_LIKE_COMMENTS", "true").lower() in ("true", "1", "yes")
    ENABLE_AI_REPLIES: bool = os.getenv("ENABLE_AI_REPLIES", "true").lower() in ("true", "1", "yes")
    FALLBACK_REPLY: str = os.getenv("FALLBACK_REPLY", "Thank you for reaching out! We appreciate your comment. 😊")

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
