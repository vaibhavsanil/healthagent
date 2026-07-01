# Implementation Plan - Multilingual Agentic Healthcare Chatbot

We will develop a primary healthcare agentic chatbot supporting **English, Hindi, and Kannada**. The system will triage patient symptoms, provide primary care guidance (with appropriate medical disclaimers), and route users to relevant doctors. 

The demo will feature:
1. **Patient Triage Portal (Gradio)**: A multilingual chatbot interface.
2. **Doctor Referral Dashboard (Gradio)**: A panel where mock doctors can view referrals, review patient details, chat transcripts, and manage consultations.
3. **Admin Configuration Panel (Gradio)**: For changing LLM providers (Gemini, OpenAI, Ollama) and entering API keys dynamically.
4. **LangGraph Backend**: Orchestrates the multi-turn diagnostic and triage conversation.
5. **Database Storage**: SQLite database (shared via volume) to persist patient chats, triage records, and doctor referral status.
6. **Docker Compose Setup**: Pre-configured environment for easy deployment.

---

## User Review Required

> [!IMPORTANT]
> **API Credentials**: To test the frontier models, you will need to provide your `GEMINI_API_KEY` and/or `OPENAI_API_KEY` in a `.env` file or directly via the Admin panel in the web interface.
> For local LLM execution, the system will attempt to connect to Ollama. If running locally, you must have Ollama running with a model pulled (e.g., `llama3` or `mistral`).

> [!NOTE]
> We will use **SQLite** as the database backend. It is self-contained, light, and perfectly suited for this demo, storing patient records and referral status persistently.

---

## Proposed Changes

We will create a modular project structure in the `/home/vaibhav/cce/project1` workspace.

```
/home/vaibhav/cce/project1/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── plan/
│   └── implementation_plan.md  # Copy of this implementation plan
└── app/
    ├── __init__.py
    ├── main.py            # Gradio Web Interface (Patient, Doctor, Config tabs)
    ├── config.py          # App settings & LLM initializers
    ├── database.py        # SQLite Database connection and queries
    └── backend/
        ├── __init__.py
        ├── agent.py       # LangGraph triage workflow definition
        ├── prompts.py     # System instructions and translation helpers
        └── llm.py         # Factory for ChatOpenAI, ChatGemini, and ChatOllama
```

### 1. Configuration & Dependency Layer

#### [NEW] [requirements.txt](file:///home/vaibhav/cce/project1/requirements.txt)
Define backend packages: `langgraph`, `langchain`, `langchain-openai`, `langchain-google-genai`, `langchain-community`, `gradio`, `sqlalchemy`, `python-dotenv`.

#### Local Development Environment (`venv`)
We will initialize a local Python virtual environment (`venv`) to install dependencies locally for linting, autocompletion, and testing:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### [NEW] [Dockerfile](file:///home/vaibhav/cce/project1/Dockerfile)
Build file for the Gradio and LangGraph application.

#### [NEW] [docker-compose.yml](file:///home/vaibhav/cce/project1/docker-compose.yml)
Compose file defining the `web` application and an optional `ollama` service.

#### [NEW] [.env.example](file:///home/vaibhav/cce/project1/.env.example)
Template environment configuration for API keys.

---

### 2. Database & Storage Layer

#### [NEW] [database.py](file:///home/vaibhav/cce/project1/app/database.py)
SQLAlchemy models for:
- `PatientSession`: Keeps track of active conversations, language preference, and triage status.
- `TriageRecord`: Symptom logs, age, gender, severity index, and proposed diagnosis.
- `Referral`: Connects a patient triage record to a doctor specialty (General Physician, Cardiologist, Pediatrician, etc.) with states `PENDING`, `ACCEPTED`, `COMPLETED`.

---

### 3. LLM & Agent Backend (LangGraph)

#### [NEW] [llm.py](file:///home/vaibhav/cce/project1/app/backend/llm.py)
A factory to return the correct LangChain chat model based on the active config:
- **Gemini**: `ChatGoogleGenerativeAI`
- **OpenAI**: `ChatOpenAI`
- **Ollama**: `ChatOllama`

#### [NEW] [prompts.py](file:///home/vaibhav/cce/project1/app/backend/prompts.py)
System prompts localized for **English**, **Hindi**, and **Kannada** to ensure cultural nuance and proper medical phrasing.

#### [NEW] [agent.py](file:///home/vaibhav/cce/project1/app/backend/agent.py)
A LangGraph state machine with the following nodes:
1. `Triage Agent`: Gathers basic info (age, gender, main symptoms, duration, severity) empathetically in the selected language.
2. `Diagnosis Agent`: Reviews collected information to suggest potential causes (strictly disclaimed as advisory), assigns a severity category (Low/Medium/High), and suggests a doctor specialty.
3. `Referral Agent`: Proposes connecting to a doctor and handles the referral creation when confirmed by the patient.

---

### 4. Frontend Interface (Gradio)

#### [NEW] [main.py](file:///home/vaibhav/cce/project1/app/main.py)
A dashboard containing three tabs:
1. **Patient Consultation**:
   - Language selector flags/buttons (English, Hindi, Kannada).
   - Conversational chat window.
   - Interactive forms to capture emergency bypasses.
   - Referral booking status card.
2. **Doctor Referral Portal**:
   - Active lists of referrals grouped by specialty (Cardiology, Pediatrics, General Medicine, etc.).
   - Patient history details, AI triage report, and chat transcript.
   - "Consult Remotely" window where the doctor can message back and issue prescriptions.
3. **Settings Panel**:
   - Provider selection dropdown.
   - Live fields to input API Keys.
   - Connection validation status check.

---

## Verification Plan

### Automated Tests
- We will write a validation script `test_backend.py` to verify the LangGraph agent runs locally and generates the correct state transitions.
- We will run the python application to verify Gradio loads correctly.

### Manual Verification
- Launch the web app using `docker-compose up --build`.
- Access the Gradio web interface in the browser.
- Perform a simulated patient flow using the following language-specific test cases:

#### Test Case 1: Low/Medium Severity (General Physician)
*   **English**:
    *   *Query*: "Hello, I have a mild fever and a sore throat since yesterday."
    *   *Expected behavior*: System triages as low/medium severity, recommends general care, and suggests scheduling a remote consultation with a General Physician.
*   **Hindi**:
    *   *Query*: "नमस्ते, मुझे कल से हल्का बुखार और गले में खराश है।"
    *   *Expected behavior*: System responds in Hindi, conducts triaging, and suggests General Physician.
*   **Kannada**:
    *   *Query*: "ನಮಸ್ಕಾರ, ನನಗೆ ನಿನ್ನೆಯಿಂದ ಲಘು ಜ್ವರ ಮತ್ತು ಗಂಟಲು ನೋವು ಇದೆ."
    *   *Expected behavior*: System responds in Kannada, conducts triaging, and suggests General Physician.

#### Test Case 2: High Severity (Cardiologist)
*   **English**:
    *   *Query*: "Hi, I have severe chest pain that spreads to my left arm, and I am sweating a lot."
    *   *Expected behavior*: System immediately recognizes high severity, flags it, and recommends emergency care or remote connection to a Cardiologist.
*   **Hindi**:
    *   *Query*: "नमस्ते, मेरे सीने में तेज दर्द हो रहा है जो मेरे बाएं हाथ तक जा रहा है, और मुझे बहुत पसीना आ रहा है।"
    *   *Expected behavior*: System responds in Hindi, identifies critical symptoms, and routes to Cardiology.
*   **Kannada**:
    *   *Query*: "ನಮಸ್ಕಾರ, ನನ್ನ ಎದೆಯಲ್ಲಿ ತೀವ್ರವಾದ ನೋವು ಕಾಣಿಸಿಕೊಂಡಿದೆ ಮತ್ತು ಅದು ಎಡಗೈಗೆ ಹರಡುತ್ತಿದೆ, ತುಂಬಾ ಬೆವರುತ್ತಿದೆ."
    *   *Expected behavior*: System responds in Kannada, identifies critical symptoms, and routes to Cardiology.
