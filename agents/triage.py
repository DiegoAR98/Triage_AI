"""Triage Agent - Classifies patients using Manchester Triage Protocol.

This agent analyzes structured anamnesis data and assigns a triage
classification (RED/YELLOW/GREEN/BLUE) based on symptom matching
against the Manchester Triage Protocol.
"""

import os
import json
from openai import OpenAI

from models.schemas import Anamnesis, TriageClassification, TriageColor, Priority
from db.vector_store import VectorStore


# Mapping from color to priority
COLOR_TO_PRIORITY = {
    TriageColor.RED: Priority.EMERGENCY,
    TriageColor.YELLOW: Priority.URGENT,
    TriageColor.GREEN: Priority.STANDARD,
    TriageColor.BLUE: Priority.LOW,
}


class TriageAgent:
    """Agent that classifies patients using Manchester Triage Protocol."""

    def __init__(self, vector_store: VectorStore):
        """Initialize the Triage Agent.

        Args:
            vector_store: ChromaDB vector store for protocol lookup
        """
        self.client = OpenAI(
            api_key=os.getenv("TARS_API_KEY"),
            base_url=os.getenv("TARS_API_URL"),
        )
        self.model = "tars-latest"
        self.vector_store = vector_store

    def _build_prompt(
        self,
        anamnesis: Anamnesis,
        relevant_protocols: list[str]
    ) -> str:
        """Build the classification prompt.

        Args:
            anamnesis: Structured patient data
            relevant_protocols: Matching protocols from ChromaDB

        Returns:
            Formatted prompt string
        """
        protocols_text = "\n".join(f"- {p}" for p in relevant_protocols)

        return f"""You are an emergency department triage specialist. Your task is to classify a patient using the Manchester Triage Protocol.

## Patient Anamnesis:

- **Chief Complaint:** {anamnesis.chief_complaint}
- **Onset:** {anamnesis.onset}
- **Pain Scale:** {anamnesis.pain_scale or "Not specified"}/10
- **Location:** {anamnesis.location or "Not specified"}
- **Radiation:** {anamnesis.radiation or "None"}
- **Associated Symptoms:** {", ".join(anamnesis.associated_symptoms) or "None"}
- **Medical History:** {", ".join(anamnesis.medical_history) or "None reported"}
- **Current Medications:** {", ".join(anamnesis.current_medications) or "None"}
- **Allergies:** {", ".join(anamnesis.allergies) or "NKDA"}

## Relevant Triage Protocols:

{protocols_text}

## Manchester Triage Classification Criteria:

| Color | Priority | Criteria | Max Wait Time |
|-------|----------|----------|---------------|
| RED | EMERGENCY | Life-threatening: airway compromise, severe breathing difficulty, major hemorrhage, shock, unconsciousness, severe chest pain with cardiac features | Immediate |
| YELLOW | URGENT | Serious but stable: moderate pain (7-8/10), localized infection with fever, possible fractures, moderate breathing issues | 30-60 minutes |
| GREEN | STANDARD | Non-urgent: minor injuries, mild symptoms, stable vital signs, low-grade fever | 1-4 hours |
| BLUE | LOW | Minor issues: small cuts, minor cold symptoms, chronic stable conditions | 4+ hours |

## Instructions:

1. Analyze the patient's symptoms against the triage protocols
2. Consider red flags: chest pain with radiation/diaphoresis, severe pain, breathing difficulty, altered consciousness
3. Account for risk factors from medical history
4. Assign the appropriate classification

## Response Format:

Respond with ONLY a valid JSON object:
{{
    "color": "RED" | "YELLOW" | "GREEN" | "BLUE",
    "reasoning": "Brief explanation of why this classification was assigned",
    "risk_factors": ["list", "of", "identified", "risks"],
    "matched_protocols": ["protocols", "that", "matched"]
}}
"""

    async def classify(self, anamnesis: Anamnesis) -> TriageClassification:
        """Classify patient urgency using Manchester Triage Protocol.

        Args:
            anamnesis: Structured patient data

        Returns:
            TriageClassification with color, priority, and reasoning
        """
        # Build search query from key symptoms
        search_query = f"{anamnesis.chief_complaint} {' '.join(anamnesis.associated_symptoms)}"

        # Retrieve relevant protocols from ChromaDB
        relevant_protocols = self.vector_store.search_triage_protocols(
            query=search_query,
            n_results=5
        )

        # Build and send prompt
        prompt = self._build_prompt(anamnesis, relevant_protocols)

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        # Extract JSON from response
        response_text = response.choices[0].message.content.strip()

        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        data = json.loads(response_text)

        # Map color string to enum
        color = TriageColor(data["color"])

        return TriageClassification(
            color=color,
            priority=COLOR_TO_PRIORITY[color],
            reasoning=data["reasoning"],
            risk_factors=data.get("risk_factors", []),
            matched_protocols=data.get("matched_protocols", []),
        )
