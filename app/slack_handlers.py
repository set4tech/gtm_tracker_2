"""
Slack command handlers for GTM Tracker
"""
import os
from typing import Dict, Any
from app.storage import storage

# Initialize Slack client for posting messages
try:
    from slack_sdk import WebClient
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    slack_client = WebClient(token=slack_token) if slack_token else None
except ImportError:
    slack_client = None


def handle_gtm_help() -> Dict[str, Any]:
    """Handle /gtm-help command"""
    help_text = """
*GTM Tracker Commands*

• `/gtm-help` - Show this help message
• `/gtm-list [filter]` - List recent activities (optional filter)
• `/gtm-list public [filter]` - Share list with channel
• `/gtm-view [id]` - View details of a specific activity
• `/gtm-view [id] public` - Share activity details with channel
• `/gtm-add hypothesis | audience | channels` - Add a new activity
• `/gtm-update [id]` - Update an existing activity

*Examples:*
```
/gtm-list
/gtm-list public
/gtm-list linkedin
/gtm-list public email
/gtm-view 1
/gtm-view 1 public
/gtm-add Test cold email | Startups | Email
```

*Sharing:* By default, responses are private (only you see them). Add `public` to share with the channel, or click the "Share with Channel" button.

*Need help?* Contact your team admin.
    """.strip()

    return {
        "response_type": "ephemeral",
        "text": help_text
    }


def handle_gtm_list(filter_text: str = None, public: bool = False) -> Dict[str, Any]:
    """Handle /gtm-list command"""
    # Check if user wants public sharing
    if filter_text and filter_text.lower() == 'public':
        public = True
        filter_text = None
    elif filter_text and filter_text.lower().startswith('public '):
        public = True
        filter_text = filter_text[7:].strip() or None

    activities = storage.list_all(limit=10, filter_text=filter_text)

    if not activities:
        text = "📭 No activities found."
        if filter_text:
            text = f"📭 No activities found matching '{filter_text}'."

        return {
            "response_type": "ephemeral",
            "text": text
        }

    # Build response
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📊 GTM Activities ({len(activities)})"
            }
        }
    ]

    if filter_text:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Filtered by: *{filter_text}*"
                }
            ]
        })

    for activity in activities:
        blocks.append({"type": "divider"})

        # Build metrics line
        metrics = []
        if activity.list_size:
            metrics.append(f"📧 {activity.list_size}")
        if activity.meetings_booked:
            metrics.append(f"📅 {activity.meetings_booked} meetings")
        if activity.start_date:
            metrics.append(f"🗓️ Started {activity.start_date}")

        metrics_text = " • ".join(metrics) if metrics else "No metrics yet"

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*#{activity.id}* - {activity.hypothesis}\n"
                        f"👥 {activity.audience or 'N/A'} • 📢 {activity.channels or 'N/A'}\n"
                        f"{metrics_text}"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View Details"
                },
                "action_id": f"view_activity_{activity.id}",
                "value": str(activity.id)
            }
        })

    return {
        "response_type": "in_channel" if public else "ephemeral",
        "blocks": blocks
    }


def handle_gtm_view(activity_id_str: str, public: bool = False) -> Dict[str, Any]:
    """Handle /gtm-view command"""
    # Check if user wants public sharing
    if activity_id_str and activity_id_str.lower().endswith(' public'):
        public = True
        activity_id_str = activity_id_str[:-7].strip()

    if not activity_id_str:
        return {
            "response_type": "ephemeral",
            "text": "❌ Please provide an activity ID. Example: `/gtm-view 1`\nTip: Add 'public' to share with channel: `/gtm-view 1 public`"
        }

    try:
        activity_id = int(activity_id_str)
    except ValueError:
        return {
            "response_type": "ephemeral",
            "text": f"❌ Invalid activity ID: `{activity_id_str}`. Please use a number."
        }

    activity = storage.get(activity_id)
    if not activity:
        return {
            "response_type": "ephemeral",
            "text": f"❌ Activity #{activity_id} not found."
        }

    # Build detailed view
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Activity #{activity.id}"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Hypothesis*\n{activity.hypothesis}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Audience*\n{activity.audience or 'N/A'}"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Channels*\n{activity.channels or 'N/A'}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*List Size*\n{activity.list_size or 'N/A'}"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Meetings Booked*\n{activity.meetings_booked or 'N/A'}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Est. Weekly Hours*\n{activity.est_weekly_hrs or 'N/A'}"
                }
            ]
        }
    ]

    # Add dates if available
    if activity.start_date or activity.end_date:
        blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Start Date*\n{activity.start_date or 'N/A'}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*End Date*\n{activity.end_date or 'N/A'}"
                }
            ]
        })

    if activity.description:
        # Limit description length for Slack
        desc = activity.description
        if len(desc) > 500:
            desc = desc[:497] + "..."

        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Description*\n{desc}"
            }
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Created: {activity.created_at[:10]}"
            }
        ]
    })

    # Add share button if viewing privately
    if not public:
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📢 Share with Channel"
                    },
                    "style": "primary",
                    "action_id": f"share_activity_{activity.id}",
                    "value": str(activity.id)
                }
            ]
        })

    return {
        "response_type": "in_channel" if public else "ephemeral",
        "blocks": blocks
    }


def handle_gtm_add(text: str) -> Dict[str, Any]:
    """Handle /gtm-add command"""
    if not text:
        return {
            "response_type": "ephemeral",
            "text": "❌ Please provide activity details.\nFormat: `/gtm-add hypothesis | audience | channels`\nExample: `/gtm-add Test cold email | Startups | Email`"
        }

    # Parse pipe-separated values
    parts = [p.strip() for p in text.split("|")]

    if len(parts) < 1:
        return {
            "response_type": "ephemeral",
            "text": "❌ Invalid format. Use: `/gtm-add hypothesis | audience | channels`"
        }

    hypothesis = parts[0]
    audience = parts[1] if len(parts) > 1 else None
    channels = parts[2] if len(parts) > 2 else None

    # Create activity
    activity = storage.create(
        hypothesis=hypothesis,
        audience=audience,
        channels=channels
    )

    # Post to #all-set4 channel
    if slack_client:
        try:
            slack_client.chat_postMessage(
                channel="all-set4",
                text=f"🎯 New GTM Activity Created: {activity.hypothesis}",
                blocks=[
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🎯 New GTM Activity #{activity.id}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Hypothesis*\n{activity.hypothesis}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Audience*\n{activity.audience or 'N/A'}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Channels*\n{activity.channels or 'N/A'}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Activity ID*\n#{activity.id}"
                            }
                        ]
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "View details: `/gtm-view " + str(activity.id) + "`"
                            }
                        ]
                    }
                ]
            )
        except Exception as e:
            # Log error but don't fail the command
            print(f"Warning: Could not post to #all-set4: {e}")

    return {
        "response_type": "ephemeral",
        "text": f"✅ Created activity #{activity.id}: {activity.hypothesis}\n_Also posted to #all-set4_",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"✅ *Activity #{activity.id} Created*\n\n*Hypothesis:* {activity.hypothesis}\n*Audience:* {activity.audience or 'N/A'}\n*Channels:* {activity.channels or 'N/A'}\n\n_Also posted to <#all-set4>_"
                }
            }
        ]
    }


def handle_gtm_update(activity_id_str: str) -> Dict[str, Any]:
    """Handle /gtm-update command (placeholder for modal)"""
    if not activity_id_str:
        return {
            "response_type": "ephemeral",
            "text": "❌ Please provide an activity ID. Example: `/gtm-update 1`"
        }

    try:
        activity_id = int(activity_id_str)
    except ValueError:
        return {
            "response_type": "ephemeral",
            "text": f"❌ Invalid activity ID: `{activity_id_str}`. Please use a number."
        }

    activity = storage.get(activity_id)
    if not activity:
        return {
            "response_type": "ephemeral",
            "text": f"❌ Activity #{activity_id} not found."
        }

    return {
        "response_type": "ephemeral",
        "text": f"ℹ️ Update functionality coming soon! For now, use `/gtm-view {activity_id}` to view the activity."
    }
