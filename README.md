# TruthGuard - AI Hallucination Detection System

A lightweight, modern web application for detecting AI hallucinations and verifying response accuracy.

## Features

- **Multi-signal Detection**: Combines black-box consistency, external grounding, LLM-as-a-judge, and score fusion
- **Modern UI**: Clean, responsive interface inspired by modern design systems
- **Lightweight**: Optimized for low memory usage (<100MB RAM)
- **Real-time Progress**: Live pipeline visualization during verification
- **Evidence-based**: Shows external sources and evidence for transparency

## Architecture

### Frontend
- Single-page HTML/CSS/JS application (no framework dependencies)
- Modern dark theme with CSS variables
- Responsive design for all screen sizes
- Direct API integration with streaming support

### Backend
- FastAPI for high-performance API
- Lazy-loaded ML components (only loaded when needed)
- Streaming endpoints for real-time progress updates
- Minimal dependencies

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your API keys:

```env
OPENROUTER_API_KEY=your_openrouter_key
GOOGLE_API_KEY=your_google_key
SEARCH_PROVIDER=duckduckgo
BASE_PROVIDER=openrouter
BASE_MODEL=qwen/qwen2.5-72b-instruct
JUDGE_PROVIDER=openrouter
JUDGE_MODEL=anthropic/claude-3.5-sonnet
```

### 3. Run the Application

```bash
# Start the FastAPI server (includes frontend)
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000` in your browser.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Frontend application |
| `/health` | GET | Health check |
| `/verify` | POST | Verify an existing AI response |
| `/generate-and-verify` | POST | Generate and verify a response |
| `/generate-and-verify-stream` | POST | Generate and verify with live progress |

## Memory Optimization

This version is optimized for deployment on platforms with limited memory (e.g., Render free tier):

1. **Removed heavy dependencies**: No sentence-transformers, langchain, or streamlit
2. **Lazy loading**: ML models only load when first request arrives
3. **Static frontend**: No server-side rendering overhead
4. **Minimal runtime**: ~50-80MB RAM usage

## Deployment on Render

1. Create a new Web Service
2. Connect your repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables for API keys

## Project Structure

```
/workspace
├── api/
│   ├── main.py          # FastAPI application
│   └── schemas.py       # Pydantic models
├── core/
│   ├── pipeline.py      # Main verification pipeline
│   ├── blackbox.py      # Consistency checking
│   ├── grounding.py     # External evidence verification
│   ├── judge.py         # LLM-as-a-judge module
│   ├── fusion.py        # Score combination
│   ├── regeneration.py  # Safe response regeneration
│   ├── search.py        # Web search provider
│   ├── llm.py           # LLM providers
│   └── config.py        # Configuration
├── static/
│   └── index.html       # Frontend application
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## License

MIT License
