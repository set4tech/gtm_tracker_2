"""
Slack utility functions for signature verification
"""
import hashlib
import hmac
import time
from typing import Optional


def verify_slack_signature(
    signing_secret: str,
    timestamp: str,
    body: bytes,
    signature: str
) -> bool:
    """
    Verify that a request came from Slack

    Args:
        signing_secret: Your Slack app's signing secret
        timestamp: X-Slack-Request-Timestamp header
        body: Raw request body
        signature: X-Slack-Signature header

    Returns:
        True if signature is valid, False otherwise
    """
    # Check timestamp to prevent replay attacks
    try:
        request_timestamp = int(timestamp)
        current_timestamp = int(time.time())

        # Request is older than 5 minutes
        if abs(current_timestamp - request_timestamp) > 60 * 5:
            return False
    except (ValueError, TypeError):
        return False

    # Construct signature base string
    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"

    # Create HMAC-SHA256 hash
    my_signature = 'v0=' + hmac.new(
        signing_secret.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Compare signatures
    return hmac.compare_digest(my_signature, signature)
