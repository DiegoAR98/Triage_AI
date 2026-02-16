from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class TriageColor(str, Enum):
    """Manchester Triage Protocol colors."""
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    BLUE = "BLUE"


class Priority(str, Enum):
    """Priority levels corresponding to triage colors."""
    EMERGENCY = "EMERGENCY"  # RED
    URGENT = "URGENT"        # YELLOW
    STANDARD = "STANDARD"    # GREEN
    LOW = "LOW"              # BLUE


class Urgency(str, Enum):
    """Urgency levels for routing."""
    IMMEDIATE = "Immediate"
    WITHIN_30_MIN = "Within 30 min"
    WITHIN_1_HOUR = "Within 1 hour"
    STANDARD = "Standard"


# =============================================================================
# Core Data Models (from SRS Section 5)
# =============================================================================

class Anamnesis(BaseModel):
    """Structured patient anamnesis data collected during intake."""

    # Patient Demographics
    patient_name: str = Field(
        ...,
        description="Patient's full name"
    )
    date_of_birth: str = Field(
        ...,
        description="Patient's date of birth"
    )
    phone_number: str | None = Field(
        default=None,
        description="Patient's contact phone number"
    )
    emergency_contact_name: str | None = Field(
        default=None,
        description="Emergency contact person's name"
    )
    emergency_contact_phone: str | None = Field(
        default=None,
        description="Emergency contact phone number"
    )

    # Chief Complaint
    chief_complaint: str = Field(
        ...,
        description="Main reason for visit"
    )
    onset: str = Field(
        ...,
        description="When symptoms started"
    )
    duration: str | None = Field(
        default=None,
        description="How long symptoms lasted"
    )
    pain_scale: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Severity on 1-10 scale"
    )
    pain_type: str | None = Field(
        default=None,
        description="Type of pain: sharp, dull, pressure, burning"
    )
    location: str | None = Field(
        default=None,
        description="Body location of symptoms"
    )
    radiation: str | None = Field(
        default=None,
        description="Where pain spreads to"
    )
    associated_symptoms: list[str] = Field(
        default_factory=list,
        description="Other symptoms"
    )
    medical_history: list[str] = Field(
        default_factory=list,
        description="Past medical conditions"
    )
    current_medications: list[str] = Field(
        default_factory=list,
        description="Active medications"
    )
    allergies: list[str] = Field(
        default_factory=list,
        description="Known allergies"
    )


class TriageClassification(BaseModel):
    """Manchester Triage classification result."""

    color: TriageColor = Field(
        ...,
        description="Triage color classification"
    )
    priority: Priority = Field(
        ...,
        description="Priority level"
    )
    reasoning: str = Field(
        ...,
        description="Explanation for this classification"
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description="Identified risk factors"
    )
    matched_protocols: list[str] = Field(
        default_factory=list,
        description="Protocols used for decision"
    )


class Routing(BaseModel):
    """Routing decision with department and preliminary orders."""

    department: str = Field(
        ...,
        description="Target department (Cardiology, Orthopedics, etc.)"
    )
    doctor_type: str = Field(
        ...,
        description="Type of doctor needed"
    )
    urgency: Urgency = Field(
        ...,
        description="How quickly patient should be seen"
    )
    room_type: str | None = Field(
        default=None,
        description="Emergency bay, consultation room, etc."
    )
    preliminary_orders: list[str] = Field(
        default_factory=list,
        description="Recommended initial orders"
    )
    contraindications: list[str] = Field(
        default_factory=list,
        description="Things to avoid due to allergies"
    )
    notes_for_staff: str = Field(
        default="",
        description="Summary notes for receiving staff"
    )


class TriageResult(BaseModel):
    """Complete triage result combining all agent outputs."""

    timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )
    session_id: str = Field(
        ...,
        description="Session identifier"
    )
    anamnesis: Anamnesis
    classification: TriageClassification
    routing: Routing


# =============================================================================
# API Request/Response Models (from SRS Section 8)
# =============================================================================

class ChatMessage(BaseModel):
    """Request model for chat endpoint."""

    session_id: str = Field(
        ...,
        description="Unique session identifier"
    )
    message: str = Field(
        ...,
        description="User's message/answer"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    session_id: str
    question_number: int = Field(
        ...,
        ge=1,
        description="Current question number (1-indexed)"
    )
    next_question: str | None = Field(
        default=None,
        description="Next question to ask, or None if complete"
    )
    is_complete: bool = Field(
        default=False,
        description="Whether anamnesis is complete"
    )


class ProcessRequest(BaseModel):
    """Request model for process endpoint."""

    session_id: str = Field(
        ...,
        description="Session to process"
    )


class ProcessResponse(BaseModel):
    """Response model for process endpoint."""

    status: Literal["processing", "completed", "error"] = Field(
        ...,
        description="Processing status"
    )
    job_id: str = Field(
        ...,
        description="Job identifier for polling results"
    )


class ResultResponse(BaseModel):
    """Response model for result endpoint."""

    status: Literal["processing", "completed", "error"]
    result: TriageResult | None = None
    error: str | None = None


# =============================================================================
# Internal Models
# =============================================================================

class SessionData(BaseModel):
    """Internal session storage model."""

    session_id: str
    answers: dict[int, str] = Field(
        default_factory=dict,
        description="Question number to answer mapping"
    )
    current_question: int = Field(
        default=1,
        description="Current question number"
    )
    is_complete: bool = Field(
        default=False
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )
    anamnesis: Anamnesis | None = None
    classification: TriageClassification | None = None
    routing: Routing | None = None
