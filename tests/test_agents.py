"""Tests for Triage AI agents and API endpoints."""

import pytest
from fastapi.testclient import TestClient

from models.schemas import (
    Anamnesis,
    TriageClassification,
    TriageColor,
    Priority,
)


# =============================================================================
# Model Tests
# =============================================================================

class TestAnamnesis:
    """Tests for Anamnesis model."""

    def test_minimal_anamnesis(self):
        """Test creating anamnesis with required fields only."""
        anamnesis = Anamnesis(
            chief_complaint="chest pain",
            onset="2 hours ago",
        )

        assert anamnesis.chief_complaint == "chest pain"
        assert anamnesis.onset == "2 hours ago"
        assert anamnesis.pain_scale is None
        assert anamnesis.allergies == []

    def test_full_anamnesis(self):
        """Test creating anamnesis with all fields."""
        anamnesis = Anamnesis(
            chief_complaint="chest pain",
            onset="2 hours ago",
            duration="ongoing",
            pain_scale=8,
            pain_type="pressure",
            location="substernal",
            radiation="left arm",
            associated_symptoms=["diaphoresis", "dyspnea"],
            medical_history=["hypertension", "diabetes"],
            current_medications=["metformin", "lisinopril"],
            allergies=["aspirin"],
        )

        assert anamnesis.pain_scale == 8
        assert "diaphoresis" in anamnesis.associated_symptoms
        assert "aspirin" in anamnesis.allergies

    def test_pain_scale_validation(self):
        """Test pain scale must be 1-10."""
        with pytest.raises(ValueError):
            Anamnesis(
                chief_complaint="pain",
                onset="now",
                pain_scale=15,  # Invalid
            )


class TestTriageClassification:
    """Tests for TriageClassification model."""

    def test_red_classification(self):
        """Test RED emergency classification."""
        classification = TriageClassification(
            color=TriageColor.RED,
            priority=Priority.EMERGENCY,
            reasoning="Chest pain with diaphoresis suggests ACS",
            risk_factors=["cardiac symptoms", "diaphoresis"],
            matched_protocols=["Cardiac chest pain protocol"],
        )

        assert classification.color == TriageColor.RED
        assert classification.priority == Priority.EMERGENCY

    def test_all_colors(self):
        """Test all triage colors can be created."""
        colors = [
            (TriageColor.RED, Priority.EMERGENCY),
            (TriageColor.YELLOW, Priority.URGENT),
            (TriageColor.GREEN, Priority.STANDARD),
            (TriageColor.BLUE, Priority.LOW),
        ]

        for color, priority in colors:
            classification = TriageClassification(
                color=color,
                priority=priority,
                reasoning=f"Test {color.value} classification",
            )
            assert classification.color == color
            assert classification.priority == priority


# =============================================================================
# API Tests (require running server)
# =============================================================================

class TestAPIEndpoints:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        # Import here to avoid import errors during collection
        from main import app
        return TestClient(app)

    def test_health_check(self, client):
        """Test root endpoint returns OK."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "Triage AI"

    def test_create_session(self, client):
        """Test session creation."""
        response = client.post("/api/session")

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "first_question" in data

    def test_chat_flow(self, client):
        """Test basic chat flow."""
        # Create session
        session_response = client.post("/api/session")
        session_id = session_response.json()["session_id"]

        # Answer first question
        chat_response = client.post(
            "/api/chat",
            json={
                "session_id": session_id,
                "message": "my chest hurts",
            },
        )

        assert chat_response.status_code == 200
        data = chat_response.json()
        assert data["session_id"] == session_id
        assert data["question_number"] == 2
        assert data["is_complete"] is False

    def test_invalid_session(self, client):
        """Test chat with invalid session ID."""
        response = client.post(
            "/api/chat",
            json={
                "session_id": "invalid-session-id",
                "message": "test",
            },
        )

        assert response.status_code == 404


# =============================================================================
# Question Tests
# =============================================================================

class TestQuestions:
    """Tests for predefined questions."""

    def test_get_question(self):
        """Test getting questions by number."""
        from chat.questions import get_question, get_total_questions

        # First question
        q1 = get_question(1)
        assert q1 is not None
        assert q1.number == 1
        assert "brings you in" in q1.question.lower()

        # Last question
        total = get_total_questions()
        q_last = get_question(total)
        assert q_last is not None
        assert "allergies" in q_last.question.lower()

        # Out of range
        q_invalid = get_question(100)
        assert q_invalid is None

    def test_total_questions(self):
        """Test total questions count."""
        from chat.questions import get_total_questions

        total = get_total_questions()
        assert total == 9  # As per SRS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
