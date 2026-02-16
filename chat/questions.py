"""Predefined anamnesis questions for the chat interface.

These questions follow a structured order to collect patient information
as defined in SRS Section 6.
"""

from dataclasses import dataclass


@dataclass
class AnamnesisQuestion:
    """Represents a single anamnesis question."""

    number: int
    question: str
    field_name: str
    description: str


# Predefined questions for patient intake
ANAMNESIS_QUESTIONS: list[AnamnesisQuestion] = [
    # Patient Demographics (Questions 1-5)
    AnamnesisQuestion(
        number=1,
        question="What is your full name?",
        field_name="patient_name",
        description="Patient's full name"
    ),
    AnamnesisQuestion(
        number=2,
        question="What is your date of birth?",
        field_name="date_of_birth",
        description="Patient's date of birth"
    ),
    AnamnesisQuestion(
        number=3,
        question="What is your phone number?",
        field_name="phone_number",
        description="Contact phone number"
    ),
    AnamnesisQuestion(
        number=4,
        question="Emergency contact name (who should we call in case of emergency)?",
        field_name="emergency_contact_name",
        description="Emergency contact person"
    ),
    AnamnesisQuestion(
        number=5,
        question="Emergency contact phone number?",
        field_name="emergency_contact_phone",
        description="Emergency contact phone"
    ),

    # Chief Complaint & Symptoms (Questions 6-14)
    AnamnesisQuestion(
        number=6,
        question="What brings you in today?",
        field_name="chief_complaint",
        description="Main reason for visit"
    ),
    AnamnesisQuestion(
        number=7,
        question="When did this start?",
        field_name="onset",
        description="When symptoms started"
    ),
    AnamnesisQuestion(
        number=8,
        question="On a scale of 1-10, how severe is it?",
        field_name="pain_scale",
        description="Severity rating"
    ),
    AnamnesisQuestion(
        number=9,
        question="Where exactly is the problem located?",
        field_name="location",
        description="Body location"
    ),
    AnamnesisQuestion(
        number=10,
        question="Does the pain spread anywhere else?",
        field_name="radiation",
        description="Pain radiation"
    ),
    AnamnesisQuestion(
        number=11,
        question="Any other symptoms? (dizziness, nausea, fever, etc.)",
        field_name="associated_symptoms",
        description="Associated symptoms"
    ),
    AnamnesisQuestion(
        number=12,
        question="Do you have any medical conditions?",
        field_name="medical_history",
        description="Past medical history"
    ),
    AnamnesisQuestion(
        number=13,
        question="What medications are you currently taking?",
        field_name="current_medications",
        description="Current medications"
    ),
    AnamnesisQuestion(
        number=14,
        question="Do you have any allergies?",
        field_name="allergies",
        description="Known allergies"
    ),
]


def get_question(question_number: int) -> AnamnesisQuestion | None:
    """Get a question by its number (1-indexed).

    Args:
        question_number: The question number (1-9)

    Returns:
        The AnamnesisQuestion or None if out of range
    """
    if 1 <= question_number <= len(ANAMNESIS_QUESTIONS):
        return ANAMNESIS_QUESTIONS[question_number - 1]
    return None


def get_total_questions() -> int:
    """Get the total number of anamnesis questions."""
    return len(ANAMNESIS_QUESTIONS)


def get_welcome_message() -> str:
    """Get the initial welcome message for the chat."""
    return (
        "Welcome to Triage AI. I'll ask you a few questions to understand "
        "your symptoms and help direct you to the right care. "
        "Let's begin."
    )


def get_first_question() -> str:
    """Get the first question to start the anamnesis."""
    return ANAMNESIS_QUESTIONS[0].question
