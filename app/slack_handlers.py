"""
Slack command handlers for GTM Tracker
"""
from typing import Dict, Any
from app.storage import storage


def handle_gtm_help() -> Dict[str, Any]:
    """Handle /gtm-help command"""
    help_text = """
*GTM Tracker Commands*

• `/gtm-help` - Show this help message
• `/gtm-list [filter]` - List recent activities (optional filter)
• `/gtm-view [id]` - View details of a specific activity
• `/gtm-add hypothesis | audience | channels` - Add a new activity
• `/gtm-update [id]` - Update an existing activity

*Examples:*
```
/gtm-list
/gtm-list linkedin
/gtm-view 1
/gtm-add Test cold email | Startups | Email
```

*Need help?* Contact your team admin.
    """.strip()

    return {
        "response_type": "ephemeral",
        "text": help_text
    }


def handle_gtm_list(filter_text: str = None) -> Dict[str, Any]:
    """Handle /gtm-list command"""
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
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*#{activity.id}* - {activity.hypothesis}\n"
                        f"👥 {activity.audience or 'N/A'} • 📢 {activity.channels or 'N/A'}"
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
        "response_type": "ephemeral",
        "blocks": blocks
    }


def handle_gtm_view(activity_id_str: str) -> Dict[str, Any]:
    """Handle /gtm-view command"""
    if not activity_id_str:
        return {
            "response_type": "ephemeral",
            "text": "❌ Please provide an activity ID. Example: `/gtm-view 1`"
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

    return {
        "response_type": "ephemeral",
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

    return {
        "response_type": "in_channel",
        "text": f"✅ Created activity #{activity.id}: {activity.hypothesis}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"✅ *Activity #{activity.id} Created*\n\n*Hypothesis:* {activity.hypothesis}\n*Audience:* {activity.audience or 'N/A'}\n*Channels:* {activity.channels or 'N/A'}"
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
