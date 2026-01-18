# Slack App Setup Guide

Follow these steps to set up the GTM Tracker Slack app and integrate it with your Vercel deployment.

## Step 1: Create Your Slack App

1. **Go to Slack API:** https://api.slack.com/apps

2. **Click "Create New App"**

3. **Choose "From an app manifest"**

4. **Select your Workspace** (choose the workspace where you want to install the app)

5. **Choose YAML format** and paste the contents from `slack-manifest.yaml`

6. **IMPORTANT:** Before submitting, replace `YOUR_VERCEL_URL` in the manifest with your actual Vercel URL:
   ```
   https://your-actual-url.vercel.app
   ```

7. **Click "Next"** → Review the configuration → **Click "Create"**

## Step 2: Configure Request URLs

After creating the app, you need to set up the request URLs:

### A. Slash Commands Request URL

1. Go to **"Slash Commands"** in the left sidebar
2. For each command (`/gtm-help`, `/gtm-list`, `/gtm-view`, `/gtm-add`, `/gtm-update`):
   - Click the command name
   - Set **Request URL** to: `https://YOUR_VERCEL_URL/api/slack/commands`
   - Click "Save"

### B. Interactivity Request URL

1. Go to **"Interactivity & Shortcuts"** in the left sidebar
2. Toggle **"Interactivity"** to ON
3. Set **Request URL** to: `https://YOUR_VERCEL_URL/api/slack/interactive`
4. Click "Save Changes"

## Step 3: Get Your Tokens

### Bot Token (SLACK_BOT_TOKEN)

1. Go to **"OAuth & Permissions"** in the left sidebar
2. Click **"Install to Workspace"**
3. Click **"Allow"**
4. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)
   - Save this - you'll need it for Vercel environment variables

### Signing Secret (SLACK_SIGNING_SECRET)

1. Go to **"Basic Information"** in the left sidebar
2. Scroll down to **"App Credentials"**
3. Copy the **"Signing Secret"**
   - Save this - you'll need it for Vercel environment variables

## Step 4: Add Environment Variables to Vercel

1. Go to your Vercel project: https://vercel.com/set4/gtm_tracker_2/settings/environment-variables

2. Add the following environment variables:

   | Name | Value | Environment |
   |------|-------|-------------|
   | `SLACK_BOT_TOKEN` | `xoxb-...` (from Step 3) | Production, Preview, Development |
   | `SLACK_SIGNING_SECRET` | Your signing secret | Production, Preview, Development |

3. Click "Save" for each variable

4. **Redeploy your app** to apply the environment variables:
   - Go to: https://vercel.com/set4/gtm_tracker_2
   - Click the three dots (...) on the latest deployment
   - Click "Redeploy"

## Step 5: Test the Integration

Once redeployed, test in your Slack workspace:

1. Go to any channel in your Slack workspace
2. Type `/gtm-help` and press Enter
3. You should see a list of available commands!

## Available Commands

- `/gtm-help` - Show all available commands
- `/gtm-list` - List recent GTM activities
- `/gtm-view [id]` - View details of a specific activity
- `/gtm-add hypothesis | audience | channels` - Add a new activity
- `/gtm-update [id]` - Update an existing activity

## Troubleshooting

### Commands not showing up
- Make sure you've installed the app to your workspace (Step 3)
- Refresh Slack (Cmd/Ctrl + R)

### "dispatch_failed" error
- Check that your Request URLs are correct (Step 2)
- Make sure your Vercel deployment is live and accessible

### "invalid_auth" error
- Verify your `SLACK_BOT_TOKEN` is correct in Vercel environment variables
- Make sure you redeployed after adding the variables

### "invalid_signature" error
- Verify your `SLACK_SIGNING_SECRET` is correct in Vercel environment variables
- Make sure you redeployed after adding the variables

## Next Steps

Once Slack is working:
1. Set up PostgreSQL database (Vercel Postgres or Neon)
2. Add database models and CRUD operations
3. Connect Slack commands to database operations
4. Test full workflow!
