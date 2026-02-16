"""CrewAI Orchestration for Triage System.

This module defines the CrewAI agents, tasks, and crew for orchestrating
the multi-agent triage system.
"""

import os
import json
from typing import Any

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from pydantic import Field

from models.schemas import (
    Anamnesis,
    TriageClassification,
    Routing,
    TriageColor,
    Priority,
    Urgency,
)
from db.vector_store import VectorStore
from chat.questions import ANAMNESIS_QUESTIONS


# =============================================================================
# TARS API / CrewAI LiteLLM Safety
# =============================================================================

# CrewAI uses LiteLLM internally which may require OPENAI_API_KEY
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("TARS_API_KEY", "dummy-key")


# =============================================================================
# Language Configuration
# =============================================================================

LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "pt-BR": "Portuguese (Brazilian)",
}

# Mapping from color to priority
COLOR_TO_PRIORITY = {
    TriageColor.RED: Priority.EMERGENCY,
    TriageColor.YELLOW: Priority.URGENT,
    TriageColor.GREEN: Priority.STANDARD,
    TriageColor.BLUE: Priority.LOW,
}

# Map triage color to default urgency
COLOR_TO_URGENCY = {
    TriageColor.RED: Urgency.IMMEDIATE,
    TriageColor.YELLOW: Urgency.WITHIN_30_MIN,
    TriageColor.GREEN: Urgency.WITHIN_1_HOUR,
    TriageColor.BLUE: Urgency.STANDARD,
}


# =============================================================================
# Custom Tools for Vector Store Access
# =============================================================================

class TriageProtocolSearchTool(BaseTool):
    """Tool to search triage protocols in the vector store."""

    name: str = "search_triage_protocols"
    description: str = "Search for relevant triage protocols based on symptoms"
    vector_store: Any = Field(default=None, exclude=True)

    def _run(self, query: str) -> str:
        """Search triage protocols."""
        if self.vector_store is None:
            return "[]"
        results = self.vector_store.search_triage_protocols(query=query, n_results=5)
        return json.dumps(results)


class RoutingRulesSearchTool(BaseTool):
    """Tool to search routing rules in the vector store."""

    name: str = "search_routing_rules"
    description: str = "Search for routing rules based on symptoms and classification"
    vector_store: Any = Field(default=None, exclude=True)

    def _run(self, query: str) -> str:
        """Search routing rules."""
        if self.vector_store is None:
            return "[]"
        results = self.vector_store.search_routing_rules(query=query, n_results=5)
        return json.dumps(results)


class PreliminaryOrdersSearchTool(BaseTool):
    """Tool to search preliminary orders in the vector store."""

    name: str = "search_preliminary_orders"
    description: str = "Search for preliminary medical orders based on condition"
    vector_store: Any = Field(default=None, exclude=True)

    def _run(self, query: str) -> str:
        """Search preliminary orders."""
        if self.vector_store is None:
            return "[]"
        results = self.vector_store.search_preliminary_orders(query=query, n_results=5)
        return json.dumps(results)


# =============================================================================
# Triage Crew
# =============================================================================

class TriageCrew:
    """CrewAI-based orchestrator for the triage system."""

    def __init__(self, vector_store: VectorStore):
        """Initialize the Triage Crew.

        Args:
            vector_store: ChromaDB vector store for protocol lookup
        """
        self.vector_store = vector_store
        self.llm = LLM(
            model="openai/tars-latest",
            api_key=os.getenv("TARS_API_KEY"),
            base_url=os.getenv("TARS_API_URL"),
        )

        # Initialize tools
        self.triage_tool = TriageProtocolSearchTool(vector_store=vector_store)
        self.routing_tool = RoutingRulesSearchTool(vector_store=vector_store)
        self.orders_tool = PreliminaryOrdersSearchTool(vector_store=vector_store)

    def _create_anamnesis_agent(self, language: str) -> Agent:
        """Create the anamnesis agent."""
        language_name = LANGUAGE_NAMES.get(language, "English")

        return Agent(
            role="Medical Data Extraction Specialist",
            goal=f"Extract and structure patient medical information accurately in {language_name}",
            backstory="""You are an experienced medical records specialist who excels at
            extracting structured medical information from patient interviews. You understand
            medical terminology in multiple languages and can accurately identify chief complaints,
            symptoms, and medical history from conversational responses.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

    def _create_triage_agent(self, language: str) -> Agent:
        """Create the triage classification agent."""
        language_name = LANGUAGE_NAMES.get(language, "English")

        return Agent(
            role="Emergency Triage Specialist",
            goal=f"Classify patient urgency using Manchester Triage Protocol, outputting reasoning in {language_name}",
            backstory="""You are a senior emergency department nurse with 15 years of experience
            in patient triage using the Manchester Triage System. You can quickly identify
            life-threatening conditions, recognize red flags, and accurately classify patients
            into RED (emergency), YELLOW (urgent), GREEN (standard), or BLUE (low priority) categories.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            tools=[self.triage_tool],
        )

    def _create_routing_agent(self, language: str) -> Agent:
        """Create the routing and orders agent."""
        language_name = LANGUAGE_NAMES.get(language, "English")

        return Agent(
            role="Hospital Routing Specialist",
            goal=f"Route patients to appropriate departments and generate preliminary orders in {language_name}",
            backstory="""You are a hospital patient flow coordinator with extensive knowledge
            of departmental capabilities. You excel at matching patient presentations to the
            appropriate specialty department and generating safe preliminary orders while
            carefully checking for allergies and contraindications.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            tools=[self.routing_tool, self.orders_tool],
        )

    def _build_anamnesis_prompt(self, answers: dict[int, str], language: str) -> str:
        """Build the anamnesis extraction prompt."""
        language_name = LANGUAGE_NAMES.get(language, "English")

        # Build Q&A pairs
        qa_pairs = []
        for q in ANAMNESIS_QUESTIONS:
            answer = answers.get(q.number, "Not provided")
            question_text = q.get_question(language)
            qa_pairs.append(f"Q{q.number}: {question_text}\nA: {answer}")

        qa_text = "\n\n".join(qa_pairs)

        return f"""Extract structured medical information from these patient responses in {language_name}.

## Patient Responses:
{qa_text}

## Required Output (JSON):
{{
    "language": "{language}",
    "patient_name": "string",
    "date_of_birth": "string",
    "phone_number": "string or null",
    "emergency_contact_name": "string or null",
    "emergency_contact_phone": "string or null",
    "chief_complaint": "string in {language_name}",
    "onset": "string in {language_name}",
    "duration": "string or null",
    "pain_scale": number 1-10 or null,
    "pain_type": "string or null",
    "location": "string or null in {language_name}",
    "radiation": "string or null",
    "associated_symptoms": ["list in {language_name}"],
    "medical_history": ["list in {language_name}"],
    "current_medications": ["list"],
    "allergies": ["list in {language_name}"]
}}

IMPORTANT: Keep all medical terms in {language_name}. Output ONLY valid JSON."""

    def _build_triage_prompt(self, anamnesis: Anamnesis, language: str) -> str:
        """Build the triage classification prompt."""
        language_name = LANGUAGE_NAMES.get(language, "English")

        return f"""Classify this patient using Manchester Triage Protocol.

## Patient Information:
- Chief Complaint: {anamnesis.chief_complaint}
- Onset: {anamnesis.onset}
- Pain Scale: {anamnesis.pain_scale or "Not specified"}/10
- Location: {anamnesis.location or "Not specified"}
- Radiation: {anamnesis.radiation or "None"}
- Associated Symptoms: {", ".join(anamnesis.associated_symptoms) or "None"}
- Medical History: {", ".join(anamnesis.medical_history) or "None"}
- Allergies: {", ".join(anamnesis.allergies) or "NKDA"}

## Classification Criteria:
- RED: Life-threatening (airway, breathing, hemorrhage, shock, unconscious)
- YELLOW: Serious but stable (moderate pain 7-8/10, fever with infection, possible fractures)
- GREEN: Non-urgent (minor injuries, mild symptoms, stable vitals)
- BLUE: Minor issues (small cuts, cold symptoms, chronic stable conditions)

## Required Output (JSON) - Write reasoning in {language_name}:
{{
    "color": "RED" | "YELLOW" | "GREEN" | "BLUE",
    "reasoning": "explanation in {language_name}",
    "risk_factors": ["list in {language_name}"],
    "matched_protocols": ["protocols that matched"]
}}

First use the search_triage_protocols tool to find relevant protocols, then classify.
Output ONLY valid JSON."""

    def _build_routing_prompt(
        self,
        anamnesis: Anamnesis,
        classification: TriageClassification,
        language: str
    ) -> str:
        """Build the routing prompt."""
        language_name = LANGUAGE_NAMES.get(language, "English")

        allergies_warning = ""
        if anamnesis.allergies:
            allergies_warning = f"\n⚠️ ALLERGIES: {', '.join(anamnesis.allergies)} - Check all orders for contraindications!"

        return f"""Route this triaged patient to the appropriate department.

## Patient:
- Chief Complaint: {anamnesis.chief_complaint}
- Location: {anamnesis.location or "Not specified"}
- Associated Symptoms: {", ".join(anamnesis.associated_symptoms) or "None"}
- Medical History: {", ".join(anamnesis.medical_history) or "None"}
- Medications: {", ".join(anamnesis.current_medications) or "None"}
- Allergies: {", ".join(anamnesis.allergies) or "NKDA"}
{allergies_warning}

## Triage Classification:
- Color: {classification.color.value}
- Priority: {classification.priority.value}
- Reasoning: {classification.reasoning}

## Departments:
- Cardiology, Orthopedics, General Surgery, Neurology, Pediatrics, Obstetrics, General Practice, Emergency Medicine

## Required Output (JSON) - Write in {language_name}:
{{
    "department": "Department name",
    "doctor_type": "Specialist type in {language_name}",
    "urgency": "Immediate" | "Within 30 min" | "Within 1 hour" | "Standard",
    "room_type": "Room type in {language_name}",
    "preliminary_orders": ["orders in {language_name}"],
    "contraindications": ["things to avoid in {language_name}"],
    "notes_for_staff": "summary in {language_name}"
}}

Use search_routing_rules and search_preliminary_orders tools first.
Output ONLY valid JSON."""

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from text that may contain markdown code blocks."""
        text = text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Find the content between ``` markers
            start_idx = 1 if lines[0].startswith("```") else 0
            end_idx = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
            text = "\n".join(lines[start_idx:end_idx])

        # Try to find JSON object in the text
        start = text.find("{")
        end = text.rfind("}") + 1

        if start != -1 and end > start:
            json_str = text[start:end]
            return json.loads(json_str)

        return json.loads(text)

    async def process(
        self,
        answers: dict[int, str],
        language: str = "en"
    ) -> tuple[Anamnesis, TriageClassification, Routing]:
        """Process patient through the full triage pipeline.

        Args:
            answers: Patient's answers to anamnesis questions
            language: Language code (en, es, pt-BR)

        Returns:
            Tuple of (Anamnesis, TriageClassification, Routing)
        """
        # Create agents for this session
        anamnesis_agent = self._create_anamnesis_agent(language)
        triage_agent = self._create_triage_agent(language)
        routing_agent = self._create_routing_agent(language)

        # Task 1: Extract anamnesis
        anamnesis_task = Task(
            description=self._build_anamnesis_prompt(answers, language),
            expected_output="Valid JSON with structured patient medical information",
            agent=anamnesis_agent,
        )

        # Create crew for anamnesis
        anamnesis_crew = Crew(
            agents=[anamnesis_agent],
            tasks=[anamnesis_task],
            process=Process.sequential,
            verbose=True,
        )

        # Execute anamnesis extraction
        anamnesis_result = anamnesis_crew.kickoff()
        anamnesis_data = self._extract_json(str(anamnesis_result))
        anamnesis = Anamnesis(**anamnesis_data)

        # Task 2: Triage classification
        triage_task = Task(
            description=self._build_triage_prompt(anamnesis, language),
            expected_output="Valid JSON with triage classification (color, reasoning, risk_factors)",
            agent=triage_agent,
        )

        triage_crew = Crew(
            agents=[triage_agent],
            tasks=[triage_task],
            process=Process.sequential,
            verbose=True,
        )

        triage_result = triage_crew.kickoff()
        triage_data = self._extract_json(str(triage_result))
        color = TriageColor(triage_data["color"])

        classification = TriageClassification(
            color=color,
            priority=COLOR_TO_PRIORITY[color],
            reasoning=triage_data["reasoning"],
            risk_factors=triage_data.get("risk_factors", []),
            matched_protocols=triage_data.get("matched_protocols", []),
        )

        # Task 3: Routing
        routing_task = Task(
            description=self._build_routing_prompt(anamnesis, classification, language),
            expected_output="Valid JSON with routing information (department, orders, contraindications)",
            agent=routing_agent,
        )

        routing_crew = Crew(
            agents=[routing_agent],
            tasks=[routing_task],
            process=Process.sequential,
            verbose=True,
        )

        routing_result = routing_crew.kickoff()
        routing_data = self._extract_json(str(routing_result))

        urgency_map = {
            "Immediate": Urgency.IMMEDIATE,
            "Within 30 min": Urgency.WITHIN_30_MIN,
            "Within 1 hour": Urgency.WITHIN_1_HOUR,
            "Standard": Urgency.STANDARD,
        }

        routing = Routing(
            department=routing_data["department"],
            doctor_type=routing_data["doctor_type"],
            urgency=urgency_map.get(routing_data["urgency"], COLOR_TO_URGENCY[color]),
            room_type=routing_data.get("room_type"),
            preliminary_orders=routing_data.get("preliminary_orders", []),
            contraindications=routing_data.get("contraindications", []),
            notes_for_staff=routing_data.get("notes_for_staff", ""),
        )

        return anamnesis, classification, routing
