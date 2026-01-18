import os
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

# Import data on startup
@app.on_event("startup")
async def startup_event():
    """Load initial data from CSV on startup"""
    from app.import_data import import_csv_data
    from app.storage import storage

    # Only import if storage is empty
    if len(storage.activities) == 0:
        try:
            count = import_csv_data()
            print(f"✓ Imported {count} GTM activities from CSV")
        except Exception as e:
            print(f"Warning: Could not import CSV data: {e}")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "GTM Tracker API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# ============================================================================
# SLACK INTEGRATION
# ============================================================================

from app.slack_handlers import (
    handle_gtm_help,
    handle_gtm_list,
    handle_gtm_view,
    handle_gtm_add,
    handle_gtm_update
)
from app.slack_utils import verify_slack_signature


@app.post("/api/slack/commands")
async def slack_commands(request: Request):
    """
    Handle Slack slash commands
    """
    try:
        # Read body for signature verification BEFORE parsing form
        body = await request.body()

        # Verify Slack signature
        signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        if signing_secret:
            timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
            signature = request.headers.get("X-Slack-Signature", "")

            if not verify_slack_signature(signing_secret, timestamp, body, signature):
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Now parse form data manually
        form_data = {}
        for item in body.decode('utf-8').split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                from urllib.parse import unquote_plus
                form_data[key] = unquote_plus(value)

        command = form_data.get('command', '')
        text = form_data.get('text', '').strip()

        # Route to appropriate handler
        if command == "/gtm-help":
            response = handle_gtm_help()
        elif command == "/gtm-list":
            response = handle_gtm_list(text if text else None)
        elif command == "/gtm-view":
            response = handle_gtm_view(text)
        elif command == "/gtm-add":
            response = handle_gtm_add(text)
        elif command == "/gtm-update":
            response = handle_gtm_update(text)
        else:
            response = {
                "response_type": "ephemeral",
                "text": f"Unknown command: {command}. Try `/gtm-help` for available commands."
            }

        return JSONResponse(response)
    except Exception as e:
        # Return error to Slack
        import traceback
        error_details = traceback.format_exc()
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"❌ Error: {str(e)}\n```{error_details[:500]}```"
        })


@app.post("/api/slack/interactive")
async def slack_interactive(request: Request):
    """
    Handle Slack interactive components (buttons, modals, etc.)
    """
    import json

    # Verify Slack signature
    signing_secret = os.getenv("SLACK_SIGNING_SECRET")
    if signing_secret:
        body = await request.body()
        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        signature = request.headers.get("X-Slack-Signature", "")

        if not verify_slack_signature(signing_secret, timestamp, body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

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
            response = handle_gtm_view(value)
            return JSONResponse(response)

        # Share activity button
        elif action_id.startswith("share_activity_"):
            response = handle_gtm_view(value, public=True)
            return JSONResponse(response)

    return JSONResponse({"ok": True})
