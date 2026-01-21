# GTM Tracker API

A FastAPI-based REST API for tracking GTM (Go-To-Market) activities, deployable on Vercel with PostgreSQL database.

## Features

- Full CRUD operations for GTM activities
- Automatic CSV data import on first run
- PostgreSQL database with SQLAlchemy ORM
- OpenAPI documentation (Swagger UI)
- CORS enabled for browser access
- Serverless deployment on Vercel
- No authentication required (open API)
- **Slack integration** with slash commands and interactive components

## Project Structure

```
gtm_tracker/
├── api/
│   └── index.py          # Main FastAPI app (Vercel entry point)
├── app/
│   ├── __init__.py
│   ├── database.py       # Database connection & session
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas for validation
│   ├── crud.py           # CRUD operations
│   ├── utils.py          # Utility functions (CSV import)
│   ├── slack_handlers.py # Slack command handlers
│   └── slack_utils.py    # Slack helper functions
├── data/
│   └── activities.csv    # CSV data to import
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel deployment config
├── .env.example         # Environment variables template
├── slack-manifest.json  # Slack app manifest (HTTP mode)
├── slack-manifest.yaml  # Slack app manifest (YAML format)
├── slack-manifest-socket-mode.json  # Slack app manifest (Socket Mode)
├── SLACK_SETUP.md       # Slack setup instructions
└── README.md            # This file
```

## Database Schema

### Table: `gtm_activities`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Auto-incrementing primary key |
| `hypothesis` | String | GTM hypothesis (required) |
| `audience` | String | Target audience |
| `channels` | String | Marketing channels |
| `description` | Text | Detailed description |
| `list_size` | Integer | Size of contact list |
| `meetings_booked` | Integer | Number of meetings booked |
| `start_date` | Date | Start date of activity |
| `end_date` | Date | End date of activity |
| `est_weekly_hrs` | Float | Estimated weekly hours |
| `created_at` | DateTime | Auto-generated timestamp |
| `updated_at` | DateTime | Auto-updated timestamp |

## API Endpoints

### Root & Health
- `GET /` - API information and endpoint list
- `GET /health` - Health check

### Activities CRUD
- `GET /api/activities` - List all activities
  - Query parameters: `skip`, `limit`, `hypothesis`, `audience`, `channels`
- `GET /api/activities/{id}` - Get single activity by ID
- `POST /api/activities` - Create new activity
- `PUT /api/activities/{id}` - Update activity (full update)
- `PATCH /api/activities/{id}` - Partial update activity
- `DELETE /api/activities/{id}` - Delete activity

### Data Import
- `POST /api/import-csv` - Import activities from CSV file

## Local Development

### Prerequisites

- Python 3.9 or higher
- PostgreSQL (or use SQLite for testing)
- pip (Python package manager)

### Setup

1. Clone or navigate to the project directory:
```bash
cd gtm_tracker
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` and set your database URL:
```
DATABASE_URL=postgresql://user:password@localhost:5432/gtm_tracker
# Or for SQLite testing:
DATABASE_URL=sqlite:///./gtm_tracker.db
```

5. Run the application:
```bash
uvicorn api.index:app --reload
```

The API will be available at `http://localhost:8000`

6. Access interactive documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Testing Endpoints

List all activities:
```bash
curl http://localhost:8000/api/activities
```

Get single activity:
```bash
curl http://localhost:8000/api/activities/1
```

Create new activity:
```bash
curl -X POST http://localhost:8000/api/activities \
  -H "Content-Type: application/json" \
  -d '{
    "hypothesis": "Test hypothesis",
    "audience": "Test audience",
    "channels": "Email, LinkedIn"
  }'
```

Update activity:
```bash
curl -X PATCH http://localhost:8000/api/activities/1 \
  -H "Content-Type: application/json" \
  -d '{"meetings_booked": 5}'
```

Delete activity:
```bash
curl -X DELETE http://localhost:8000/api/activities/1
```

## Vercel Deployment

### Prerequisites

- Vercel account
- Vercel CLI: `npm i -g vercel`

### Deployment Steps

1. Navigate to project directory:
```bash
cd gtm_tracker
```

2. Login to Vercel:
```bash
vercel login
```

3. Link to Vercel project:
```bash
vercel link
```

4. Create Vercel Postgres database:
   - Go to your Vercel dashboard
   - Select your project
   - Go to "Storage" tab
   - Create a new Postgres database
   - Link it to your project

5. Pull environment variables:
```bash
vercel env pull
```

This will create a `.env` file with your `DATABASE_URL`

6. Deploy to production:
```bash
vercel --prod
```

7. Your API will be live at: `https://your-project.vercel.app`

### Environment Variables in Vercel

The following environment variables are automatically set when you link Vercel Postgres:
- `DATABASE_URL` - PostgreSQL connection string

You can also set them manually in the Vercel dashboard:
1. Go to Project Settings
2. Navigate to Environment Variables
3. Add `DATABASE_URL` with your database connection string

## CSV Data Import

The API automatically imports data from `data/activities.csv` on first run when the database is empty.

CSV format expected:
```csv
Hypothesis,Audience,Channels,Description/Activities,List size,Meetings booked,T1 Date or Start,End Date,Est weekly hrs
```

To manually import CSV data:
```bash
curl -X POST http://localhost:8000/api/import-csv
```

## Slack Integration

GTM Tracker includes full Slack integration, allowing you to manage activities directly from Slack.

### Automatic Notifications

When a new GTM activity is created (via API or Slack commands), an automatic notification is posted to your configured Slack channel with:
- Activity details (hypothesis, audience, channels, list size)
- A "View Details" button for quick access
- Defaults to posting in the `#all-set4` channel

To configure the notification channel, set the `SLACK_NOTIFICATION_CHANNEL` environment variable:
```bash
SLACK_NOTIFICATION_CHANNEL=all-set4
```

### Setup Slack Integration

1. **Create Slack App:**
   - See `SLACK_SETUP.md` for detailed instructions
   - Use `slack-manifest-socket-mode.json` for quick setup (no URLs needed)
   - Or use `slack-manifest.json` / `slack-manifest.yaml` with your Vercel URL

2. **Get Credentials:**
   - Go to https://api.slack.com/apps
   - Select your app
   - **Bot Token:** Settings > Install App (`xoxb-...`)
   - **Signing Secret:** Settings > Basic Information

3. **Configure Environment Variables:**
   ```bash
   # Add to .env or Vercel environment variables
   SLACK_BOT_TOKEN=xoxb-your-bot-token
   SLACK_SIGNING_SECRET=your-signing-secret
   SLACK_NOTIFICATION_CHANNEL=all-set4  # Optional, defaults to all-set4
   ```

4. **Set Request URLs** (if using HTTP mode):
   - Commands: `https://your-app.vercel.app/api/slack/commands`
   - Interactivity: `https://your-app.vercel.app/api/slack/interactive`
   - Events: `https://your-app.vercel.app/api/slack/events`

### Slack Commands

Once configured, use these commands in Slack:

**`/gtm-list [filter]`**
- List recent GTM activities with optional filter
- Examples:
  - `/gtm-list` - Show all recent activities
  - `/gtm-list LinkedIn` - Filter by "LinkedIn"

**`/gtm-add hypothesis | audience | channels`**
- Quick add new activity
- Example: `/gtm-add API is useful | Construction Software | Cold Email`

**`/gtm-view [id]`**
- View detailed information about an activity
- Example: `/gtm-view 1`

**`/gtm-update [id]`**
- Update an activity (opens interactive form)
- Example: `/gtm-update 1`

**`/gtm-help`**
- Show help and available commands

### Interactive Features

- **View Details Button:** Click on any activity to see full details
- **Edit Button:** Opens a modal form to update activity fields
- **Delete Button:** Remove an activity (with confirmation)
- **@mention:** Mention the bot anywhere to get help
- **Direct Messages:** DM the bot for help

### Slack Endpoints

The following Slack-specific endpoints are available:

- `POST /api/slack/commands` - Handle slash commands
- `POST /api/slack/interactive` - Handle buttons and modals
- `POST /api/slack/events` - Handle mentions and DMs
- `GET /api/slack/oauth/callback` - OAuth callback

## API Response Examples

### List Activities Response
```json
[
  {
    "id": 1,
    "hypothesis": "City growing visualizations would be engaging",
    "audience": "Architects, Cities",
    "channels": "LinkedIn, TikTok",
    "description": "Post city growth visualisations on linkedIn",
    "list_size": null,
    "meetings_booked": null,
    "start_date": null,
    "end_date": null,
    "est_weekly_hrs": null,
    "created_at": "2024-01-17T10:00:00Z",
    "updated_at": "2024-01-17T10:00:00Z"
  }
]
```

### Error Response
```json
{
  "detail": "Activity with id 999 not found"
}
```

## Development Notes

### Database Connection Pooling
The app uses SQLAlchemy's `NullPool` for serverless compatibility, which creates a new connection for each request. This is necessary for Vercel's serverless functions.

### Date Parsing
The CSV import utility handles multiple date formats:
- `YYYY-MM-DD` (2024-01-15)
- `MM/DD/YYYY` (01/15/2024)
- `Month DD, YYYY` (January 15, 2024)
- And more...

### CORS Configuration
CORS is enabled for all origins (`*`) to allow browser-based API access. For production, consider restricting this to specific domains.

## Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` is correctly set in `.env`
- For Vercel Postgres, ensure the connection string uses `postgresql://` (not `postgres://`)
- Check that your database server is running

### CSV Import Issues
- Verify CSV file exists at `data/activities.csv`
- Check CSV column names match expected format
- Ensure CSV is UTF-8 encoded

### Vercel Deployment Issues
- Run `vercel env pull` to sync environment variables
- Check Vercel logs: `vercel logs`
- Verify database is linked to project in Vercel dashboard

### Slack Integration Issues
- **Commands not responding:** Verify `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` are set in Vercel
- **URL verification failed:** Ensure your Vercel app is deployed and accessible
- **Signature verification failed:** Check that `SLACK_SIGNING_SECRET` matches the value in Slack app settings
- **Modal not opening:** Ensure Slack bot token has correct scopes and `interactivity` is enabled
- **Test locally:** For local development, use Socket Mode or a tunneling tool like ngrok

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
