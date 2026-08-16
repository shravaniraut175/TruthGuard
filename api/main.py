# TruthGuard FastAPI Application
"""FastAPI backend for TruthGuard hallucination detection."""

import sys
import os

import json
import asyncio

from fastapi.responses import StreamingResponse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    VerifyRequest,
    GenerateAndVerifyRequest,
    VerificationResponse,
    GenerateAndVerifyResponse,
    HealthResponse,
    WelcomeResponse,
    ModuleScores
)
from core.pipeline import VerificationPipeline
from core.config import settings

# Create FastAPI app
app = FastAPI(
    title="TruthGuard",
    description="AI Hallucination Detection Framework",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline
pipeline = VerificationPipeline()


@app.get("/", response_model=WelcomeResponse, tags=["Root"])
async def root():
    """Root endpoint with welcome message and API information."""
    return WelcomeResponse(
        message="Welcome to TruthGuard - AI Hallucination Detection Framework",
        version="1.0.0",
        endpoints={
            "GET /": "This welcome message",
            "GET /health": "Health check",
            "POST /verify": "Verify an existing LLM response",
            "POST /generate-and-verify": "Generate a response and verify it"
        }
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    # Check for missing API keys
    missing_keys = settings.validate_api_keys()

    config_summary = {
        "base_provider": settings.BASE_PROVIDER,
        "base_model": settings.BASE_MODEL,
        "judge_provider": settings.JUDGE_PROVIDER,
        "judge_model": settings.JUDGE_MODEL,
        "whitebox_enabled": settings.WHITEBOX_ENABLED,
        "hallucination_threshold": settings.HALLUCINATION_THRESHOLD,
        "missing_api_keys": missing_keys if missing_keys else None
    }

    status = "healthy" if not missing_keys else "degraded"

    return HealthResponse(
        status=status,
        version="1.0.0",
        config=config_summary
    )


@app.post("/verify", response_model=VerificationResponse, tags=["Verification"])
async def verify_response(request: VerifyRequest):
    """
    Verify an existing LLM response.

    Accepts a user prompt and an LLM-generated response, then verifies
    whether the response is likely hallucinated.

    Returns:
        VerificationResult with truth score, confidence, hallucination probability,
        risk level, explanations, module scores, evidence, and optional regenerated response.
    """
    try:
        # Validate API keys before processing
        missing_keys = settings.validate_api_keys()
        if missing_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required API keys: {', '.join(missing_keys)}"
            )

        # Run verification pipeline
        result = pipeline.verify(
            prompt=request.prompt,
            response=request.response,
            regenerate=request.regenerate
        )

        # Convert to response schema
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
                grounding=result.module_scores.get("grounding")
            ),
            evidence=result.evidence,
            sources=result.sources,
            regenerated_response=result.regenerated_response,
            regeneration_triggered=result.regeneration_triggered,
            regeneration_explanation=result.regeneration_explanation,
            veto_applied=result.veto_applied,
            veto_reason=result.veto_reason
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}"
        )

@app.post("/generate-and-verify-stream", tags=["Verification"])
async def generate_and_verify_stream(request: GenerateAndVerifyRequest):

    async def event_stream():
        progress_queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def progress_callback(stage: str, message: str, progress: int):
            event = {
                "type": "progress",
                "stage": stage,
                "message": message,
                "progress": progress,
            }

            # Thread-safe communication from pipeline worker → async loop
            loop.call_soon_threadsafe(
                progress_queue.put_nowait,
                event
            )

        task = asyncio.create_task(
            asyncio.to_thread(
                pipeline.generate_and_verify,
                request.prompt,
                request.regenerate,
                progress_callback,
            )
        )

        # Keep the HTTP stream alive while the pipeline is running.
        while not task.done():
            try:
                event = await asyncio.wait_for(
                    progress_queue.get(),
                    timeout=5.0,
                )

                yield json.dumps(event) + "\n"

            except asyncio.TimeoutError:
                # Heartbeat prevents Render/proxies from considering
                # the streaming connection idle.
                yield json.dumps({
                    "type": "heartbeat"
                }) + "\n"

        # Send any progress events that arrived just before completion.
        while not progress_queue.empty():
            event = await progress_queue.get()
            yield json.dumps(event) + "\n"

        try:
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

            yield json.dumps({
                "type": "complete",
                "result": final_result,
            }) + "\n"

        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": str(e),
            }) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
@app.post("/generate-and-verify", response_model=GenerateAndVerifyResponse, tags=["Verification"])
async def generate_and_verify(request: GenerateAndVerifyRequest):
    """
    Generate a response using the configured base model and verify it.

    This endpoint first generates a response using the base model,
    then runs the complete verification pipeline on it.

    Returns:
        GenerateAndVerifyResponse with generated response and all verification metrics.
    """
    try:
        # Validate API keys before processing
        missing_keys = settings.validate_api_keys()
        if missing_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required API keys: {', '.join(missing_keys)}"
            )

        # Generate and verify
        generated_response, result = pipeline.generate_and_verify(
            prompt=request.prompt,
            regenerate=request.regenerate
        )

        # Convert to response schema
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
                grounding=result.module_scores.get("grounding")
            ),
            evidence=result.evidence,
            sources=result.sources,
            regenerated_response=result.regenerated_response,
            regeneration_triggered=result.regeneration_triggered,
            regeneration_explanation=result.regeneration_explanation,
            veto_applied=result.veto_applied,
            veto_reason=result.veto_reason
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Generate and verify failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
