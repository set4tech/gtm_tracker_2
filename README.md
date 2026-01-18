# GTM Tracker API

A FastAPI-based REST API for tracking Go-To-Market (GTM) activities.

## Features

- FastAPI framework for high performance
- Automatic API documentation (Swagger UI)
- CORS enabled for web clients
- Ready for Vercel deployment

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the development server:
```bash
uvicorn api.index:app --reload
```

3. Access the API:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Deployment

This project is configured for easy deployment on Vercel.

### Deploy to Vercel

1. Push your code to GitHub
2. Import the repository in Vercel
3. Vercel will automatically detect the FastAPI app
4. Deploy!

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## Project Structure

```
gtm_tracker_2/
├── api/
│   └── index.py          # Main FastAPI application
├── app/                  # Application modules (future)
├── data/                 # Data files (future)
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## License

MIT
