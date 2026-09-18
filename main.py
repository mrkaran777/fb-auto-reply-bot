import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, Response, Query, HTTPException, BackgroundTasks, status
from pydantic import BaseModel

from config import settings
from facebook_service import facebook_service
from ai_service import ai_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("facebook_bot")

app = FastAPI(
    title="Facebook Comment Reply Automation",
    description="Automated AI replies for Facebook Page comments using Meta Graph API & Gemini AI",
    version="1.0.0"
)

def process_comment_in_background(comment: Dict[str, Any]):
    """
    Background worker to handle AI generation and Facebook reply
    without blocking Meta's webhook response.
    """
    comment_id = comment["comment_id"]
    sender_name = comment.get("sender_name", "")
    message = comment["message"]

    logger.info(f"Processing comment [{comment_id}] from '{sender_name}': \"{message}\"")

    # Step 1: Auto-like the comment if enabled
    if settings.AUTO_LIKE_COMMENTS:
        facebook_service.like_comment(comment_id)

    # Step 2: Generate reply via Gemini AI
    reply_text = ai_service.generate_reply(comment_text=message, sender_name=sender_name)

    # Step 3: Send reply to Facebook comment
    success = facebook_service.reply_to_comment(comment_id=comment_id, reply_message=reply_text)
    if success:
        logger.info(f"Successfully processed and replied to comment {comment_id}")
    else:
        logger.error(f"Failed to reply to comment {comment_id}")

@app.get("/")
def health_check():
    """Health check endpoint and configuration summary."""
    return {
        "status": "online",
        "service": "Facebook Comment Automation Bot",
        "config": {
            "page_id_configured": bool(settings.PAGE_ID),
            "page_access_token_configured": bool(settings.PAGE_ACCESS_TOKEN),
            "gemini_api_key_configured": bool(settings.GEMINI_API_KEY),
            "ai_model": settings.GEMINI_MODEL,
            "auto_like_enabled": settings.AUTO_LIKE_COMMENTS,
            "ai_replies_enabled": settings.ENABLE_AI_REPLIES
        }
    }

@app.get("/webhook")
def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    verify_token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    """
    Webhook verification endpoint called by Meta Developer Dashboard.
    When you configure the webhook URL, Meta sends a GET request with:
    - hub.mode = 'subscribe'
    - hub.verify_token = [your configured token]
    - hub.challenge = [random string to echo back]
    """
    logger.info(f"Received webhook verification request. mode={mode}")

    if mode == "subscribe" and verify_token == settings.VERIFY_TOKEN:
        logger.info("Webhook verification succeeded.")
        # Return the challenge string as plain text with 200 OK
        return Response(content=challenge, media_type="text/plain", status_code=status.HTTP_200_OK)
    
    logger.warning("Webhook verification failed. Token mismatch or invalid mode.")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token mismatch or invalid mode"
    )

@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook event receiver for Facebook Page events (feed changes).
    Responds with HTTP 200 immediately to Meta, and dispatches comment processing
    to background tasks.
    """
    raw_body = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256")

    # Verify signature if APP_SECRET is configured
    if settings.APP_SECRET:
        if not facebook_service.verify_webhook_signature(raw_body, signature_header):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature"
            )

    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Error parsing JSON payload: {e}")
        return {"status": "error", "message": "Invalid JSON"}

    # Extract valid comment events
    comments = facebook_service.parse_comment_events(data)
    logger.info(f"Found {len(comments)} valid comment event(s) to process.")

    # Queue background task for each comment
    for comment in comments:
        background_tasks.add_task(process_comment_in_background, comment)

    # Return HTTP 200 OK immediately
    return {"status": "received", "count": len(comments)}

class TestReplyRequest(BaseModel):
    comment_text: str
    sender_name: str = "Test User"

@app.post("/test-reply")
def test_ai_reply(payload: TestReplyRequest):
    """
    Utility endpoint to test AI comment reply generation locally
    without needing a Facebook webhook event.
    """
    reply = ai_service.generate_reply(
        comment_text=payload.comment_text,
        sender_name=payload.sender_name
    )
    return {
        "user_comment": payload.comment_text,
        "sender_name": payload.sender_name,
        "ai_reply": reply
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
  
