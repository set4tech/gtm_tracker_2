"""
Slack utility functions for GTM Tracker
"""
import os
import hmac
import hashlib
import time
from typing import Optional
from fastapi import Request, HTTPException

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    WebClient = None


def verify_slack_request(request: Request, body: bytes, timestamp: str, signature: str) -> bool:
    """
    Verify that a request came from Slack using the signing secret.

    Args:
        request: FastAPI request object
        body: Raw request body
        timestamp: X-Slack-Request-Timestamp header
        signature: X-Slack-Signature header

    Returns:
        True if request is valid, False otherwise
    """
    slack_signing_secret = os.getenv("SLACK_SIGNING_SECRET", "")

    if not slack_signing_secret:
        # If no signing secret is configured, skip verification (development mode)
        return True

    # Check timestamp to prevent replay attacks (5 minutes)
    current_time = int(time.time())
    if abs(current_time - int(timestamp)) > 60 * 5:
        return False

    # Compute signature
    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    my_signature = 'v0=' + hmac.new(
        slack_signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()

    # Compare signatures
    return hmac.compare_digest(my_signature, signature)


async def verify_slack_signature(request: Request) -> bool:
    """
    Middleware-style verification of Slack request signature.
    Raises HTTPException if verification fails.
    """
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")

    if not timestamp or not signature:
        raise HTTPException(status_code=400, detail="Missing Slack signature headers")

    body = await request.body()

    if not verify_slack_request(request, body, timestamp, signature):
        raise HTTPException(status_code=403, detail="Invalid Slack signature")

    return True


def format_activity_for_slack(activity) -> str:
    """
    Format an activity object as a Slack message string.

    Args:
        activity: GTMActivity model instance

    Returns:
        Formatted string for Slack
    """
    text = f"*#{activity.id}: {activity.hypothesis}*\n"

    if activity.audience:
        text += f"👥 Audience: {activity.audience}\n"
    if activity.channels:
        text += f"📢 Channels: {activity.channels}\n"
    if activity.description:
        text += f"📝 Description: {activity.description}\n"
    if activity.list_size:
        text += f"📊 List Size: {activity.list_size}\n"
    if activity.meetings_booked:
        text += f"📅 Meetings Booked: {activity.meetings_booked}\n"
    if activity.start_date:
        text += f"📆 Start: {activity.start_date}\n"
    if activity.end_date:
        text += f"📆 End: {activity.end_date}\n"
    if activity.est_weekly_hrs:
        text += f"⏰ Est Weekly Hours: {activity.est_weekly_hrs}\n"

    return text


def create_update_modal(activity) -> dict:
    """
    Create a Slack modal view for updating an activity.

    Args:
        activity: GTMActivity model instance

    Returns:
        Modal view dict
    """
    return {
        "type": "modal",
        "callback_id": f"update_activity_{activity.id}",
        "title": {
            "type": "plain_text",
            "text": f"Update Activity #{activity.id}"
        },
        "submit": {
            "type": "plain_text",
            "text": "Save"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "input",
                "block_id": "hypothesis",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "hypothesis_input",
                    "initial_value": activity.hypothesis or ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "Hypothesis"
                }
            },
            {
                "type": "input",
                "block_id": "audience",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "audience_input",
                    "initial_value": activity.audience or ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "Audience"
                }
            },
            {
                "type": "input",
                "block_id": "channels",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "channels_input",
                    "initial_value": activity.channels or ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "Channels"
                }
            },
            {
                "type": "input",
                "block_id": "description",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "description_input",
                    "multiline": True,
                    "initial_value": activity.description or ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "Description"
                }
            },
            {
                "type": "input",
                "block_id": "list_size",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "list_size_input",
                    "initial_value": str(activity.list_size) if activity.list_size else ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "List Size"
                }
            },
            {
                "type": "input",
                "block_id": "meetings_booked",
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "meetings_booked_input",
                    "initial_value": str(activity.meetings_booked) if activity.meetings_booked else ""
                },
                "label": {
                    "type": "plain_text",
                    "text": "Meetings Booked"
                }
            }
        ]
    }


def parse_modal_submission(view: dict) -> dict:
    """
    Parse a modal submission and extract form values.

    Args:
        view: Modal view state dict

    Returns:
        Dict of field values
    """
    values = view.get("state", {}).get("values", {})

    data = {}

    # Extract hypothesis
    hypothesis_block = values.get("hypothesis", {})
    data["hypothesis"] = hypothesis_block.get("hypothesis_input", {}).get("value")

    # Extract optional fields
    audience_block = values.get("audience", {})
    data["audience"] = audience_block.get("audience_input", {}).get("value") or None

    channels_block = values.get("channels", {})
    data["channels"] = channels_block.get("channels_input", {}).get("value") or None

    description_block = values.get("description", {})
    data["description"] = description_block.get("description_input", {}).get("value") or None

    list_size_block = values.get("list_size", {})
    list_size_value = list_size_block.get("list_size_input", {}).get("value")
    data["list_size"] = int(list_size_value) if list_size_value and list_size_value.strip() else None

    meetings_booked_block = values.get("meetings_booked", {})
    meetings_value = meetings_booked_block.get("meetings_booked_input", {}).get("value")
    data["meetings_booked"] = int(meetings_value) if meetings_value and meetings_value.strip() else None

    return data


def post_new_activity_notification(activity, slack_client: Optional[WebClient] = None, channel: str = None) -> bool:
    """
    Post a notification to Slack when a new GTM activity is created.

    Args:
        activity: GTMActivity model instance
        slack_client: Slack WebClient instance (optional, will be created if not provided)
        channel: Slack channel to post to (defaults to env var SLACK_NOTIFICATION_CHANNEL or #all-set4)

    Returns:
        True if notification was sent successfully, False otherwise
    """
    if not SLACK_AVAILABLE:
        return False

    # Get or create Slack client
    if not slack_client:
        slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_bot_token:
            return False
        slack_client = WebClient(token=slack_bot_token)

    # Get channel from parameter, environment, or default
    if not channel:
        channel = os.getenv("SLACK_NOTIFICATION_CHANNEL", "all-set4")

    # Ensure channel starts with #
    if not channel.startswith("#"):
        channel = f"#{channel}"

    try:
        # Build message blocks
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🚀 *New GTM Activity!*"
                }
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": format_activity_for_slack(activity)
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Details"},
                        "value": str(activity.id),
                        "action_id": f"view_activity_{activity.id}"
                    }
                ]
            }
        ]

        # Post message to Slack
        response = slack_client.chat_postMessage(
            channel=channel,
            text=f"New GTM Activity: {activity.hypothesis}",  # Fallback text
            blocks=blocks
        )

        return response.get("ok", False)

    except SlackApiError as e:
        # Log error but don't fail the request
        print(f"Error posting to Slack: {e.response['error']}")
        return False
    except Exception as e:
        print(f"Unexpected error posting to Slack: {str(e)}")
        return False
