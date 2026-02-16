"""Anamnesis Agent - Structures raw patient answers into medical data.

This agent transforms free-text patient responses into a structured
Anamnesis object using LLM processing.
"""

import os
from openai import OpenAI

from models.schemas import Anamnesis
from chat.questions import ANAMNESIS_QUESTIONS


# Language names for display in prompts
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "pt-BR": "Portuguese (Brazil)",
}


class AnamnesisAgent:
    """Agent that structures raw patient answers into medical anamnesis data."""

    def __init__(self):
        """Initialize the Anamnesis Agent with TARS API client."""
        self.client = OpenAI(
            api_key=os.getenv("TARS_API_KEY"),
            base_url=os.getenv("TARS_API_URL"),
        )
        self.model = "tars-latest"

    def _build_prompt(self, answers: dict[int, str], language: str = "en") -> str:
        """Build the prompt for structuring anamnesis data.

        Args:
            answers: Dictionary mapping question number to patient answer
            language: Patient's preferred language code

        Returns:
            Formatted prompt string
        """
        # Build Q&A pairs in the patient's language
        qa_pairs = []
        for q in ANAMNESIS_QUESTIONS:
            answer = answers.get(q.number, "Not provided")
            question_text = q.get_question(language)
            qa_pairs.append(f"Q{q.number}: {question_text}\nA: {answer}")

        qa_text = "\n\n".join(qa_pairs)
        language_name = LANGUAGE_NAMES.get(language, "English")

        return f"""You are a medical data extraction assistant. Your task is to analyze patient responses from a triage intake interview and extract structured medical information.

NOTE: The patient's responses are in {language_name}. Extract information regardless of the input language, but output field values in medical English terminology where appropriate.

## Patient Responses:

{qa_text}

## Instructions:

Extract and structure the information into a medical anamnesis. Follow these guidelines:

### Patient Demographics:
1. **patient_name**: Extract the patient's full name exactly as provided
2. **date_of_birth**: Extract date of birth in the format provided
3. **phone_number**: Extract phone number if provided
4. **emergency_contact_name**: Extract emergency contact person's name
5. **emergency_contact_phone**: Extract emergency contact phone number

### Medical Information:
6. **chief_complaint**: Identify the main reason for the visit in medical terminology (e.g., "chest pain" instead of "my chest hurts")

7. **onset**: Extract when symptoms started (e.g., "2 hours ago", "yesterday morning")

8. **pain_scale**: Extract numeric value 1-10. If not numeric, estimate based on descriptors (severe=8-10, moderate=5-7, mild=1-4)

9. **location**: Body location using anatomical terms where appropriate

10. **radiation**: Where pain spreads to, if mentioned

11. **associated_symptoms**: List of other symptoms. Convert lay terms to medical terminology:
   - "sweating" → "diaphoresis"
   - "throwing up" → "nausea/vomiting"
   - "hard to breathe" → "dyspnea"
   - "dizzy" → "dizziness/vertigo"

12. **medical_history**: List of past medical conditions

13. **current_medications**: List of medications

14. **allergies**: List of allergies (especially drug allergies)

## Response Format:

Respond with ONLY a valid JSON object matching this structure:
{{
    "language": "string (language code: en, es, or pt-BR)",
    "patient_name": "string",
    "date_of_birth": "string",
    "phone_number": "string or null",
    "emergency_contact_name": "string or null",
    "emergency_contact_phone": "string or null",
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

    async def process(self, answers: dict[int, str], language: str = "en") -> Anamnesis:
        """Process patient answers into structured Anamnesis.

        Args:
            answers: Dictionary mapping question number to patient answer
            language: Patient's preferred language code

        Returns:
            Structured Anamnesis object
        """
        prompt = self._build_prompt(answers, language)

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
