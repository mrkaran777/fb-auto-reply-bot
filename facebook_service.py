import hmac
import hashlib
import logging
from typing import List, Dict, Any, Optional
from collections import OrderedDict
import requests
from config import settings

logger = logging.getLogger(__name__)

class RecentCommentCache:
    """Simple LRU cache to prevent replying to the same comment multiple times if webhook retries."""
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache: OrderedDict[str, bool] = OrderedDict()

    def contains(self, key: str) -> bool:
        return key in self.cache

    def add(self, key: str):
        if key in self.cache:
            self.cache.move_to_end(key)
            return
        if len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = True

class FacebookService:
    def __init__(self):
        self.graph_url = f"https://graph.facebook.com/{settings.GRAPH_API_VERSION}"
        self.cache = RecentCommentCache(capacity=1000)

    def verify_webhook_signature(self, payload: bytes, signature_header: Optional[str]) -> bool:
        """
        Verify incoming webhook payload using App Secret HMAC SHA256.
        """
        if not settings.APP_SECRET:
            # If APP_SECRET is not configured by user yet, skip signature verification
            return True

        if not signature_header or not signature_header.startswith("sha256="):
            logger.warning("Missing or malformed X-Hub-Signature-256 header.")
            return False

        expected_signature = signature_header.split("sha256=")[1]
        calculated_signature = hmac.new(
            key=settings.APP_SECRET.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256
        ).hexdigest()

        is_valid = hmac.compare_digest(expected_signature, calculated_signature)
        if not is_valid:
            logger.warning("Webhook signature mismatch!")
        return is_valid

    def parse_comment_events(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract valid comment events from Facebook Webhook feed payload.
        Filters out page's own comments and duplicate webhook retries.
        """
        valid_comments = []

        if data.get("object") != "page":
            return valid_comments

        entries = data.get("entry", [])
        for entry in entries:
            page_id = entry.get("id")
            changes = entry.get("changes", [])

            for change in changes:
                if change.get("field") != "feed":
                    continue

                value = change.get("value", {})
                item = value.get("item")
                verb = value.get("verb")

                # We only want newly added comments
                if item != "comment" or verb != "add":
                    continue

                comment_id = value.get("comment_id")
                sender_id = str(value.get("sender_id", ""))
                sender_name = value.get("sender_name", "")
                message = value.get("message", "").strip()

                if not comment_id:
                    continue

                # Loop prevention 1: Skip if sender is our own page
                if settings.PAGE_ID and sender_id == str(settings.PAGE_ID):
                    logger.info(f"Skipping comment {comment_id} posted by own page ({sender_id}).")
                    continue

                # Loop prevention 2: Skip if already processed recently
                if self.cache.contains(comment_id):
                    logger.info(f"Skipping comment {comment_id}, already processed.")
                    continue

                # Skip if empty message
                if not message:
                    logger.info(f"Skipping empty comment {comment_id}.")
                    continue

                # Mark as processed
                self.cache.add(comment_id)

                valid_comments.append({
                    "comment_id": comment_id,
                    "sender_id": sender_id,
                    "sender_name": sender_name,
                    "message": message,
                    "page_id": page_id
                })

        return valid_comments

    def reply_to_comment(self, comment_id: str, reply_message: str) -> bool:
        """
        Post a reply to a Facebook comment using Graph API:
        POST https://graph.facebook.com/{version}/{comment_id}/comments
        """
        if not settings.PAGE_ACCESS_TOKEN:
            logger.error("PAGE_ACCESS_TOKEN is not set. Cannot post comment reply.")
            return False

        url = f"{self.graph_url}/{comment_id}/comments"
        params = {"access_token": settings.PAGE_ACCESS_TOKEN}
        payload = {"message": reply_message}

        try:
            response = requests.post(url, params=params, json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully posted reply to comment {comment_id}. Reply ID: {result.get('id')}")
                return True
            else:
                logger.error(f"Failed to reply to comment {comment_id}. HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exception while replying to comment {comment_id}: {e}")
            return False

    def like_comment(self, comment_id: str) -> bool:
        """
        Like a Facebook comment using Graph API:
        POST https://graph.facebook.com/{version}/{comment_id}/likes
        """
        if not settings.PAGE_ACCESS_TOKEN or not settings.AUTO_LIKE_COMMENTS:
            return False

        url = f"{self.graph_url}/{comment_id}/likes"
        params = {"access_token": settings.PAGE_ACCESS_TOKEN}

        try:
            response = requests.post(url, params=params, timeout=10)
            if response.status_code == 200:
                logger.info(f"Successfully liked comment {comment_id}.")
                return True
            else:
                logger.warning(f"Could not like comment {comment_id}. HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.warning(f"Exception while liking comment {comment_id}: {e}")
            return False

facebook_service = FacebookService()
