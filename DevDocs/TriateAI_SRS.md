# Software Requirements Specification

## Triage AI

**Version:** 2.0 (MVP)
**Author:** Diego Araujo
**Date:** January 2026
**Status:** Draft

---

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for Triage AI, a multi-agent system that conducts patient anamnesis through a chat interface, classifies patients using the Manchester Triage Protocol (RED/YELLOW/GREEN/BLUE), and routes them to the appropriate medical department.

### 1.2 Scope

The MVP focuses on a chat-based intake flow using three sequential agents: Anamnesis, Triage, and Routing. The system collects patient information through predefined questions, classifies urgency, and generates actionable output for clinical staff.

### 1.3 Definitions

| Term | Definition |
|------|------------|
| Anamnesis | Structured medical history interview with a patient |
| Manchester Triage | Standardized triage classification system using colors (RED, YELLOW, GREEN, BLUE) |
| RAG | Retrieval-Augmented Generation: combining search with LLM response |
| CrewAI | Multi-agent orchestration framework |
| ChromaDB | Vector database for similarity search |

---

## 2. System Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              TRIAGE AI                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  USER                                                                   │
│  (Chat Interface)                                                       │
│       │                                                                 │
│       │ Answers predefined questions                                    │
│       ▼                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │   ANAMNESIS  │───►│    TRIAGE    │───►│   ROUTING    │              │
│  │    AGENT     │    │    AGENT     │    │    AGENT     │              │
│  │              │    │              │    │              │              │
│  │ Structures   │    │ Classifies   │    │ Directs to   │              │
│  │ patient data │    │ RED/YLW/GRN  │    │ department   │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│                             │                   │                       │
│                             ▼                   ▼                       │
│                      ┌─────────────────────────────────┐               │
│                      │         ChromaDB                │               │
│                      │  • Triage protocols             │               │
│                      │  • Routing rules                │               │
│                      │  • Preliminary orders           │               │
│                      └─────────────────────────────────┘               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | Python 3.11 + FastAPI |
| Agent Orchestration | CrewAI |
| LLM Provider | Claude API (Anthropic) |
| Vector Database | ChromaDB (embedded) |
| Data Validation | Pydantic |
| Frontend | React (chat interface) |
| Deployment | Render |

---

## 3. User Flow

### 3.1 Chat Interface Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         CHAT SCREEN                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🏥 Triage AI                                                   │
│                                                                 │
│  Agent: What brings you in today?                               │
│                                                                 │
│  You: my chest hurts really bad                                 │
│                                                                 │
│  Agent: When did this start?                                    │
│                                                                 │
│  You: about 2 hours ago                                         │
│                                                                 │
│  Agent: On a scale of 1-10, how severe is it?                   │
│                                                                 │
│  You: 8                                                         │
│                                                                 │
│  Agent: Any other symptoms? (dizziness, nausea, fever, etc.)    │
│                                                                 │
│  You: yeah im dizzy and sweating                                │
│                                                                 │
│  [Type your message...]                              [Send]     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Results Screen

```
┌─────────────────────────────────────────────────────────────────┐
│                        TRIAGE RESULT                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔴 RED - EMERGENCY                                             │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  PATIENT SUMMARY                                                │
│  Chief Complaint: Chest pain                                    │
│  Severity: 8/10                                                 │
│  Onset: 2 hours ago                                             │
│  Associated Symptoms: Dizziness, diaphoresis                    │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ROUTE TO: Cardiology                                           │
│  URGENCY: Immediate                                             │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  PRELIMINARY ORDERS                                             │
│  • 12-lead ECG within 10 minutes                                │
│  • Troponin I and T levels                                      │
│  • Continuous cardiac monitoring                                │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ⚠️ CONTRAINDICATIONS                                           │
│  • NO ASPIRIN - Patient allergic                                │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  [Start New Triage]                        [Download Summary]   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Agent Specifications

### 4.1 Agent 1: Anamnesis Agent

**Purpose:** Transform raw patient answers into structured medical data.

**Input:** Raw conversation answers from predefined questions

**Processing:**
- Clean and normalize language
- Extract medical terminology
- Structure data into Pydantic model

**Output:** Structured Anamnesis object

**Tools:** None (LLM processing only)

**Example:**

```
INPUT (raw answers):
- "my chest hurts really bad"
- "like 2 hours ago maybe more"
- "8"
- "yeah im dizzy and sweating"

OUTPUT (structured):
{
  "chief_complaint": "chest pain",
  "onset": "2 hours ago",
  "pain_scale": 8,
  "associated_symptoms": ["dizziness", "diaphoresis"]
}
```

### 4.2 Agent 2: Triage Agent

**Purpose:** Classify patient urgency using Manchester Triage Protocol.

**Input:** Structured Anamnesis from Agent 1

**Processing:**
- Search ChromaDB for matching triage protocols
- Apply Manchester Triage criteria
- Determine classification with reasoning

**Output:** TriageClassification object

**Tools:** ChromaDB search (triage_protocols collection)

**Classification Criteria:**

| Color | Priority | Criteria | Wait Time |
|-------|----------|----------|-----------|
| 🔴 RED | Emergency | Life-threatening symptoms | Immediate |
| 🟡 YELLOW | Urgent | Serious but stable | 30-60 min |
| 🟢 GREEN | Standard | Non-urgent | 1-4 hours |
| 🔵 BLUE | Low | Minor issues | 4+ hours |

### 4.3 Agent 3: Routing Agent

**Purpose:** Direct patient to appropriate department with preliminary orders.

**Input:** Anamnesis + TriageClassification

**Processing:**
- Match symptoms and classification to department
- Search for applicable preliminary orders
- Check for contraindications (allergies)
- Generate staff notes

**Output:** Routing object

**Tools:** ChromaDB search (routing_rules, preliminary_orders collections)

**Routing Examples:**

| Symptoms | Classification | Route To |
|----------|----------------|----------|
| Chest pain, cardiac symptoms | RED | Cardiology |
| Abdominal pain, fever | YELLOW | General Surgery |
| Fracture, trauma | YELLOW | Orthopedics |
| Fever, cough, general illness | GREEN | General Practice |
| Minor cut, no bleeding | BLUE | General Practice |

---

## 5. Data Models

### 5.1 Anamnesis

```python
class Anamnesis(BaseModel):
    chief_complaint: str          # Main reason for visit
    onset: str                    # When symptoms started
    duration: str | None          # How long symptoms lasted
    pain_scale: int | None        # 1-10 severity
    pain_type: str | None         # sharp, dull, pressure, burning
    location: str | None          # Body location
    radiation: str | None         # Where pain spreads
    associated_symptoms: list[str] # Other symptoms
    medical_history: list[str]    # Past conditions
    current_medications: list[str] # Active medications
    allergies: list[str]          # Known allergies
```

### 5.2 TriageClassification

```python
class TriageClassification(BaseModel):
    color: Literal["RED", "YELLOW", "GREEN", "BLUE"]
    priority: Literal["EMERGENCY", "URGENT", "STANDARD", "LOW"]
    reasoning: str                # Why this classification
    risk_factors: list[str]       # Identified risks
    matched_protocols: list[str]  # Protocols used for decision
```

### 5.3 Routing

```python
class Routing(BaseModel):
    department: str               # Cardiology, Orthopedics, etc.
    doctor_type: str              # Cardiologist, GP, etc.
    urgency: Literal["Immediate", "Within 30 min", "Within 1 hour", "Standard"]
    room_type: str | None         # Emergency bay, consultation room
    preliminary_orders: list[str] # Recommended initial orders
    contraindications: list[str]  # Things to avoid (allergies)
    notes_for_staff: str          # Summary for receiving staff
```

### 5.4 TriageResult (Final Output)

```python
class TriageResult(BaseModel):
    timestamp: datetime
    anamnesis: Anamnesis
    classification: TriageClassification
    routing: Routing
```

---

## 6. Predefined Anamnesis Questions

The chat interface asks these questions in order:

| # | Question | Maps To |
|---|----------|---------|
| 1 | What brings you in today? | chief_complaint |
| 2 | When did this start? | onset |
| 3 | On a scale of 1-10, how severe is it? | pain_scale |
| 4 | Where exactly is the problem located? | location |
| 5 | Does the pain spread anywhere else? | radiation |
| 6 | Any other symptoms? (dizziness, nausea, fever, etc.) | associated_symptoms |
| 7 | Do you have any medical conditions? | medical_history |
| 8 | What medications are you currently taking? | current_medications |
| 9 | Do you have any allergies? | allergies |

---

## 7. ChromaDB Collections

### 7.1 triage_protocols

Manchester Triage criteria and symptom-to-classification mappings.

**Example documents:**
```
"RED: Chest pain with diaphoresis, radiation to arm/jaw, or shortness of breath - possible ACS"
"RED: Severe respiratory distress, SpO2 < 92%, cyanosis"
"RED: Uncontrolled bleeding, signs of shock"
"YELLOW: Abdominal pain with fever and localized tenderness"
"YELLOW: Moderate respiratory symptoms, SpO2 92-95%"
"GREEN: Minor injuries, stable vital signs, low-grade fever"
"BLUE: Minor cuts without active bleeding, mild cold symptoms"
```

### 7.2 routing_rules

Symptom-to-department mappings.

**Example documents:**
```
"Chest pain, cardiac symptoms, arrhythmia → Cardiology"
"Fractures, dislocations, sprains, trauma → Orthopedics"
"Abdominal pain with surgical indicators → General Surgery"
"Pediatric patient (age < 18) → Pediatrics"
"Pregnancy-related symptoms → Obstetrics"
"General illness, fever, infection, unspecified → General Practice"
```

### 7.3 preliminary_orders

Standard initial orders by condition type.

**Example documents:**
```
"Cardiac chest pain: 12-lead ECG within 10 min, Troponin I/T, CBC, BMP, continuous monitoring"
"Respiratory distress: Pulse oximetry, chest X-ray, ABG if SpO2 < 92%"
"Abdominal pain: CBC, CMP, lipase, urinalysis, consider CT abdomen"
"Trauma: X-ray affected area, tetanus status, wound care supplies"
```

---

## 8. API Specification

### 8.1 POST /api/chat

Send a message in the anamnesis conversation.

**Request:**
```json
{
  "session_id": "abc123",
  "message": "my chest hurts"
}
```

**Response:**
```json
{
  "session_id": "abc123",
  "question_number": 2,
  "next_question": "When did this start?",
  "is_complete": false
}
```

### 8.2 POST /api/process

Process completed anamnesis through Triage and Routing agents.

**Request:**
```json
{
  "session_id": "abc123"
}
```

**Response:**
```json
{
  "status": "processing",
  "job_id": "xyz789"
}
```

### 8.3 GET /api/result/{job_id}

Get triage result.

**Response:**
```json
{
  "timestamp": "2026-01-13T10:30:00Z",
  "anamnesis": { ... },
  "classification": {
    "color": "RED",
    "priority": "EMERGENCY",
    "reasoning": "...",
    "risk_factors": [...]
  },
  "routing": {
    "department": "Cardiology",
    "urgency": "Immediate",
    "preliminary_orders": [...],
    "contraindications": [...],
    "notes_for_staff": "..."
  }
}
```

---

## 9. Non-Functional Requirements

### 9.1 Performance

- Chat response time: < 500ms per message
- Triage processing time: < 30 seconds total
- Concurrent users: 10 simultaneous sessions (MVP)

### 9.2 Reliability

- System uptime: 99% (MVP)
- Graceful error handling with user-friendly messages
- Automatic retry for transient LLM API failures

### 9.3 Security

- API key authentication
- No patient data stored after session ends
- Session data cleared after 24 hours

---

## 10. Project Structure

```
triage-ai/
├── main.py                  # FastAPI application
├── agents/
│   ├── __init__.py
│   ├── anamnesis.py         # Anamnesis Agent
│   ├── triage.py            # Triage Agent
│   └── routing.py           # Routing Agent
├── models/
│   ├── __init__.py
│   └── schemas.py           # Pydantic models
├── db/
│   ├── __init__.py
│   ├── vector_store.py      # ChromaDB setup
│   └── seed_data.py         # Protocol seeding script
├── chat/
│   ├── __init__.py
│   └── questions.py         # Predefined questions
├── static/                  # Frontend (React build)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── data/
│   └── protocols/           # Protocol text files
├── tests/
│   └── test_agents.py
├── Dockerfile
├── requirements.txt
├── render.yaml
└── README.md
```

---

## 11. MVP Scope

### 11.1 Included in MVP

- Chat interface with 9 predefined questions
- Three-agent sequential pipeline (Anamnesis → Triage → Routing)
- Manchester Triage classification (RED/YELLOW/GREEN/BLUE)
- Department routing with preliminary orders
- ChromaDB with ~30 seeded protocols
- Allergy/contraindication checking
- Simple React chat UI
- Deployment on Render

### 11.2 Future Enhancements (Post-MVP)

- Dynamic follow-up questions based on symptoms
- Patient identification and history lookup
- Integration with hospital EHR systems
- Multi-language support (Portuguese, Spanish)
- Voice input option
- Analytics dashboard
- PDF report generation
- Waiting time estimation

---

## 12. Development Timeline

| Time Block | Deliverables |
|------------|--------------|
| **Sat AM (4 hrs)** | Project setup, Pydantic models, predefined questions, chat flow |
| **Sat PM (4 hrs)** | Anamnesis Agent, ChromaDB setup, seed triage protocols |
| **Sun AM (4 hrs)** | Triage Agent, Routing Agent, connect pipeline |
| **Sun PM (4 hrs)** | React chat UI, API endpoints, deploy to Render |

---

## 13. Success Criteria

The MVP is complete when:

1. User can answer 9 questions via chat interface
2. System returns correct triage color based on symptoms
3. System routes to appropriate department
4. Contraindications are flagged (allergies)
5. Results display in a clear, readable format
6. Application is deployed and accessible via URL

---

## 14. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2026 | Diego Araujo | Initial PDF-based approach |
| 2.0 | Jan 2026 | Diego Araujo | Updated to chat-based anamnesis with 3-agent pipeline |