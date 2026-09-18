"""
Simulation and Unit Test Script for Facebook Comment Automation Bot
Runs tests locally without needing external Meta servers.
"""

import hmac
import hashlib
import json
from config import settings
from facebook_service import FacebookService
from ai_service import AIService

def run_tests():
    print("=" * 60)
    print("Running Facebook Bot Simulation Tests")
    print("=" * 60)

    fb_service = FacebookService()
    ai = AIService()

    # ----------------------------------------------------
    # Test 1: Webhook Payload Parsing & Event Extraction
    # ----------------------------------------------------
    print("\n[Test 1] Testing Webhook Payload Parsing...")
    dummy_page_id = "1122334455"
    settings.PAGE_ID = dummy_page_id

    mock_webhook_payload = {
        "object": "page",
        "entry": [
            {
                "id": dummy_page_id,
                "time": 1726000000,
                "changes": [
                    {
                        "field": "feed",
                        "value": {
                            "item": "comment",
                            "verb": "add",
                            "comment_id": "comment_user_001",
                            "parent_id": "post_100",
                            "sender_id": "user_999",
                            "sender_name": "Rohan Sharma",
                            "message": "Kya aapke courses online available hain?",
                            "created_time": 1726000000
                        }
                    },
                    {
                        # This should be ignored (it is from the page itself)
                        "field": "feed",
                        "value": {
                            "item": "comment",
                            "verb": "add",
                            "comment_id": "comment_page_002",
                            "parent_id": "post_100",
                            "sender_id": dummy_page_id,
                            "sender_name": "My Business Page",
                            "message": "Our own page comment",
                            "created_time": 1726000005
                        }
                    }
                ]
            }
        ]
    }

    comments = fb_service.parse_comment_events(mock_webhook_payload)
    print(f"Extracted {len(comments)} comment(s).")
    assert len(comments) == 1, f"Expected 1 valid comment, got {len(comments)}"
    assert comments[0]["comment_id"] == "comment_user_001"
    assert comments[0]["sender_name"] == "Rohan Sharma"
    print("✓ Test 1 Passed: Valid comment extracted, page's own comment successfully filtered out!")

    # ----------------------------------------------------
    # Test 2: Duplicate Comment Filtering (Deduplication)
    # ----------------------------------------------------
    print("\n[Test 2] Testing Duplicate Comment Filtering...")
    duplicate_comments = fb_service.parse_comment_events(mock_webhook_payload)
    assert len(duplicate_comments) == 0, f"Expected 0 comments (duplicate), got {len(duplicate_comments)}"
    print("✓ Test 2 Passed: Duplicate webhook retry prevented!")

    # ----------------------------------------------------
    # Test 3: Signature Verification
    # ----------------------------------------------------
    print("\n[Test 3] Testing HMAC SHA-256 Webhook Signature Verification...")
    test_secret = "my_secret_key_123"
    settings.APP_SECRET = test_secret

    sample_payload = b'{"object": "page"}'
    valid_sig = "sha256=" + hmac.new(test_secret.encode(), sample_payload, hashlib.sha256).hexdigest()
    invalid_sig = "sha256=invalid_hash_value"

    assert fb_service.verify_webhook_signature(sample_payload, valid_sig) is True
    assert fb_service.verify_webhook_signature(sample_payload, invalid_sig) is False
    print("✓ Test 3 Passed: Signature validation verified successfully!")

    # ----------------------------------------------------
    # Test 4: AI Reply Service Fallback & Logic
    # ----------------------------------------------------
    print("\n[Test 4] Testing AI Service Fallback...")
    # Without API key, it should safely return fallback reply
    reply = ai.generate_reply("Kya price hai iska?", sender_name="Amit")
    print(f"Sample response: \"{reply}\"")
    assert reply is not None and len(reply) > 0
    print("✓ Test 4 Passed: AI Service handled request safely!")

    print("\n" + "=" * 60)
    print("All Simulation Tests Completed Successfully! 🎉")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
  
