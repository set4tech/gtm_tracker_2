import os
import json
from fastapi import FastAPI, Depends, HTTPException, Query, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    WebClient = None

from app.database import get_db, init_db
from app.schemas import ActivityResponse, ActivityCreate, ActivityUpdate
from app import crud
from app.utils import import_csv_to_db
from app.slack_handlers import (
    handle_gtm_help,
    handle_gtm_list,
    handle_gtm_view,
    handle_gtm_add,
    handle_gtm_update
)
from app.slack_utils import (
    create_update_modal,
    parse_modal_submission,
    format_activity_for_slack,
    post_new_activity_notification
)

# Initialize FastAPI app
app = FastAPI(
    title="GTM Tracker API",
    description="REST API for tracking GTM (Go-To-Market) activities",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event disabled temporarily for debugging
# @app.on_event("startup")
# async def startup_event():
#     pass

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    try:
        db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("POSTGRES_URL_NO_SSL")
        return {
            "message": "GTM Tracker API",
            "version": "1.0.0",
            "docs": "/docs",
            "database_configured": bool(db_url),
            "slack_configured": bool(os.getenv("SLACK_BOT_TOKEN")),
            "endpoints": {
                "list_activities": "GET /api/activities",
                "get_activity": "GET /api/activities/{id}",
                "create_activity": "POST /api/activities",
                "update_activity": "PUT /api/activities/{id}",
                "patch_activity": "PATCH /api/activities/{id}",
                "delete_activity": "DELETE /api/activities/{id}",
                "import_csv": "POST /api/import-csv"
            }
        }
    except Exception as e:
        return {"error": str(e), "type": str(type(e))}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("POSTGRES_URL_NO_SSL")
        return {
            "status": "healthy",
            "env_check": {
                "DATABASE_URL": "set" if db_url else "missing",
                "SLACK_BOT_TOKEN": "set" if os.getenv("SLACK_BOT_TOKEN") else "missing"
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# List all activities
@app.get("/api/activities", response_model=List[ActivityResponse])
async def list_activities(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    hypothesis: Optional[str] = Query(None, description="Filter by hypothesis (case-insensitive partial match)"),
    audience: Optional[str] = Query(None, description="Filter by audience (case-insensitive partial match)"),
    channels: Optional[str] = Query(None, description="Filter by channels (case-insensitive partial match)"),
    db: Session = Depends(get_db)
):
    """Get list of activities with optional filters"""
    activities = crud.get_activities(
        db,
        skip=skip,
        limit=limit,
        hypothesis=hypothesis,
        audience=audience,
        channels=channels
    )
    return activities

# Get single activity
@app.get("/api/activities/{activity_id}", response_model=ActivityResponse)
async def get_activity(activity_id: int, db: Session = Depends(get_db)):
    """Get a single activity by ID"""
    activity = crud.get_activity(db, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail=f"Activity with id {activity_id} not found")
    return activity

# Create new activity
@app.post("/api/activities", response_model=ActivityResponse, status_code=201)
async def create_activity(activity: ActivityCreate, db: Session = Depends(get_db)):
    """Create a new activity"""
    new_activity = crud.create_activity(db, activity)

    # Post notification to Slack
    if slack_client:
        post_new_activity_notification(new_activity, slack_client)

    return new_activity

# Update activity (full update)
@app.put("/api/activities/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: int,
    activity: ActivityCreate,
    db: Session = Depends(get_db)
):
    """Update an activity (full update - all fields required)"""
    # Convert ActivityCreate to ActivityUpdate for full update
    activity_update = ActivityUpdate(**activity.model_dump())
    updated_activity = crud.update_activity(db, activity_id, activity_update, partial=False)
    if not updated_activity:
        raise HTTPException(status_code=404, detail=f"Activity with id {activity_id} not found")
    return updated_activity

# Partial update activity
@app.patch("/api/activities/{activity_id}", response_model=ActivityResponse)
async def patch_activity(
    activity_id: int,
    activity: ActivityUpdate,
    db: Session = Depends(get_db)
):
    """Partially update an activity (only provided fields are updated)"""
    updated_activity = crud.update_activity(db, activity_id, activity, partial=True)
    if not updated_activity:
        raise HTTPException(status_code=404, detail=f"Activity with id {activity_id} not found")
    return updated_activity

# Delete activity
@app.delete("/api/activities/{activity_id}", status_code=204)
async def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    """Delete an activity"""
    deleted = crud.delete_activity(db, activity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Activity with id {activity_id} not found")
    return None

# Import CSV
@app.post("/api/import-csv")
async def import_csv(db: Session = Depends(get_db)):
    """Import activities from CSV file"""
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "activities.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="CSV file not found")

    try:
        imported = import_csv_to_db(db, csv_path)
        return {
            "message": f"Successfully imported {imported} activities",
            "count": imported
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing CSV: {str(e)}")


# ============================================================================
# SLACK INTEGRATION ENDPOINTS
# ============================================================================

# Initialize Slack client
slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
slack_client = WebClient(token=slack_bot_token) if (slack_bot_token and WebClient) else None


@app.post("/api/slack/commands")
async def slack_commands(
    request: Request,
    command: str = Form(...),
    text: str = Form(default=""),
    user_id: str = Form(...),
    response_url: str = Form(...),
    trigger_id: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Handle Slack slash commands
    """
    text = text.strip()

    # Route to appropriate handler
    if command == "/gtm-help":
        response = handle_gtm_help()
    elif command == "/gtm-list":
        response = handle_gtm_list(db, text if text else None)
    elif command == "/gtm-view":
        response = handle_gtm_view(db, text)
    elif command == "/gtm-add":
        response = handle_gtm_add(db, text)
    elif command == "/gtm-update":
        # For update, we need to open a modal
        if not text:
            return JSONResponse({
                "response_type": "ephemeral",
                "text": "Please provide an activity ID. Example: `/gtm-update 1`"
            })

        try:
            activity_id = int(text)
            activity = crud.get_activity(db, activity_id)

            if not activity:
                return JSONResponse({
                    "response_type": "ephemeral",
                    "text": f"Activity #{activity_id} not found."
                })

            # Open modal
            if slack_client and trigger_id:
                modal_view = create_update_modal(activity)
                slack_client.views_open(trigger_id=trigger_id, view=modal_view)

                return JSONResponse({
                    "response_type": "ephemeral",
                    "text": ""
                })
            else:
                return JSONResponse({
                    "response_type": "ephemeral",
                    "text": "Slack client not configured or trigger_id missing"
                })
        except ValueError:
            return JSONResponse({
                "response_type": "ephemeral",
                "text": f"Invalid activity ID: `{text}`. Please use a number."
            })
        except Exception as e:
            return JSONResponse({
                "response_type": "ephemeral",
                "text": f"Error opening modal: {str(e)}"
            })
    else:
        response = {
            "response_type": "ephemeral",
            "text": f"Unknown command: {command}. Try `/gtm-help` for available commands."
        }

    return JSONResponse(response)


@app.post("/api/slack/interactive")
async def slack_interactive(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Slack interactive components (buttons, modals, etc.)
    """
    # Parse form data
    form_data = await request.form()
    payload_str = form_data.get("payload", "{}")
    payload = json.loads(payload_str)

    interaction_type = payload.get("type")

    # Handle button clicks
    if interaction_type == "block_actions":
        actions = payload.get("actions", [])
        if not actions:
            return JSONResponse({"ok": True})

        action = actions[0]
        action_id = action.get("action_id", "")
        value = action.get("value", "")

        # View activity button
        if action_id.startswith("view_activity_"):
            activity_id = int(value)
            response = handle_gtm_view(db, str(activity_id))
            return JSONResponse(response)

        # Edit activity button
        elif action_id.startswith("edit_activity_"):
            activity_id = int(value)
            activity = crud.get_activity(db, activity_id)

            if not activity:
                return JSONResponse({
                    "response_type": "ephemeral",
                    "text": f"Activity #{activity_id} not found."
                })

            # Open modal
            if slack_client:
                trigger_id = payload.get("trigger_id")
                modal_view = create_update_modal(activity)
                slack_client.views_open(trigger_id=trigger_id, view=modal_view)

            return JSONResponse({"ok": True})

        # Delete activity button
        elif action_id.startswith("delete_activity_"):
            activity_id = int(value)
            deleted = crud.delete_activity(db, activity_id)

            if deleted:
                return JSONResponse({
                    "response_type": "ephemeral",
                    "text": f"✅ Activity #{activity_id} has been deleted.",
                    "replace_original": True
                })
            else:
                return JSONResponse({
                    "response_type": "ephemeral",
                    "text": f"❌ Activity #{activity_id} not found."
                })

    # Handle modal submissions
    elif interaction_type == "view_submission":
        view = payload.get("view", {})
        callback_id = view.get("callback_id", "")

        if callback_id.startswith("update_activity_"):
            activity_id = int(callback_id.split("_")[-1])

            # Parse form data
            form_data = parse_modal_submission(view)

            # Update activity
            activity_update = ActivityUpdate(**form_data)
            updated_activity = crud.update_activity(db, activity_id, activity_update, partial=True)

            if updated_activity:
                # Send confirmation message
                response_url = payload.get("response_url")
                return JSONResponse({
                    "response_action": "clear",
                    "text": f"✅ Activity #{activity_id} updated successfully!"
                })
            else:
                return JSONResponse({
                    "response_action": "errors",
                    "errors": {
                        "hypothesis": f"Activity #{activity_id} not found"
                    }
                })

    return JSONResponse({"ok": True})


# Events endpoint removed - not needed for slash commands


@app.get("/api/slack/oauth/callback")
async def slack_oauth_callback(code: str = Query(None), error: str = Query(None)):
    """
    Handle Slack OAuth callback
    """
    if error:
        return {"error": error}

    if not code:
        return {"error": "No authorization code provided"}

    # In a production app, you would exchange the code for an access token here
    # For now, just acknowledge the callback
    return {
        "message": "OAuth flow initiated. In a production app, the code would be exchanged for an access token.",
        "code": code
    }


# Vercel's Python runtime natively supports ASGI apps (FastAPI)
# No need for Mangum - just export the app directly
