"""Routing Agent - Directs patients to appropriate departments.

This agent determines the correct department, preliminary orders,
and contraindications based on patient data and triage classification.
"""

import os
import json
from openai import OpenAI

from models.schemas import (
    Anamnesis,
    TriageClassification,
    Routing,
    Urgency,
    TriageColor,
)
from db.vector_store import VectorStore


# Map triage color to default urgency
COLOR_TO_URGENCY = {
    TriageColor.RED: Urgency.IMMEDIATE,
    TriageColor.YELLOW: Urgency.WITHIN_30_MIN,
    TriageColor.GREEN: Urgency.WITHIN_1_HOUR,
    TriageColor.BLUE: Urgency.STANDARD,
}


class RoutingAgent:
    """Agent that routes patients to appropriate departments."""

    def __init__(self, vector_store: VectorStore):
        """Initialize the Routing Agent.

        Args:
            vector_store: ChromaDB vector store for routing rules
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
        classification: TriageClassification,
        routing_rules: list[str],
        preliminary_orders: list[str],
        language: str = "en",
    ) -> str:
        """Build the routing prompt.

        Args:
            anamnesis: Patient data
            classification: Triage classification
            routing_rules: Relevant routing rules from ChromaDB
            preliminary_orders: Relevant preliminary orders from ChromaDB
            language: Patient's language (en, es, pt-BR)

        Returns:
            Formatted prompt string
        """
        rules_text = "\n".join(f"- {r}" for r in routing_rules)
        orders_text = "\n".join(f"- {o}" for o in preliminary_orders)

        language_names = {
            "en": "English",
            "es": "Spanish",
            "pt-BR": "Portuguese (Brazilian)"
        }
        language_name = language_names.get(language, "English")

        allergies_warning = ""
        if anamnesis.allergies:
            allergies_warning = f"""
## ⚠️ PATIENT ALLERGIES - CHECK FOR CONTRAINDICATIONS:
{", ".join(anamnesis.allergies)}

You MUST check if any preliminary orders might conflict with these allergies.
"""

        return f"""You are a hospital routing specialist. Your task is to direct a triaged patient to the appropriate department and generate preliminary orders.

## IMPORTANT: Language Context
The patient's data is in **{language_name}**. You must:
1. Understand the symptoms and data in their original language
2. Match them against the English routing rules and orders provided
3. **Output preliminary_orders, contraindications, and notes_for_staff in {language_name}**

## Patient Information:

- **Chief Complaint:** {anamnesis.chief_complaint}
- **Location:** {anamnesis.location or "Not specified"}
- **Associated Symptoms:** {", ".join(anamnesis.associated_symptoms) or "None"}
- **Medical History:** {", ".join(anamnesis.medical_history) or "None reported"}
- **Current Medications:** {", ".join(anamnesis.current_medications) or "None"}
- **Allergies:** {", ".join(anamnesis.allergies) or "NKDA (No Known Drug Allergies)"}

## Triage Classification:

- **Color:** {classification.color.value}
- **Priority:** {classification.priority.value}
- **Reasoning:** {classification.reasoning}
{allergies_warning}

## Available Routing Rules:

{rules_text}

## Available Preliminary Orders:

{orders_text}

## Department Options:

- Cardiology - chest pain, cardiac symptoms, arrhythmias
- Orthopedics - fractures, dislocations, musculoskeletal trauma
- General Surgery - abdominal emergencies, surgical conditions
- Neurology - stroke symptoms, seizures, severe headaches
- Pediatrics - patients under 18
- Obstetrics - pregnancy-related conditions
- General Practice - general illness, infections, non-specific symptoms
- Emergency Medicine - critical/unstable patients

## Instructions:

1. Match symptoms to the appropriate department
2. Select relevant preliminary orders for the condition
3. CHECK ALL ORDERS AGAINST PATIENT ALLERGIES
4. Generate a brief summary note for receiving staff

## Response Format:

Respond with ONLY a valid JSON object. **IMPORTANT: Write preliminary_orders, contraindications, and notes_for_staff in {language_name}**:
{{
    "department": "Department name",
    "doctor_type": "Specialist type (e.g., Cardiologist, Orthopedic Surgeon)",
    "urgency": "Immediate" | "Within 30 min" | "Within 1 hour" | "Standard",
    "room_type": "Emergency bay" | "Consultation room" | "Trauma bay" | null,
    "preliminary_orders": ["list of orders in {language_name}"],
    "contraindications": ["list of things to avoid in {language_name}"],
    "notes_for_staff": "Brief summary for receiving staff in {language_name}"
}}
"""

    async def route(
        self,
        anamnesis: Anamnesis,
        classification: TriageClassification,
        language: str = "en"
    ) -> Routing:
        """Route patient to appropriate department with orders.

        Args:
            anamnesis: Patient data
            classification: Triage classification
            language: Patient's language for output (en, es, pt-BR)

        Returns:
            Routing with department, orders, and contraindications
        """
        # Build search query
        search_query = f"{anamnesis.chief_complaint} {classification.color.value}"

        # Retrieve relevant routing rules and orders
        routing_rules = self.vector_store.search_routing_rules(
            query=search_query,
            n_results=5
        )

        preliminary_orders = self.vector_store.search_preliminary_orders(
            query=f"{anamnesis.chief_complaint} {' '.join(anamnesis.associated_symptoms)}",
            n_results=5
        )

        # Build and send prompt
        prompt = self._build_prompt(
            anamnesis,
            classification,
            routing_rules,
            preliminary_orders,
            language,
        )

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

        # Map urgency string to enum
        urgency_map = {
            "Immediate": Urgency.IMMEDIATE,
            "Within 30 min": Urgency.WITHIN_30_MIN,
            "Within 1 hour": Urgency.WITHIN_1_HOUR,
            "Standard": Urgency.STANDARD,
        }

        return Routing(
            department=data["department"],
            doctor_type=data["doctor_type"],
            urgency=urgency_map.get(data["urgency"], COLOR_TO_URGENCY[classification.color]),
            room_type=data.get("room_type"),
            preliminary_orders=data.get("preliminary_orders", []),
            contraindications=data.get("contraindications", []),
            notes_for_staff=data.get("notes_for_staff", ""),
        )
