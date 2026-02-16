"""Triage AI - FastAPI Application

A multi-agent system for patient triage using the Manchester Triage Protocol.
"""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()  # Load .env file

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from chat.questions import (
    get_question,
    get_total_questions,
    get_first_question,
    get_question_text,
    get_welcome_message,
    LANGUAGE_OPTIONS,
)
from models.schemas import (
    ChatMessage,
    ChatResponse,
    ProcessRequest,
    ProcessResponse,
    ResultResponse,
    SessionData,
    TriageResult,
)
from db.vector_store import VectorStore
from agents.anamnesis import AnamnesisAgent
from agents.triage import TriageAgent
from agents.routing import RoutingAgent


# =============================================================================
# In-Memory Session Storage (MVP - replace with Redis for production)
# =============================================================================

sessions: dict[str, SessionData] = {}
job_results: dict[str, TriageResult | None] = {}


def cleanup_old_sessions():
    """Remove sessions older than 24 hours."""
    cutoff = datetime.utcnow() - timedelta(hours=24)
    expired = [
        sid for sid, data in sessions.items()
        if data.created_at < cutoff
    ]
    for sid in expired:
        del sessions[sid]


# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup: Initialize vector store
    print("Initializing ChromaDB vector store...")
    app.state.vector_store = VectorStore()

    # Initialize agents
    app.state.anamnesis_agent = AnamnesisAgent()
    app.state.triage_agent = TriageAgent(app.state.vector_store)
    app.state.routing_agent = RoutingAgent(app.state.vector_store)

    print("Triage AI ready!")

    yield

    # Shutdown: Cleanup
    print("Shutting down Triage AI...")
    sessions.clear()
    job_results.clear()


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Triage AI",
    description="Multi-agent patient triage system using Manchester Triage Protocol",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "Triage AI", "version": "2.0.0"}


@app.post("/api/session")
async def create_session() -> dict:
    """Create a new chat session.

    Returns:
        session_id: Unique session identifier
        language_options: Available language options
        is_language_selection: Whether this is the language selection step
    """
    session_id = str(uuid.uuid4())
    sessions[session_id] = SessionData(session_id=session_id)

    return {
        "session_id": session_id,
        "language_options": LANGUAGE_OPTIONS,
        "is_language_selection": True,
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage) -> ChatResponse:
    """Handle chat message and return next question.

    Args:
        message: The user's message containing session_id and answer

    Returns:
        ChatResponse with next question or completion status
    """
    session = sessions.get(message.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.is_complete:
        raise HTTPException(status_code=400, detail="Session already complete")

    # Store the answer
    session.answers[session.current_question] = message.message

    # Handle language selection (question 0)
    if session.current_question == 0:
        # Validate and store language preference
        language_code = message.message.strip()
        if language_code not in LANGUAGE_OPTIONS:
            raise HTTPException(status_code=400, detail="Invalid language selection")

        session.language = language_code
        session.current_question = 1

        # Return first actual question in selected language
        next_question_text = get_question_text(1, session.language)
        return ChatResponse(
            session_id=message.session_id,
            question_number=1,
            next_question=next_question_text,
            is_complete=False,
        )

    # Move to next question
    session.current_question += 1

    # Check if all questions answered
    total_questions = get_total_questions()

    if session.current_question > total_questions:
        session.is_complete = True
        return ChatResponse(
            session_id=message.session_id,
            question_number=total_questions,
            next_question=None,
            is_complete=True,
        )

    # Get next question in user's language
    next_question_text = get_question_text(session.current_question, session.language)

    return ChatResponse(
        session_id=message.session_id,
        question_number=session.current_question,
        next_question=next_question_text,
        is_complete=False,
    )


@app.post("/api/process", response_model=ProcessResponse)
async def process_triage(request: ProcessRequest) -> ProcessResponse:
    """Process completed anamnesis through triage and routing agents.

    Args:
        request: Contains the session_id to process

    Returns:
        ProcessResponse with job_id for polling results
    """
    session = sessions.get(request.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.is_complete:
        raise HTTPException(
            status_code=400,
            detail="Anamnesis not complete. Please answer all questions first."
        )

    # Generate job ID
    job_id = str(uuid.uuid4())
    job_results[job_id] = None  # Placeholder

    # Process through agents (in production, this would be async/background)
    try:
        # Agent 1: Structure the anamnesis
        anamnesis = await app.state.anamnesis_agent.process(session.answers, session.language)
        session.anamnesis = anamnesis

        # Agent 2: Classify with triage
        classification = await app.state.triage_agent.classify(anamnesis)
        session.classification = classification

        # Agent 3: Route to department
        routing = await app.state.routing_agent.route(anamnesis, classification)
        session.routing = routing

        # Create final result
        result = TriageResult(
            session_id=request.session_id,
            anamnesis=anamnesis,
            classification=classification,
            routing=routing,
        )

        job_results[job_id] = result

    except Exception as e:
        # Store error for retrieval
        job_results[job_id] = None
        raise HTTPException(status_code=500, detail=str(e))

    return ProcessResponse(
        status="completed",
        job_id=job_id,
    )


@app.get("/api/result/{job_id}", response_model=ResultResponse)
async def get_result(job_id: str) -> ResultResponse:
    """Get the result of a triage processing job.

    Args:
        job_id: The job identifier from /api/process

    Returns:
        ResultResponse with triage result or processing status
    """
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail="Job not found")

    result = job_results.get(job_id)

    if result is None:
        return ResultResponse(status="processing", result=None)

    return ResultResponse(status="completed", result=result)


@app.get("/api/session/{session_id}")
async def get_session(session_id: str) -> dict:
    """Get current session state (for debugging/recovery)."""
    session = sessions.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.session_id,
        "current_question": session.current_question,
        "is_complete": session.is_complete,
        "answers_count": len(session.answers),
        "language": session.language,
    }


# =============================================================================
# Static Files (Frontend)
# =============================================================================

# Mount static files last to avoid route conflicts
app.mount("/", StaticFiles(directory="static", html=True), name="static")


# =============================================================================
# Development Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
