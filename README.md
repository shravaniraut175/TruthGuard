# TruthGuard - AI Hallucination Detection Framework

## Overview

TruthGuard is an AI hallucination detection framework for Large Language Model responses. It accepts a user prompt and an LLM-generated response, then verifies whether the response is likely hallucinated before presenting it to the user.

## Features

- **Heterogeneous Model Ensembling**: Configure base and judge models separately from different providers
- **External Search Grounding**: Verify responses against web evidence using DuckDuckGo search
- **Multi-Detector Fusion**: Combines black-box consistency, white-box token confidence, LLM-as-a-Judge, and external grounding scores
- **Weighted Score Fusion**: Normalized weights with automatic adjustment when modules are disabled
- **Confidence-Based Regeneration**: Automatically regenerates safer responses when hallucination probability is high
- **Risk Assessment**: Returns truth score, confidence score, hallucination probability, risk level, and detailed explanations

## Project Structure

```
TruthGuard/
│
├── app.py                 # Streamlit frontend
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env.example          # Environment variable template
├── .gitignore
│
├── api/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   └── schemas.py        # Pydantic schemas
│
└── core/
    ├── __init__.py
    ├── config.py         # Configuration management
    ├── utils.py          # Utility functions
    ├── llm.py            # LLM provider abstraction
    ├── search.py         # Web search functionality
    ├── embeddings.py     # Semantic similarity
    ├── blackbox.py       # Black-box consistency detector
    ├── whitebox.py       # White-box token confidence detector
    ├── grounding.py      # External grounding verification
    ├── judge.py          # LLM-as-a-Judge evaluation
    ├── fusion.py         # Score fusion logic
    ├── regeneration.py   # Response regeneration
    └── pipeline.py       # Main verification pipeline
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd TruthGuard
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

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Configuration

Edit `.env` to configure:

### API Keys (Required)
- `OPENROUTER_API_KEY`: For OpenRouter access
- `GOOGLE_API_KEY`: For Google Gemini
- `OPENAI_API_KEY`: For OpenAI

### Model Configuration
- `BASE_PROVIDER`: Provider for generating responses (openrouter, google, openai)
- `BASE_MODEL`: Model name for base generation
- `JUDGE_PROVIDER`: Provider for judging (can be different from base)
- `JUDGE_MODEL`: Model name for judging

### Search Configuration
- `SEARCH_PROVIDER`: Currently supports duckduckgo
- `MAX_SEARCH_RESULTS`: Number of search results (default: 5)
- `NUM_BLACKBOX_SAMPLES`: Samples for consistency check (default: 3)

### White-box Configuration (Optional)
- `WHITEBOX_ENABLED`: Enable/disable white-box scoring (default: false)
- `WHITEBOX_MODEL`: Hugging Face model for token-level analysis

### Thresholds and Weights
- `HALLUCINATION_THRESHOLD`: Threshold for triggering regeneration (default: 0.60)
- `BLACKBOX_WEIGHT`, `WHITEBOX_WEIGHT`, `JUDGE_WEIGHT`, `GROUNDING_WEIGHT`: Score weights

## Usage

### Running the Backend

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running the Frontend

```bash
streamlit run app.py
```

### API Endpoints

#### GET /
Returns welcome message and API information.

#### GET /health
Health check endpoint.

#### POST /verify
Verify an existing response:
```json
{
  "prompt": "What is the capital of France?",
  "response": "The capital of France is Paris.",
  "regenerate": false
}
```

#### POST /generate-and-verify
Generate a response and verify it:
```json
{
  "prompt": "What is quantum entanglement?",
  "regenerate": true
}
```

### Response Format

```json
{
  "truth_score": 0.92,
  "confidence_score": 0.88,
  "hallucination_probability": 0.08,
  "risk_level": "low",
  "explanation": "Response is consistent across multiple samples...",
  "grounding_explanation": "External evidence supports the claims...",
  "module_scores": {
    "blackbox": 0.95,
    "whitebox": null,
    "judge": 0.90,
    "grounding": 0.92
  },
  "evidence": [...],
  "sources": [...],
  "regenerated_response": null
}
```

## How It Works

### 1. Black-box Consistency Detector
Generates multiple samples from the base model at different temperatures and measures semantic similarity between the original response and samples using sentence transformers.

### 2. White-box Token Confidence (Optional)
Uses a local Hugging Face model to calculate mean token probability for response tokens. Disabled by default to avoid heavy dependencies.

### 3. LLM-as-a-Judge
Uses a configurable judge model (can be from a different provider) to evaluate factual accuracy, grounding, coherence, and provide explanations.

### 4. External Grounding
Searches the web for evidence related to the prompt and response, then uses the judge model to determine if evidence supports, contradicts, or is insufficient.

### 5. Score Fusion
Combines all scores with weighted averaging, applies veto mechanisms:
- **Grounding Veto**: If external evidence strongly contradicts, truth score is reduced
- **Judge Veto**: If judge rates factual accuracy very low, truth score is reduced

### 6. Regeneration
If hallucination probability exceeds the threshold, generates a safer response that acknowledges uncertainty and cites available evidence.

## Risk Levels

- **low**: Hallucination probability < 0.30
- **medium**: Hallucination probability 0.30-0.50
- **high**: Hallucination probability 0.50-0.70
- **critical**: Hallucination probability >= 0.70

## License

MIT License
