# Triage AI Complete Data Flow Guide

## Phase 1: Application Startup

```
1. main.py line 1-11
   |
   Import modules
   Load .env file (TARS_API_KEY and TARS_API_URL loaded here)
   |
2. main.py line 61-80 (@asynccontextmanager lifespan)
   |
   STARTUP EVENT TRIGGERED
   |
   Line 66: app.state.vector_store = VectorStore()
   +- Goes to: db/vector_store.py line 18-31
   +- What happens:
   |  +- Initializes ChromaDB PersistentClient
   |  +- Creates/loads 3 collections:
   |  |  +- triage_protocols (29 documents)
   |  |  +- routing_rules (31 documents)
   |  |  +- preliminary_orders (22 documents)
   |  +- Returns VectorStore instance
   |
   Line 70: app.state.triage_crew = TriageCrew(app.state.vector_store)
   +- Goes to: agents/crew.py line 111-125
   +- What happens:
   |  +- Creates TriageCrew instance
   |  +- Initializes LLM with TARS API (OpenAI-compatible)
   |  +- Stores reference to ChromaDB vector_store
   |  +- Ready to create agents on demand
   |
   Application is now READY

- Vector Store initialized with 82 protocols
- CrewAI orchestrator ready
- TARS LLM client configured
```

---

## Phase 2: User Starts Session

```
FRONTEND API CALL:
POST /api/session
  (no body needed)

main.py line 114-129 (@app.post("/api/session"))
  |
  Line 122: session_id = str(uuid.uuid4())
  | Creates unique session ID
  |
  Line 123: sessions[session_id] = SessionData(session_id=session_id)
  | Goes to: models/schemas.py
  | Creates new SessionData object with:
  | +- session_id
  | +- created_at = now
  | +- current_question = 0 (language selection)
  | +- language = None (not set yet)
  | +- answers = {} (empty dict)
  | +- is_complete = False
  +- Stored in: sessions dict (in-memory storage)
  |
  Line 125-129: Return response
  +- session_id: "abc123-def456..."
  +- language_options: ["en", "es", "pt-BR"]
  +- is_language_selection: True

FRONTEND receives session_id -> stores it for next requests
```

---

## Phase 3: Language Selection (First Question)

```
FRONTEND API CALL:
POST /api/chat
{
  "session_id": "abc123-def456...",
  "message": "es"  <- User selects Spanish
}

main.py line 132-192 (@app.post("/api/chat"))
  |
  Line 142: session = sessions.get(message.session_id)
  | Retrieves SessionData from in-memory dict
  |
  Line 151-164: if session.current_question == 0:
  | YES - this is language selection
  +- Line 155: session.language = message.message  <- Set to "es"
  +- Line 156: session.current_question = 1  <- Move to first medical question
  +- Line 162: get_first_question(session.language)
  |  +- Goes to: chat/questions.py
  |     Returns first question in Spanish
  |
  Return ChatResponse:
  +- next_question: "Cual es su nombre?"
  +- question_number: 1
  +- is_complete: False

FRONTEND displays first medical question in Spanish
```

---

## Phase 4: Answer Questions (14 total)

```
LOOP x 14 times:

FRONTEND API CALL (Example: Question 2):
POST /api/chat
{
  "session_id": "abc123-def456...",
  "message": "Juan Garcia"  <- Patient's answer
}

main.py line 132-192 (@app.post("/api/chat"))
  |
  Line 142: session = sessions.get(message.session_id)
  | Retrieves current session
  |
  Line 167: session.answers[session.current_question] = message.message
  | Stores: session.answers[1] = "Juan Garcia"
  | In-memory storage for this session only
  |
  Line 170: session.current_question += 1  <- Move to question 2
  |
  Line 173: total_questions = get_total_questions()
  | Returns: 14 (from chat/questions.py)
  |
  Line 175: if session.current_question > total_questions:
  | NO - continue
  |
  Line 185: next_question_text = get_question_text(session.current_question, session.language)
  | Goes to: chat/questions.py
  | Gets question 2 in Spanish
  |
  Return ChatResponse:
  +- next_question: "Cuando nacio?" (When were you born?)
  +- question_number: 2
  +- is_complete: False

REPEAT for questions 3-14...

After Question 14:
  |
  Line 175: if session.current_question (15) > total_questions (14):
  | YES
  +- Line 176: session.is_complete = True
  +- Return is_complete: True

FRONTEND: All questions answered -> Show "Process" button
```

---

## Phase 5: The Main Processing - CrewAI Orchestration

```
FRONTEND API CALL:
POST /api/process
{
  "session_id": "abc123-def456..."
}

main.py line 195-251 (@app.post("/api/process"))
  |
  Line 205: session = sessions.get(request.session_id)
  | Retrieve completed session with all 14 answers
  +- session.answers = {
  |   1: "Juan Garcia",
  |   2: "1970-05-15",
  |   3: "+34 912345678",
  |   ...
  |   14: "No"
  | }
  +- session.language = "es"
  +- session.is_complete = True
  |
  Line 223: await app.state.triage_crew.process(
              session.answers,
              language=session.language
            )

  ================================================================
       ENTERS AGENTS/CREW.PY - THE MAGIC HAPPENS
  ================================================================
```

---

## Phase 6: Agent 1 - Anamnesis (Data Structuring)

```
agents/crew.py line 226: anamnesis_crew.kickoff()
  |
  Line 304-340: Task 1 - Extract anamnesis
  +- Agent created: _create_anamnesis_agent(language="es")
  +- Role: "Medical Data Extraction Specialist"
  +- Goal: "Extract and structure patient medical information in Spanish"
  +- LLM: TARS API via CrewAI LLM (model="openai/tars-latest")
  |
  +- Task description built from:
     Line 262-293: _build_anamnesis_prompt()
     +- Builds Q&A pairs from session.answers
     +- Constructs JSON schema prompt
     +- Keeps all medical terms in Spanish
  |
  ================================================================
    LLM CALL #1: TARS API (OpenAI-compatible)
  ================================================================

  +- Request goes to: https://api.router.tetrate.ai/v1
  +- Uses: TARS_API_KEY from .env
  +- Model: tars-latest (via OpenAI-compatible endpoint)
  +- Processing time: ~3 seconds
  +- Returns: Structured JSON with Anamnesis data

  |
  Line 396: anamnesis_data = self._extract_json(str(anamnesis_result))
  | Parses JSON response
  |
  Line 397: anamnesis = Anamnesis(**anamnesis_data)
  | Creates Anamnesis Pydantic model
  | Validates all fields
  +- patient_name: "Juan Garcia"
  +- date_of_birth: "1970-05-15"
  +- chief_complaint: "dolor en el pecho"
  +- pain_scale: 8
  +- associated_symptoms: ["mareos", "sudoracion"]
  +- allergies: ["aspirina"]

Agent 1 COMPLETE: Structured medical data in Spanish
```

---

## Phase 7: Agent 2 - Triage (Classification)

```
agents/crew.py line 344-377: triage_crew.kickoff()
  |
  Line 341-377: Task 2 - Classify with Manchester Protocol
  +- Agent created: _create_triage_agent(language="es")
  +- Role: "Emergency Triage Specialist"
  +- Goal: "Classify patient urgency using Manchester Triage Protocol"
  +- Tools: [self.triage_tool]  <- Can search ChromaDB
  |
  ================================================================
    AGENT USES TOOL: search_triage_protocols
  ================================================================

  +- Line 61-71: TriageProtocolSearchTool._run()
  +- Query: "chest pain with diaphoresis and dizziness"
  +- Goes to: db/vector_store.py
  |  +- ChromaDB searches semantic similarity
  |  +- Returns top 5 matching protocols:
  |  |  [
  |  |    "RED: Chest pain with diaphoresis, radiation to arm/jaw...",
  |  |    "RED: Severe respiratory distress, SpO2 < 92%...",
  |  |    ...
  |  |  ]
  |  +- Processing time: ~100ms
  +- Tool result returned to Agent
  |
  ================================================================
    LLM CALL #2: TARS API with Tool Results
  ================================================================

  +- LLM sees:
  |  +- Patient symptoms
  |  +- Top 5 matching protocols from vector search
  |  +- Classification criteria (RED/YELLOW/GREEN/BLUE)
  +- Processing time: ~5 seconds
  +- Returns: JSON with classification
     {
       "color": "RED",
       "reasoning": "Dolor toracico con diaforesis sugiere...",
       "risk_factors": ["SCA", "infarto"],
       "matched_protocols": ["RED: Chest pain with diaphoresis..."]
     }
  |
  Line 401-408: Parse and create TriageClassification
  | Output: TriageClassification object
  | +- color: RED
  | +- priority: EMERGENCY
  | +- reasoning: in Spanish
  | +- risk_factors: in Spanish

Agent 2 COMPLETE: RED/YELLOW/GREEN/BLUE classification with reasoning
```

---

## Phase 8: Agent 3 - Routing (Department Assignment)

```
agents/crew.py line 414-451: routing_crew.kickoff()
  |
  Line 410-451: Task 3 - Route and generate orders
  +- Agent created: _create_routing_agent(language="es")
  +- Role: "Hospital Routing Specialist"
  +- Goal: "Route patients to appropriate departments"
  +- Tools: [self.routing_tool, self.orders_tool]  <- 2 tools available

  |
  ================================================================
    AGENT USES TOOL #1: search_routing_rules
  ================================================================

  +- Query: "chest pain cardiac symptoms"
  +- Goes to: db/vector_store.py
  +- ChromaDB returns matching routing rules:
  |  [
  |    "Chest pain, cardiac symptoms -> Cardiology",
  |    "Arrhythmia, palpitations -> Cardiology",
  |    ...
  |  ]
  +- Processing time: ~100ms

  |
  ================================================================
    AGENT USES TOOL #2: search_preliminary_orders
  ================================================================

  +- Query: "Acute Coronary Syndrome cardiac chest pain"
  +- Goes to: db/vector_store.py
  +- ChromaDB returns matching order sets:
  |  [
  |    "ACS: 12-lead ECG within 10 min, Troponin I/T, CBC, BMP...",
  |    ...
  |  ]
  +- Processing time: ~100ms

  |
  ================================================================
    LLM CALL #3: TARS API with Routing Info
  ================================================================

  +- LLM sees:
  |  +- Anamnesis (patient data + allergies)
  |  +- TriageClassification (RED priority)
  |  +- Matching routing rules
  |  +- Preliminary orders
  +- WARNING: "NO ASPIRINA - Alergia del paciente"
  +- Processing time: ~7 seconds
  +- Returns: Routing JSON
     {
       "department": "Cardiologia",
       "doctor_type": "Cardiologo",
       "urgency": "Inmediato",
       "preliminary_orders": [
         "ECG de 12 derivaciones",
         "Troponina I y T",
         ...
       ],
       "contraindications": ["NO ASPIRINA"],
       "notes_for_staff": "..."
     }
  |
  Line 440-453: Parse and create Routing object

Agent 3 COMPLETE: Department, urgency, orders, contraindications
```

---

## Phase 9: Final Result Assembly

```
main.py line 226-241 (@app.post("/api/process"))
  |
  Line 226-229: All 3 agents have completed
  | Returns:
  | +- anamnesis: Anamnesis object (structured patient data)
  | +- classification: TriageClassification (RED/YELLOW/GREEN/BLUE)
  | +- routing: Routing object (department, orders, etc.)
  |
  Line 234-239: Create final TriageResult
  | Combines all 3 agent outputs into one result object
  +- session_id
  +- anamnesis
  +- classification
  +- routing
  |
  Line 241: job_results[job_id] = result
  | Store in in-memory dict for retrieval

PROCESSING COMPLETE - Result stored and ready for retrieval
```

---

## Phase 10: Frontend Retrieves Result

```
FRONTEND API CALL:
GET /api/result/{job_id}

main.py line 254-275 (@app.get("/api/result/{job_id}"))
  |
  Line 264: result = job_results.get(job_id)
  | Retrieve from in-memory dict
  |
  Line 266: return ResultResponse(status="completed", result=result)
  | Return full result to frontend
  +- anamnesis: { patient data in Spanish }
  +- classification: { RED, reasoning in Spanish }
  +- routing: { Cardiologia, orders in Spanish }

FRONTEND displays:
  +- RED - EMERGENCY
  +- Patient: Juan Garcia
  +- Chief Complaint: dolor en el pecho
  +- Route to: Cardiologia
  +- Urgency: Inmediato
  +- Orders: [ECG, Troponina, etc.]
  +- WARNING: NO ASPIRINA - Alergia
```

---

## Summary: Where LLM is Called

```
3 LLM CALLS TOTAL (via TARS API):

1. AGENT 1 - ANAMNESIS
    +- Input: 14 Q&A pairs from user
    +- Model: tars-latest (via OpenAI-compatible API)
    +- Time: ~3 seconds
    +- Output: Structured medical data

2. AGENT 2 - TRIAGE
    +- Input: Anamnesis + 5 matching protocols from ChromaDB
    +- Model: tars-latest (via OpenAI-compatible API)
    +- Tool: Vector search (ChromaDB)
    +- Time: ~5 seconds
    +- Output: RED/YELLOW/GREEN/BLUE classification

3. AGENT 3 - ROUTING
    +- Input: Anamnesis + Classification + routing rules + orders
    +- Model: tars-latest (via OpenAI-compatible API)
    +- Tools: 2 vector searches (ChromaDB)
    +- Time: ~7 seconds
    +- Output: Department, urgency, preliminary orders

TOTAL PROCESSING TIME: ~15-20 seconds
```

---

## Data Storage Overview

```
IN-MEMORY (Ephemeral - lost on restart):
+- sessions: dict[session_id -> SessionData]
|  +- Stores user answers for 14 questions
+- job_results: dict[job_id -> TriageResult]
|  +- Stores final triage results
+- Expires after 24 hours

CHROMADB (Persistent - survives restart):
+- triage_protocols (29 documents)
|  +- Manchester Triage criteria
+- routing_rules (31 documents)
|  +- Symptom-to-department mappings
+- preliminary_orders (22 documents)
   +- Standard medical orders

ENVIRONMENT:
+- .env file
   +- TARS_API_KEY (loaded at startup)
   +- TARS_API_URL (loaded at startup)
```

---

## Key Insights

### Why This Architecture?

1. **Multi-Agent Approach**
   - Each agent = one responsibility
   - Anamnesis = structuring
   - Triage = classifying
   - Routing = routing
   - Testable and maintainable

2. **RAG (Retrieval-Augmented Generation)**
   - Agents search ChromaDB before calling LLM
   - Makes LLM decisions more reliable
   - Uses vector embeddings for semantic search

3. **Multilingual from Start**
   - Language captured in session
   - Passed through all agents
   - All outputs in patient's language

4. **Stateless API Calls**
   - Each request includes session_id
   - Can scale horizontally
   - No server affinity needed

5. **TARS API (OpenAI-compatible)**
   - Uses standard OpenAI SDK format
   - CrewAI LLM wrapper handles routing
   - Easy to swap LLM providers

---

**Next Steps:**

- Run `python main.py` locally
- Use Postman/Insomnia to call `/api/session`
- Trace through the flow with print statements
- Monitor LLM calls via TARS API dashboard
