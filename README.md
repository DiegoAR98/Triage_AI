# Triage AI - Multi-Agent Medical Triage System

> **Status:** Production-ready MVP
> **Version:** 2.0
> **Deployed on:** [Render](https://render.com)
> **SRS Document:** [DevDocs/TriateAI_SRS.md](DevDocs/TriateAI_SRS.md)

---

## Overview

**Triage AI** is a multi-agent AI system that conducts patient anamnesis through a chat interface, classifies urgency using the **Manchester Triage Protocol** (RED/YELLOW/GREEN/BLUE), and intelligently routes patients to appropriate medical departments.

Built for the **Tetrate AI Buildathon**, powered by the **TARS API** (Tetrate Agent Router Service).

### Key Features

- **14-Question Chat Anamnesis** - Including demographics (name, DOB, emergency contact)
- **Multi-Agent Orchestration** - CrewAI-powered sequential pipeline (Anamnesis -> Triage -> Routing)
- **Manchester Triage Classification** - Evidence-based RED/YELLOW/GREEN/BLUE urgency assessment
- **Smart Department Routing** - 8 departments with preliminary medical orders
- **Allergy/Contraindication Checking** - Safety flags for known allergies
- **Fully Multilingual** - English, Spanish, Portuguese (Brazil), and Italian with full medical term translation
- **Live Production Deployment** - Running on Render, accessible via URL
- **CrewAI Agents** - Each agent is a specialized medical professional

---

## System Architecture

### High-Level Data Flow

```
+------------------------------------------------------------+
|                    TRIAGE AI SYSTEM                         |
+------------------------------------------------------------+
|                                                            |
|  FRONTEND (Vanilla JS, 4 Languages)                       |
|  +------------------------------------------------------+ |
|  | Language Selection -> Chat Interface -> Results Panel | |
|  +------------------------------------------------------+ |
|                          |                                 |
|                          v                                 |
|  FASTAPI BACKEND                                          |
|  +------------------------------------------------------+ |
|  | /api/session  /api/chat  /api/process  /api/result   | |
|  +------------------------------------------------------+ |
|                          |                                 |
|                          v                                 |
|  CREWAI ORCHESTRATION                                     |
|  +------------------------------------------------------+ |
|  |  Agent 1: Anamnesis       -> Structures patient data  | |
|  |  Agent 2: Triage          -> Manchester classification| |
|  |  Agent 3: Routing         -> Department assignment    | |
|  +------------------------------------------------------+ |
|                          |                                 |
|                          v                                 |
|  CHROMADB VECTOR SEARCH (3 Collections)                   |
|  +- triage_protocols: 29 Manchester criteria             |
|  +- routing_rules: 31 symptom-to-department mappings     |
|  +- preliminary_orders: 22 standard order sets           |
|                                                            |
|  LLM PROCESSING: TARS API (Tetrate Agent Router Service) |
|                                                            |
+------------------------------------------------------------+
```

### Technology Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| **Backend** | FastAPI 0.115.0+ | Async Python web framework |
| **Agent Orchestration** | CrewAI 1.0.0+ | Multi-agent coordination |
| **LLM** | TARS API (OpenAI-compatible) | Tetrate Agent Router Service |
| **Vector Database** | ChromaDB | In-memory vector search |
| **Data Validation** | Pydantic 2.x | Type-safe models |
| **Frontend** | Vanilla JS/HTML/CSS (Inter font) | Clinical-grade responsive UI |
| **Deployment** | Render (Free Tier) | Auto-scaling, HTTPS included |
| **Runtime** | Python 3.11.10 | Long-term support version |

---

## Multi-Language Support

### Supported Languages

- **English** (en)
- **Spanish** (es)
- **Portuguese (Brazil)** (pt-BR)
- **Italian** (it)

### What Gets Translated

1. **User Interface** - All buttons, labels, and messages
2. **Medical Questions** - All 14 anamnesis questions
3. **Agent Reasoning** - Triage classification explanations
4. **Clinical Orders** - Preliminary medical orders
5. **Medical Terminology** - Chief complaints, symptoms, conditions, medications

### Example

**Patient answers in Spanish:**
```
Q1: "Me duele el pecho"
Q2: "Hace como 2 horas"
Q3: "8"
Q4: "En el pecho"
Q5: "No"
Q6: "Mareos y sudoracion"
```

**Output (also in Spanish):**
```json
{
  "color": "ROJO",
  "reasoning": "Dolor toracico con diaforesis sugiere sindrome coronario agudo...",
  "preliminary_orders": ["ECG de 12 derivaciones", "Troponina I y T"],
  "department": "Cardiologia"
}
```

---

## Data Models (Pydantic)

### Anamnesis (Patient Medical History)

```python
class Anamnesis(BaseModel):
    language: str                      # Patient's selected language
    patient_name: str                  # Full name
    date_of_birth: str                 # YYYY-MM-DD format
    phone_number: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None

    # Medical Information (ALL in patient's language)
    chief_complaint: str               # Main symptom
    onset: str                         # When symptoms started
    duration: str | None
    pain_scale: int | None             # 1-10 severity
    pain_type: str | None
    location: str | None               # Body location
    radiation: str | None              # Where pain spreads
    associated_symptoms: list[str]     # Additional symptoms
    medical_history: list[str]         # Past conditions
    current_medications: list[str]
    allergies: list[str]
```

### TriageClassification (Urgency Assessment)

```python
class TriageClassification(BaseModel):
    color: Literal["RED", "YELLOW", "GREEN", "BLUE"]
    priority: Literal["EMERGENCY", "URGENT", "STANDARD", "LOW"]
    reasoning: str                     # Clinical explanation (in patient's language)
    risk_factors: list[str]            # Identified risks
    matched_protocols: list[str]       # Protocols applied
```

**Manchester Triage Colors:**

| Color | Priority | Criteria | Wait Time |
|-------|----------|----------|-----------|
| RED | EMERGENCY | Life-threatening (airway obstruction, severe hemorrhage, shock) | Immediate |
| YELLOW | URGENT | Serious but stable (high fever, severe pain, moderate respiratory distress) | 30 min |
| GREEN | STANDARD | Non-urgent (mild symptoms, stable vitals) | 1-4 hours |
| BLUE | LOW | Minor issues (small cuts, cold symptoms, chronic stable condition) | 4+ hours |

### Routing (Department Assignment)

```python
class Routing(BaseModel):
    department: str                    # Cardiology, Orthopedics, Surgery, etc.
    doctor_type: str                   # Specialist type (in patient's language)
    urgency: Literal["Immediate", "Within 30 min", "Within 1 hour", "Standard"]
    room_type: str | None              # ER Bay, ICU, Consultation Room (translated)
    preliminary_orders: list[str]      # Recommended tests & treatments
    contraindications: list[str]       # Safety warnings (e.g., allergies)
    notes_for_staff: str               # Clinical summary for receiving team
```

---

## CrewAI Agent Pipeline

Each agent is a specialized medical professional with specific tools and responsibilities.

### Agent 1: Anamnesis Specialist

**Role:** Medical Data Extraction Specialist
**Goal:** Extract and structure patient information in their language
**Tools:** None (LLM processing only)

**Processing:**
1. Receives raw chat responses
2. Converts to structured medical data
3. Keeps all medical terms in patient's language
4. Validates required fields
5. Returns `Anamnesis` Pydantic model

### Agent 2: Emergency Triage Specialist

**Role:** Emergency Triage Specialist
**Goal:** Classify urgency using Manchester Triage Protocol
**Tools:** `search_triage_protocols` (ChromaDB query)

**Processing:**
1. Receives structured Anamnesis
2. Queries ChromaDB for matching triage protocols
3. Applies Manchester criteria
4. Generates clinical reasoning
5. Returns `TriageClassification` (RED/YELLOW/GREEN/BLUE)

### Agent 3: Hospital Routing Specialist

**Role:** Hospital Routing Specialist
**Goal:** Route patient to appropriate department with preliminary orders
**Tools:**
- `search_routing_rules` (Find matching department)
- `search_preliminary_orders` (Get standard orders)

**Processing:**
1. Receives Anamnesis + TriageClassification
2. Queries ChromaDB for department routing rules
3. Searches for preliminary medical orders
4. Checks allergies for contraindications
5. Generates staff notes
6. Returns `Routing` object

---

## ChromaDB Collections (82 documents total)

### 1. triage_protocols (29 documents)

Manchester Triage criteria and symptom-to-classification mappings.

### 2. routing_rules (31 documents)

Symptom-to-department mappings for patient flow.

### 3. preliminary_orders (22 documents)

Standard initial medical orders by condition type.

---

## REST API Endpoints

### Session Management

#### `POST /api/session`
Create a new triage session.

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "language_options": ["en", "es", "pt-BR", "it"],
  "is_language_selection": true
}
```

### Chat Flow

#### `POST /api/chat`
Send a message (answer a question).

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "My chest hurts really bad"
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "question_number": 2,
  "next_question": "When did this start?",
  "is_complete": false
}
```

### Triage Processing

#### `POST /api/process`
Process completed anamnesis through triage pipeline.

#### `GET /api/result/{job_id}`
Retrieve final triage result.

### System Health

#### `GET /api/health`
Health check endpoint.

---

## Project Structure

```
Triage_AI/
|-- main.py                          # FastAPI app
|                                    # - Session management
|                                    # - Chat endpoint
|                                    # - Triage processing
|                                    # - Result retrieval
|
|-- agents/                          # CrewAI Agents
|   +-- crew.py                      # TriageCrew orchestrator
|                                    # - Agent definitions (Anamnesis, Triage, Routing)
|                                    # - Task orchestration
|                                    # - Tool integration
|
|-- models/                          # Pydantic Data Models
|   +-- schemas.py                   # Type definitions
|
|-- db/                              # Database & Vector Store
|   |-- vector_store.py              # ChromaDB wrapper
|   +-- seed_data.py                 # Data seeding script (82 protocols)
|
|-- chat/                            # Chat Flow
|   +-- questions.py                 # 14 questions x 4 languages
|
|-- static/                          # Frontend
|   |-- index.html                   # Chat UI
|   |-- app.js                       # Chat logic & translations
|   +-- styles.css                   # Styling
|
|-- requirements.txt                 # Dependencies (managed by CrewAI)
|-- render.yaml                      # Render deployment blueprint
|-- Dockerfile                       # Container deployment
|
|-- DevDocs/
|   +-- TriateAI_SRS.md              # Software Requirements Spec
|
+-- README.md                        # This file
```

---

## Deployment (Render)

### Deployment Steps

1. **Connect GitHub Repository**
   - Log in to Render Dashboard
   - Create -> Web Service
   - Select your GitHub repository

2. **Configure Build Settings**
   - Render auto-detects `render.yaml`
   - Build Command: `pip install -r requirements.txt && python -m db.seed_data`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables**
   - Add `TARS_API_KEY` from Tetrate
   - Add `TARS_API_URL` = `https://api.router.tetrate.ai/v1`
   - Keep `PYTHON_VERSION=3.11.10`

4. **Deploy**
   - Click "Create Web Service"
   - Render automatically builds and deploys

> **Note:** Render's free tier spins down after 15 minutes of inactivity, causing ~30 second cold starts on the next request. For production ER use, upgrade to a paid instance to avoid spin-down delays.

---

## Local Development

### Prerequisites

- Python 3.11.10+
- pip / venv
- TARS API credentials from Tetrate

### Quick Start

```bash
# Clone repo
git clone https://github.com/DiegoAR98/Triage_AI.git
cd Triage_AI

# Setup
python -m venv venv
.\venv\Scripts\Activate  # Windows
# OR
source venv/bin/activate  # macOS/Linux

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your TARS_API_KEY and TARS_API_URL

# Seed database
python -m db.seed_data

# Run
python main.py
```

Visit: **http://localhost:8000**

### Development Commands

```bash
# Run with auto-reload
uvicorn main:app --reload

# Run tests
pytest tests/

# Format code
black .

# Lint
ruff check .
```

---

## Comparison: SRS vs Implementation

### MVP Requirements

| Requirement | SRS Planned | Implemented |
|-------------|------------|------------|
| Chat interface | 9 questions | 14 questions (added demographics) |
| Three-agent pipeline | Anamnesis, Triage, Routing | CrewAI orchestrated |
| Manchester classification | RED/YELLOW/GREEN/BLUE | Full support |
| Department routing | Yes | 8 departments |
| ChromaDB protocols | ~30 docs | 82 total documents |
| Allergy checking | Yes | Contraindications flagged |
| React UI | Yes | Vanilla JS alternative |
| Render deployment | Yes | Live & accessible |

### Exceeded Expectations

| Feature | SRS Status | Implementation |
|---------|-----------|-----------------|
| Multi-language | Future enhancement | 4 languages (EN/ES/PT-BR/IT) |
| Demographic data | Not mentioned | Name, DOB, emergency contact |
| CrewAI orchestration | Not specified | Full agent coordination |
| Multilingual medical terms | Future enhancement | All terms fully translated |
| UI translations | Future enhancement | Complete 4-language UI |

---

## Security Notes

- **No persistent patient storage** - Sessions expire after 24 hours
- **Environment-based secrets** - API keys in .env, not in code
- **HTTPS on Render** - Automatic SSL certificate
- **CORS enabled** - Safe cross-origin requests

---

## Performance Metrics

| Operation | Time | Notes |
|-----------|------|-------|
| Chat response | ~200ms | Just API processing |
| Agent 1 (Anamnesis) | ~3s | LLM + JSON parsing |
| Agent 2 (Triage) | ~5s | LLM + vector search |
| Agent 3 (Routing) | ~7s | LLM + 2 vector searches |
| **Total pipeline** | ~15-20s | Entire triage process |
| Vector search | ~100ms | ChromaDB semantic search |

---

## License

MIT License - See LICENSE file

---

## Author

**Diego Araujo**
GitHub: [@DiegoAR98](https://github.com/DiegoAR98)

---

## Acknowledgments

- Tetrate team for the TARS API (Agent Router Service)
- Manchester Triage System creators
- Render for free deployment infrastructure
- CrewAI team for agent orchestration framework

---

**Built for the Tetrate AI Buildathon**

Last Updated: February 2026
