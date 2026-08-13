# TruthGuard FastAPI Application
"""FastAPI backend for TruthGuard hallucination detection."""

import sys
import os
import json
import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.schemas import (
    VerifyRequest, GenerateAndVerifyRequest, VerificationResponse,
    GenerateAndVerifyResponse, HealthResponse, WelcomeResponse, ModuleScores
)
from core.config import settings

app = FastAPI(
    title="TruthGuard",
    description="AI Hallucination Detection Framework",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Lazy initialization: heavy ML components are NOT loaded during server startup.
pipeline = None


def get_pipeline():
    """Create the verification pipeline only when it is first needed."""
    global pipeline
    if pipeline is None:
        from core.pipeline import VerificationPipeline
        pipeline = VerificationPipeline()
    return pipeline


@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def root():
    """Serve the main frontend application."""
    index_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return WelcomeResponse(
        message="Welcome to TruthGuard - AI Hallucination Detection Framework",
        version="1.0.0",
        endpoints={
            "GET /": "Frontend application (if available)",
            "GET /health": "Health check",
            "POST /verify": "Verify an existing LLM response",
            "POST /generate-and-verify": "Generate a response and verify it",
            "POST /generate-and-verify-stream": "Generate and verify with live pipeline progress",
        },
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Lightweight health check; does not initialize the ML pipeline."""
    missing_keys = settings.validate_api_keys()
    config_summary = {
        "base_provider": settings.BASE_PROVIDER,
        "base_model": settings.BASE_MODEL,
        "judge_provider": settings.JUDGE_PROVIDER,
        "judge_model": settings.JUDGE_MODEL,
        "whitebox_enabled": settings.WHITEBOX_ENABLED,
        "hallucination_threshold": settings.HALLUCINATION_THRESHOLD,
        "missing_api_keys": missing_keys if missing_keys else None,
    }
    return HealthResponse(
        status="healthy" if not missing_keys else "degraded",
        version="1.0.0",
        config=config_summary,
    )


def validate_api_keys():
    missing_keys = settings.validate_api_keys()
    if missing_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required API keys: {', '.join(missing_keys)}"
        )


def build_verification_response(result):
    return VerificationResponse(
        prompt=result.prompt,
        response=result.response,
        truth_score=result.truth_score,
        confidence_score=result.confidence_score,
        hallucination_probability=result.hallucination_probability,
        risk_level=result.risk_level,
        explanation=result.explanation,
        grounding_explanation=result.grounding_explanation,
        module_scores=ModuleScores(
            blackbox=result.module_scores.get("blackbox"),
            whitebox=result.module_scores.get("whitebox"),
            judge=result.module_scores.get("judge"),
            grounding=result.module_scores.get("grounding"),
        ),
        evidence=result.evidence,
        sources=result.sources,
        regenerated_response=result.regenerated_response,
        regeneration_triggered=result.regeneration_triggered,
        regeneration_explanation=result.regeneration_explanation,
        veto_applied=result.veto_applied,
        veto_reason=result.veto_reason,
    )


def build_generate_response(generated_response, result):
    return GenerateAndVerifyResponse(
        generated_response=generated_response,
        prompt=result.prompt,
        response=result.response,
        truth_score=result.truth_score,
        confidence_score=result.confidence_score,
        hallucination_probability=result.hallucination_probability,
        risk_level=result.risk_level,
        explanation=result.explanation,
        grounding_explanation=result.grounding_explanation,
        module_scores=ModuleScores(
            blackbox=result.module_scores.get("blackbox"),
            whitebox=result.module_scores.get("whitebox"),
            judge=result.module_scores.get("judge"),
            grounding=result.module_scores.get("grounding"),
        ),
        evidence=result.evidence,
        sources=result.sources,
        regenerated_response=result.regenerated_response,
        regeneration_triggered=result.regeneration_triggered,
        regeneration_explanation=result.regeneration_explanation,
        veto_applied=result.veto_applied,
        veto_reason=result.veto_reason,
    )


@app.post("/verify", response_model=VerificationResponse, tags=["Verification"])
async def verify_response(request: VerifyRequest):
    try:
        validate_api_keys()
        result = await asyncio.to_thread(
            get_pipeline().verify,
            request.prompt,
            request.response,
            request.regenerate,
        )
        return build_verification_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@app.post("/generate-and-verify-stream", tags=["Verification"])
async def generate_and_verify_stream(request: GenerateAndVerifyRequest):
    async def event_stream():
        progress_queue = asyncio.Queue()

        def progress_callback(stage: str, message: str, progress: int):
            progress_queue.put_nowait({
                "type": "progress",
                "stage": stage,
                "message": message,
                "progress": progress,
            })

        try:
            validate_api_keys()
            task = asyncio.create_task(asyncio.to_thread(
                get_pipeline().generate_and_verify,
                request.prompt,
                request.regenerate,
                progress_callback,
            ))

            while not task.done():
                try:
                    event = await asyncio.wait_for(progress_queue.get(), timeout=0.25)
                    yield json.dumps(event) + "\n"
                except asyncio.TimeoutError:
                    continue

            while not progress_queue.empty():
                event = await progress_queue.get()
                yield json.dumps(event) + "\n"

            generated_response, result = await task
            final_result = {
                "generated_response": generated_response,
                "prompt": result.prompt,
                "response": result.response,
                "truth_score": result.truth_score,
                "confidence_score": result.confidence_score,
                "hallucination_probability": result.hallucination_probability,
                "risk_level": result.risk_level,
                "explanation": result.explanation,
                "grounding_explanation": result.grounding_explanation,
                "module_scores": result.module_scores,
                "evidence": result.evidence,
                "sources": result.sources,
                "regenerated_response": result.regenerated_response,
                "regeneration_triggered": result.regeneration_triggered,
                "regeneration_explanation": result.regeneration_explanation,
                "veto_applied": result.veto_applied,
                "veto_reason": result.veto_reason,
            }
            yield json.dumps({"type": "complete", "result": final_result}) + "\n"

        except HTTPException as e:
            yield json.dumps({"type": "error", "message": e.detail}) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/generate-and-verify", response_model=GenerateAndVerifyResponse, tags=["Verification"])
async def generate_and_verify(request: GenerateAndVerifyRequest):
    try:
        validate_api_keys()
        generated_response, result = await asyncio.to_thread(
            get_pipeline().generate_and_verify,
            request.prompt,
            request.regenerate,
        )
        return build_generate_response(generated_response, result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generate and verify failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)