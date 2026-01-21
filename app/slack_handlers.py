"""
Slack command handlers for GTM Tracker
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from app import crud
from app.schemas import ActivityCreate, ActivityUpdate


def handle_gtm_help() -> Dict[str, Any]:
    """
    Handle /gtm-help command
    Returns help text with available commands
    """
    help_text = """
*GTM Tracker Commands*

• `/gtm-list [filter]` - List recent GTM activities
  Example: `/gtm-list` or `/gtm-list LinkedIn`

• `/gtm-add hypothesis | audience | channels` - Add a new activity
  Example: `/gtm-add API is useful | Construction Software | Cold Email`

• `/gtm-view [id]` - View details of a specific activity
  Example: `/gtm-view 1`

• `/gtm-update [id]` - Update an activity (opens a form)
  Example: `/gtm-update 1`

• `/gtm-help` - Show this help message

*Tips:*
• Use pipe `|` to separate fields when adding activities
• Leave fields blank by using empty pipes: `hypothesis | | channels`
• Filter the list by including text after `/gtm-list`
"""
    return {
        "response_type": "ephemeral",
        "text": help_text
    }


def handle_gtm_list(db: Session, filter_text: str = None) -> Dict[str, Any]:
    """
    Handle /gtm-list command
    Lists recent GTM activities with optional filter
    """
    # Get activities with optional filter
    activities = crud.get_activities(
        db,
        skip=0,
        limit=10,
        hypothesis=filter_text if filter_text else None
    )

    if not activities:
        return {
            "response_type": "ephemeral",
            "text": "No activities found." + (f" (filtered by: {filter_text})" if filter_text else "")
        }

    # Build response blocks
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Recent GTM Activities* {f'(filtered by: {filter_text})' if filter_text else ''}"
            }
        },
        {"type": "divider"}
    ]

    for activity in activities:
        # Format activity info
        activity_text = f"*#{activity.id}: {activity.hypothesis}*\n"

        if activity.audience:
            activity_text += f"👥 Audience: {activity.audience}\n"
        if activity.channels:
            activity_text += f"📢 Channels: {activity.channels}\n"
        if activity.meetings_booked:
            activity_text += f"📅 Meetings: {activity.meetings_booked}\n"
        if activity.list_size:
            activity_text += f"📊 List Size: {activity.list_size}\n"

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": activity_text
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "View Details"
                },
                "value": str(activity.id),
                "action_id": f"view_activity_{activity.id}"
            }
        })

    return {
        "response_type": "ephemeral",
        "blocks": blocks
    }


def handle_gtm_view(db: Session, activity_id: str) -> Dict[str, Any]:
    """
    Handle /gtm-view command
    Shows detailed view of a specific activity
    """
    if not activity_id:
        return {
            "response_type": "ephemeral",
            "text": "Please provide an activity ID. Example: `/gtm-view 1`"
        }

    try:
        activity_id_int = int(activity_id)
    except ValueError:
        return {
            "response_type": "ephemeral",
            "text": f"Invalid activity ID: `{activity_id}`. Please use a number."
        }

    activity = crud.get_activity(db, activity_id_int)

    if not activity:
        return {
            "response_type": "ephemeral",
            "text": f"Activity #{activity_id} not found."
        }

    # Build detailed view
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Activity #{activity.id}*"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Hypothesis:*\n{activity.hypothesis}"
                }
            ]
        }
    ]

    # Add optional fields
    fields = []
    if activity.audience:
        fields.append({"type": "mrkdwn", "text": f"*Audience:*\n{activity.audience}"})
    if activity.channels:
        fields.append({"type": "mrkdwn", "text": f"*Channels:*\n{activity.channels}"})
    if activity.list_size:
        fields.append({"type": "mrkdwn", "text": f"*List Size:*\n{activity.list_size}"})
    if activity.meetings_booked:
        fields.append({"type": "mrkdwn", "text": f"*Meetings Booked:*\n{activity.meetings_booked}"})
    if activity.start_date:
        fields.append({"type": "mrkdwn", "text": f"*Start Date:*\n{activity.start_date}"})
    if activity.end_date:
        fields.append({"type": "mrkdwn", "text": f"*End Date:*\n{activity.end_date}"})
    if activity.est_weekly_hrs:
        fields.append({"type": "mrkdwn", "text": f"*Est Weekly Hours:*\n{activity.est_weekly_hrs}"})

    if fields:
        blocks.append({
            "type": "section",
            "fields": fields
        })

    if activity.description:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Description:*\n{activity.description}"
            }
        })

    # Add action buttons
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Edit"
                },
                "style": "primary",
                "value": str(activity.id),
                "action_id": f"edit_activity_{activity.id}"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Delete"
                },
                "style": "danger",
                "value": str(activity.id),
                "action_id": f"delete_activity_{activity.id}",
                "confirm": {
                    "title": {
                        "type": "plain_text",
                        "text": "Are you sure?"
                    },
                    "text": {
                        "type": "mrkdwn",
                        "text": f"This will permanently delete activity #{activity.id}"
                    },
                    "confirm": {
                        "type": "plain_text",
                        "text": "Delete"
                    },
                    "deny": {
                        "type": "plain_text",
                        "text": "Cancel"
                    }
                }
            }
        ]
    })

    return {
        "response_type": "ephemeral",
        "blocks": blocks
    }


def handle_gtm_add(db: Session, text: str) -> Dict[str, Any]:
    """
    Handle /gtm-add command
    Quick add format: hypothesis | audience | channels
    """
    if not text or text.strip() == "":
        return {
            "response_type": "ephemeral",
            "text": "Please provide activity details.\nFormat: `hypothesis | audience | channels`\nExample: `/gtm-add API is useful | Construction Software | Cold Email`"
        }

    # Parse input
    parts = [p.strip() for p in text.split("|")]

    if len(parts) < 1:
        return {
            "response_type": "ephemeral",
            "text": "Invalid format. Please use: `hypothesis | audience | channels`"
        }

    hypothesis = parts[0] if parts[0] else None
    audience = parts[1] if len(parts) > 1 and parts[1] else None
    channels = parts[2] if len(parts) > 2 and parts[2] else None

    if not hypothesis:
        return {
            "response_type": "ephemeral",
            "text": "Hypothesis is required. Example: `/gtm-add API is useful | Construction Software | Cold Email`"
        }

    # Create activity
    try:
        activity_data = ActivityCreate(
            hypothesis=hypothesis,
            audience=audience,
            channels=channels
        )
        activity = crud.create_activity(db, activity_data)

        return {
            "response_type": "in_channel",
            "text": f"✅ Created new activity #{activity.id}: {activity.hypothesis}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"✅ *Created Activity #{activity.id}*\n*Hypothesis:* {activity.hypothesis}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Audience:*\n{audience or 'Not specified'}"},
                        {"type": "mrkdwn", "text": f"*Channels:*\n{channels or 'Not specified'}"}
                    ]
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
        }
    except Exception as e:
        return {
            "response_type": "ephemeral",
            "text": f"Error creating activity: {str(e)}"
        }


def handle_gtm_update(db: Session, activity_id: str) -> Dict[str, Any]:
    """
    Handle /gtm-update command
    Opens a modal for updating an activity
    """
    if not activity_id:
        return {
            "response_type": "ephemeral",
            "text": "Please provide an activity ID. Example: `/gtm-update 1`"
        }

    try:
        activity_id_int = int(activity_id)
    except ValueError:
        return {
            "response_type": "ephemeral",
            "text": f"Invalid activity ID: `{activity_id}`. Please use a number."
        }

    activity = crud.get_activity(db, activity_id_int)

    if not activity:
        return {
            "response_type": "ephemeral",
            "text": f"Activity #{activity_id} not found."
        }

    # Return a message that the modal should be triggered
    # The actual modal will be opened by the Slack endpoint
    return {
        "response_type": "ephemeral",
        "text": f"Opening update form for activity #{activity_id}...",
        "metadata": {
            "action": "open_update_modal",
            "activity_id": activity_id_int
        }
    }
