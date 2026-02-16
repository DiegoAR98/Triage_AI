"""Anamnesis Agent - Structures raw patient answers into medical data.

This agent transforms free-text patient responses into a structured
Anamnesis object using LLM processing.
"""

import os
from openai import OpenAI

from models.schemas import Anamnesis
from chat.questions import ANAMNESIS_QUESTIONS


class AnamnesisAgent:
    """Agent that structures raw patient answers into medical anamnesis data."""

    def __init__(self):
        """Initialize the Anamnesis Agent with TARS API client."""
        self.client = OpenAI(
            api_key=os.getenv("TARS_API_KEY"),
            base_url=os.getenv("TARS_API_URL"),
        )
        self.model = "tars-latest"

    def _build_prompt(self, answers: dict[int, str]) -> str:
        """Build the prompt for structuring anamnesis data.

        Args:
            answers: Dictionary mapping question number to patient answer

        Returns:
            Formatted prompt string
        """
        # Build Q&A pairs
        qa_pairs = []
        for q in ANAMNESIS_QUESTIONS:
            answer = answers.get(q.number, "Not provided")
            qa_pairs.append(f"Q{q.number}: {q.question}\nA: {answer}")

        qa_text = "\n\n".join(qa_pairs)

        return f"""You are a medical data extraction assistant. Your task is to analyze patient responses from a triage intake interview and extract structured medical information.

## Patient Responses:

{qa_text}

## Instructions:

Extract and structure the information into a medical anamnesis. Follow these guidelines:

1. **chief_complaint**: Identify the main reason for the visit in medical terminology (e.g., "chest pain" instead of "my chest hurts")

2. **onset**: Extract when symptoms started (e.g., "2 hours ago", "yesterday morning")

3. **pain_scale**: Extract numeric value 1-10. If not numeric, estimate based on descriptors (severe=8-10, moderate=5-7, mild=1-4)

4. **location**: Body location using anatomical terms where appropriate

5. **radiation**: Where pain spreads to, if mentioned

6. **associated_symptoms**: List of other symptoms. Convert lay terms to medical terminology:
   - "sweating" → "diaphoresis"
   - "throwing up" → "nausea/vomiting"
   - "hard to breathe" → "dyspnea"
   - "dizzy" → "dizziness/vertigo"

7. **medical_history**: List of past medical conditions

8. **current_medications**: List of medications

9. **allergies**: List of allergies (especially drug allergies)

## Response Format:

Respond with ONLY a valid JSON object matching this structure:
{{
    "chief_complaint": "string",
    "onset": "string",
    "duration": "string or null",
    "pain_scale": number or null (1-10),
    "pain_type": "string or null",
    "location": "string or null",
    "radiation": "string or null",
    "associated_symptoms": ["list", "of", "symptoms"],
    "medical_history": ["list", "of", "conditions"],
    "current_medications": ["list", "of", "medications"],
    "allergies": ["list", "of", "allergies"]
}}

If information is not provided or unclear, use null for optional fields or empty arrays for lists.
"""

    async def process(self, answers: dict[int, str]) -> Anamnesis:
        """Process patient answers into structured Anamnesis.

        Args:
            answers: Dictionary mapping question number to patient answer

        Returns:
            Structured Anamnesis object
        """
        prompt = self._build_prompt(answers)

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        # Extract JSON from response
        response_text = response.choices[0].message.content.strip()

        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first and last lines (```json and ```)
            response_text = "\n".join(lines[1:-1])

        import json
        data = json.loads(response_text)

        return Anamnesis(**data)
