import os
import uuid
import gradio as gr
from langchain_core.messages import HumanMessage, AIMessage

from app.config import Config
from app.database import (
    init_db,
    get_or_create_session,
    update_session_language,
    add_chat_message,
    get_chat_history,
    create_triage_record,
    create_referral,
    get_pending_referrals,
    get_all_referrals,
    get_referral_by_id,
    update_referral_status
)
from app.backend.agent import agent_graph

# Initialize database
init_db()

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Force dark mode theme variables globally */
.gradio-container, .gradio-container *, :root {
    --body-background-fill: #11111b !important;
    --background-fill-primary: #1e1e2e !important;
    --background-fill-secondary: #11111b !important;
    --block-background-fill: #1e1e2e !important;
    --block-border-color: rgba(255, 255, 255, 0.08) !important;
    --border-color-primary: rgba(255, 255, 255, 0.08) !important;
    --border-color-accent: #89b4fa !important;
    --body-text-color: #cdd6f4 !important;
    --body-text-color-subdued: #bac2de !important;
    --block-title-text-color: #89b4fa !important;
    --block-label-text-color: #bac2de !important;
    --input-background-fill: #11111b !important;
    --input-text-color: #ffffff !important;
    --input-border-color: rgba(255, 255, 255, 0.1) !important;
}

body, .gradio-container {
    background: linear-gradient(135deg, #11111b 0%, #1e1e2e 50%, #11111b 100%) !important;
    font-family: 'Outfit', sans-serif !important;
    color: #cdd6f4 !important;
}

.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
    padding: 20px !important;
}

/* Headers */
#title-header {
    text-align: center;
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: rgba(30, 30, 46, 0.4);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px);
}

#title-header h1 {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    background: linear-gradient(90deg, #89b4fa, #f5c2e7, #a6e3a1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

#title-header p {
    color: #bac2de;
    font-size: 1.1rem;
}

/* Glassmorphic cards */
.glass-card {
    background: rgba(30, 30, 46, 0.4) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    backdrop-filter: blur(12px) !important;
    padding: 20px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
}

/* Sidebar Info styling (e.g. Session Details, Triage Diagnostics) */
.info-box {
    background: rgba(17, 17, 27, 0.75) !important;
    border-radius: 12px !important;
    padding: 15px !important;
    border-left: 4px solid #89b4fa !important;
    margin-bottom: 15px !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
}

.info-box h3 {
    color: #89b4fa !important;
    font-size: 1.15rem !important;
    margin-top: 0 !important;
    margin-bottom: 8px !important;
    font-weight: 600 !important;
}

.info-box p {
    color: #e6e9ef !important;
    font-size: 0.95rem !important;
    margin: 4px 0 !important;
}

.info-box b {
    color: #bac2de !important;
}

.info-box span {
    color: #ffffff !important;
}

.info-box code {
    background: rgba(0, 0, 0, 0.4) !important;
    color: #f5c2e7 !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
}

/* Force dark backgrounds on all group / box containers */
.gr-group, .gr-form, .group, .form, .block, .box, .dark-group, #referral-box, #review-panel {
    background-color: rgba(17, 17, 27, 0.6) !important;
    background: rgba(17, 17, 27, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
}

/* Force light text color on all Markdown prose */
.prose, .prose p, .prose h1, .prose h2, .prose h3, .prose h4, .prose h5, .prose h6, .prose ul, .prose li, .prose ol, .prose span, .prose strong {
    color: #cdd6f4 !important;
}

.prose h1, .prose h2, .prose h3 {
    color: #89b4fa !important;
    font-weight: 600 !important;
}

/* Chatbot bubbles styling overrides */
.gradio-container button.svelte-1e1jlin {
    background-color: transparent !important;
}

.gradio-container button[aria-label^="bot's message"],
.gradio-container button[aria-label^="bot's message"] *,
.svelte-1e1jlin[aria-label^="bot's message"],
.svelte-1e1jlin[aria-label^="bot's message"] * {
    background-color: rgba(17, 17, 27, 0.8) !important;
    background: rgba(17, 17, 27, 0.8) !important;
    color: #cdd6f4 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

.gradio-container button[aria-label^="user's message"],
.gradio-container button[aria-label^="user's message"] *,
.svelte-1e1jlin[aria-label^="user's message"],
.svelte-1e1jlin[aria-label^="user's message"] * {
    background: linear-gradient(90deg, #f5c2e7, #cba6f7) !important;
    color: #11111b !important;
}

/* Textboxes, Textareas, and Dropdowns styling */
.gradio-container input[type="text"], 
.gradio-container input[type="password"], 
.gradio-container textarea, 
.gradio-container select,
.gradio-container .dropdown {
    color: #ffffff !important;
    background-color: rgba(17, 17, 27, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* Labels and headers of fields */
.gradio-container .block-label, 
.gradio-container .block-info,
.gradio-container label span {
    color: #bac2de !important;
    font-weight: 500 !important;
}

/* Dropdown choice list styling */
.gradio-container .dropdown-menu,
.gradio-container .options {
    background-color: #1e1e2e !important;
    color: #ffffff !important;
}

/* Custom Buttons */
.lang-btn {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.lang-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 15px rgba(137, 180, 250, 0.2) !important;
}

.btn-primary {
    background: linear-gradient(90deg, #89b4fa, #b4befe) !important;
    color: #11111b !important;
    font-weight: 600 !important;
    border: none !important;
}

.btn-primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 15px rgba(137, 180, 250, 0.4) !important;
}

/* Tabs customization */
.tabs {
    border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.tab-nav button {
    color: #cdd6f4 !important;
    font-weight: 500 !important;
    font-size: 1rem !important;
}

.tab-nav button.selected {
    color: #89b4fa !important;
    border-bottom-color: #89b4fa !important;
}

/* Severity Indicator colors */
.severity-high {
    color: #f38ba8 !important;
    font-weight: bold !important;
}
.severity-medium {
    color: #f9e2af !important;
    font-weight: bold !important;
}
.severity-low {
    color: #a6e3a1 !important;
    font-weight: bold !important;
}
"""

WELCOME_MESSAGES = {
    "en": "Hello! I am your AI primary healthcare assistant. How can I help you today? Please share your age, gender, and what symptoms you are experiencing.",
    "hi": "नमस्ते! मैं आपका एआई प्राथमिक स्वास्थ्य सेवा सहायक हूँ। आज मैं आपकी क्या सहायता कर सकता हूँ? कृपया अपनी उम्र, लिंग और अपने लक्षणों के बारे में बताएं।",
    "kn": "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ AI ಪ್ರಾಥಮಿಕ ಆರೋಗ್ಯ ಸಹಾಯಕ. ಇವತ್ತು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು? ದಯವಿಟ್ಟು ನಿಮ್ಮ ವಯಸ್ಸು, ಲಿಂಗ ಮತ್ತು ರೋಗಲಕ್ಷಣಗಳ ವಿವರಗಳನ್ನು ತಿಳಿಸಿ."
}

def format_chat_for_gradio(session_id: str):
    """Loads chat history and formats it as [(user, bot)] for Gradio Chatbot."""
    db_history = get_chat_history(session_id)
    gradio_history = []
    
    # Pair up messages
    temp_user = None
    for sender, msg in db_history:
        if sender == "patient":
            temp_user = msg
        elif sender == "bot":
            if temp_user is not None:
                gradio_history.append((temp_user, msg))
                temp_user = None
            else:
                gradio_history.append((None, msg))
                
    if temp_user is not None:
        gradio_history.append((temp_user, None))
        
    return gradio_history

def start_new_session(lang: str):
    """Generates a new session ID, sets language, and adds first welcome message."""
    session_id = str(uuid.uuid4())
    get_or_create_session(session_id, lang)
    
    welcome_text = WELCOME_MESSAGES.get(lang, WELCOME_MESSAGES["en"])
    add_chat_message(session_id, "bot", welcome_text)
    
    chat_history = format_chat_for_gradio(session_id)
    status_md = get_session_status_markdown(session_id)
    
    return session_id, chat_history, status_md, gr.update(visible=False), ""

def get_session_status_markdown(session_id: str):
    """Generates sidebar HTML representation of the patient state from the session info."""
    session = get_or_create_session(session_id)
    
    lang_name = {"en": "English", "hi": "हिंदी (Hindi)", "kn": "ಕನ್ನಡ (Kannada)"}.get(session.language, "English")
    
    # Fetch latest triage record if exists
    latest_record = None
    if session.triage_records:
        # Get latest by id
        latest_record = sorted(session.triage_records, key=lambda r: r.id)[-1]
        
    severity_class = "severity-low"
    severity_val = "None"
    age_val = "Not Gathered"
    gender_val = "Not Gathered"
    symptoms_val = "Gathering..."
    duration_val = "Not Gathered"
    specialty_val = "Pending evaluation"
    stage_val = "Gathering Details"
    
    if latest_record:
        severity_val = latest_record.severity or "Low"
        if severity_val == "High":
            severity_class = "severity-high"
        elif severity_val == "Medium":
            severity_class = "severity-medium"
        else:
            severity_class = "severity-low"
            
        age_val = str(latest_record.age) if latest_record.age else "Not Gathered"
        gender_val = latest_record.gender or "Not Gathered"
        symptoms_val = latest_record.symptoms or "Gathering..."
        duration_val = latest_record.duration or "Not Gathered"
        specialty_val = latest_record.suggested_specialty or "General Physician"
        
        # Check referral
        if latest_record.referral:
            stage_val = f"Referred ({latest_record.referral.status})"
        else:
            stage_val = "AI Triaged / Diagnosed"
    else:
        # Check database records
        pass
        
    return f"""
    <div class="info-box">
        <h3>Session Details</h3>
        <p><b>Session ID:</b> <code style="font-size:0.8rem;">{session_id[:8]}...</code></p>
        <p><b>Active Language:</b> {lang_name}</p>
    </div>
    
    <div class="info-box">
        <h3>Triage Diagnostics</h3>
        <p><b>Status:</b> {stage_val}</p>
        <p><b>Patient Age:</b> {age_val}</p>
        <p><b>Gender:</b> {gender_val}</p>
        <p><b>Symptoms:</b> {symptoms_val}</p>
        <p><b>Duration:</b> {duration_val}</p>
        <p><b>Triage Severity:</b> <span class="{severity_class}">{severity_val}</span></p>
        <p><b>Recommended Doctor:</b> {specialty_val}</p>
    </div>
    """

def process_patient_chat(user_msg: str, chat_history, session_id: str):
    """Processes user input, updates state in DB, runs LangGraph, and updates UI."""
    if not user_msg.strip():
        return "", chat_history, get_session_status_markdown(session_id), gr.update(), ""
        
    # 1. Save user message to DB
    add_chat_message(session_id, "patient", user_msg)
    
    # 2. Re-load session details and chat history
    session = get_or_create_session(session_id)
    db_history = get_chat_history(session_id)
    
    # Convert db history to message format for LangGraph
    messages = []
    for sender, msg in db_history:
        if sender == "patient":
            messages.append(HumanMessage(content=msg))
        elif sender == "bot":
            messages.append(AIMessage(content=msg))
            
    # Gather configuration parameters
    provider = Config.DEFAULT_PROVIDER
    if provider == "deepseek":
        api_key = Config.DEEPSEEK_API_KEY
        model_name = Config.DEEPSEEK_MODEL
    elif provider == "gemini":
        api_key = Config.GEMINI_API_KEY
        model_name = Config.GEMINI_MODEL
    elif provider == "openai":
        api_key = Config.OPENAI_API_KEY
        model_name = Config.OPENAI_MODEL
    else:
        api_key = ""
        model_name = Config.OLLAMA_MODEL
        
    # Prepare current patient info
    latest_record = sorted(session.triage_records, key=lambda r: r.id)[-1] if session.triage_records else None
    
    patient_info = {
        "age": latest_record.age if latest_record else None,
        "gender": latest_record.gender if latest_record else None,
        "symptoms": latest_record.symptoms if latest_record else None,
        "duration": latest_record.duration if latest_record else None,
        "severity": latest_record.severity if latest_record else "Low"
    }
    
    triage_stage = "GATHERING"
    if latest_record:
        if latest_record.referral:
            triage_stage = "REFERRED"
        else:
            triage_stage = "DIAGNOSED" if latest_record.triage_summary else "GATHERING"
            
    # 3. Invoke LangGraph
    input_state = {
        "messages": messages,
        "language": session.language,
        "patient_info": patient_info,
        "triage_summary": latest_record.triage_summary if latest_record else "",
        "suggested_specialty": latest_record.suggested_specialty if latest_record else "",
        "triage_stage": triage_stage,
        "referral_required": latest_record.referral is not None if latest_record else False,
        "provider": provider,
        "api_key": api_key,
        "model_name": model_name
    }
    
    try:
        output_state = agent_graph.invoke(input_state)
    except Exception as e:
        # Return error gracefully in chat
        err_msg = f"System error communicating with LLM ({provider}): {str(e)}"
        add_chat_message(session_id, "bot", err_msg)
        chat_history = format_chat_for_gradio(session_id)
        return "", chat_history, get_session_status_markdown(session_id), gr.update(), ""
        
    # Get last message
    bot_reply = output_state["messages"][-1].content
    add_chat_message(session_id, "bot", bot_reply)
    
    # 4. Check if triage output has been finalized
    new_stage = output_state.get("triage_stage", "GATHERING")
    
    if new_stage == "DIAGNOSED" and triage_stage == "GATHERING":
        # Create triage record in database
        info = output_state["patient_info"]
        summary = output_state.get("triage_summary", "")
        specialty = output_state.get("suggested_specialty", "General Physician")
        severity = info.get("severity", "Low")
        
        create_triage_record(
            session_id=session_id,
            age=info.get("age"),
            gender=info.get("gender"),
            symptoms=info.get("symptoms"),
            duration=info.get("duration"),
            severity=severity,
            triage_summary=summary,
            suggested_specialty=specialty
        )
        
    # Refresh chat display
    chat_history = format_chat_for_gradio(session_id)
    status_md = get_session_status_markdown(session_id)
    
    # Show doctor referral card if DIAGNOSED
    updated_session = get_or_create_session(session_id)
    latest_rec = sorted(updated_session.triage_records, key=lambda r: r.id)[-1] if updated_session.triage_records else None
    
    show_referral_card = gr.update(visible=False)
    summary_text = ""
    
    if latest_rec and not latest_rec.referral:
        # Show prompt to connect to doctor
        show_referral_card = gr.update(visible=True)
        summary_text = f"### AI Diagnostic Summary & Recommendations\n\n{latest_rec.triage_summary}\n\n**Do you want to connect to a remote {latest_rec.suggested_specialty} now?**"
        
    return "", chat_history, status_md, show_referral_card, summary_text

def accept_remote_referral(session_id: str):
    """Creates a doctor referral in the database and updates status."""
    session = get_or_create_session(session_id)
    if not session.triage_records:
        return gr.update(visible=False), "Error: No triage record found to refer.", get_session_status_markdown(session_id)
        
    latest_rec = sorted(session.triage_records, key=lambda r: r.id)[-1]
    referral = create_referral(latest_rec.id, latest_rec.suggested_specialty)
    
    # Add bot confirmation in chat
    confirm_text = {
        "en": f"I have successfully scheduled a remote consultation with a {latest_rec.suggested_specialty}. A doctor will evaluate your case shortly.",
        "hi": f"मैंने {latest_rec.suggested_specialty} के साथ एक रिमोट परामर्श सफलतापूर्वक निर्धारित कर दिया है। एक डॉक्टर जल्द ही आपके मामले का मूल्यांकन करेंगे।",
        "kn": f"ನಾನು {latest_rec.suggested_specialty} ಅವರೊಂದಿಗೆ ದೂರಸ್ಥ ಸಮಾಲೋಚನೆಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಕಾಯ್ದಿರಿಸಿದ್ದೇನೆ. ಒಬ್ಬ ವೈದ್ಯರು ಶೀಘ್ರದಲ್ಲೇ ನಿಮ್ಮ ಪ್ರಕರಣವನ್ನು ಪರಿಶೀಲಿಸಲಿದ್ದಾರೆ."
    }.get(session.language, f"Scheduled consultation with a {latest_rec.suggested_specialty}.")
    
    add_chat_message(session_id, "bot", confirm_text)
    
    chat_history = format_chat_for_gradio(session_id)
    status_md = get_session_status_markdown(session_id)
    
    success_msg = f"✅ Referral Request submitted! Doctor specialty: **{latest_rec.suggested_specialty}**."
    
    return gr.update(visible=False), success_msg, status_md, chat_history

# --- Doctor Portal Functions ---

def refresh_referral_list(specialty_filter: str):
    """Loads all pending referrals and returns a formatted choices list for the dropdown."""
    referrals = get_pending_referrals(specialty_filter)
    choices = []
    for ref in referrals:
        record = ref.triage_record
        session_id = record.session_id
        label = f"Ref #{ref.id} | {record.suggested_specialty} | Severity: {record.severity} | Patient: Age {record.age}, {record.gender}"
        choices.append((label, str(ref.id)))
        
    if not choices:
        return gr.update(choices=[], value=None, label="No Pending Referrals Found")
        
    return gr.update(choices=choices, value=None, label=f"Select Referral ({len(choices)} pending)")

def select_referral_to_review(referral_id_str: str):
    """Loads the selected referral details, patient chat transcript, and fills forms."""
    if not referral_id_str:
        return "", "", gr.update(visible=False), "", "PENDING"
        
    ref_id = int(referral_id_str)
    ref = get_referral_by_id(ref_id)
    if not ref:
        return "Referral not found.", "", gr.update(visible=False), "", "PENDING"
        
    record = ref.triage_record
    
    # Detail markdown
    patient_info_md = f"""
    ### 📋 Patient Details (Referral #{ref.id})
    *   **Age / Gender:** {record.age} years / {record.gender}
    *   **Severity Category:** **{record.severity}**
    *   **Symptoms:** {record.symptoms}
    *   **Duration:** {record.duration}
    *   **Requested Specialty:** **{record.suggested_specialty}**
    *   **Date Submitted:** {ref.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
    """
    
    # Triage Summary
    triage_summary_md = f"""
    ### 🩺 AI Diagnostic Assessment
    {record.triage_summary}
    """
    
    # Chat History Transcript
    chat_history = get_chat_history(record.session_id)
    transcript = "### 💬 Triage Conversation History\n\n"
    for sender, msg in chat_history:
        role = "Patient" if sender == "patient" else "AI Assistant"
        transcript += f"**{role}:** {msg}\n\n"
        
    return patient_info_md, triage_summary_md, gr.update(visible=True), transcript, ref.status

def save_doctor_consultation(referral_id_str: str, doctor_name: str, status: str, notes: str):
    """Saves doctor prescription notes and updates status in SQLite DB."""
    if not referral_id_str:
        return "❌ Please select a referral first.", gr.update()
        
    ref_id = int(referral_id_str)
    ref = get_referral_by_id(ref_id)
    if not ref:
        return "❌ Referral record not found.", gr.update()
        
    # Update status and save
    update_referral_status(ref_id, status, doctor_name, notes)
    
    # Send message to patient session notifying them of the update
    lang = ref.triage_record.session.language
    notify_msg = {
        "en": f"📢 Remote evaluation update from Dr. {doctor_name}:\nStatus: {status}\nDoctor Notes/Prescription:\n{notes}",
        "hi": f"📢 डॉ. {doctor_name} से दूरस्थ मूल्यांकन अपडेट:\nस्थिति (Status): {status}\nडॉक्टर के नोट्स/नुस्खा:\n{notes}",
        "kn": f"📢 ಡಾ. {doctor_name} ರಿಂದ ದೂರಸ್ಥ ಮೌಲ್ಯಮಾಪನ ಅಪ್ಡೇಟ್:\nಸ್ಥಿತಿ: {status}\nವೈದ್ಯರ ಟಿಪ್ಪಣಿಗಳು/ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್:\n{notes}"
    }.get(lang, f"Update from Doctor {doctor_name}")
    
    add_chat_message(ref.triage_record.session_id, "doctor", notify_msg)
    
    success_text = f"✅ Referral #{ref.id} successfully updated! Status changed to **{status}**."
    
    return success_text, gr.update()

# --- Settings Portal Functions ---

def test_llm_connection(provider, deepseek_key, gemini_key, openai_key, deepseek_model, gemini_model, openai_model, ollama_model, ollama_host):
    """Test LLM connection and return status message."""
    # Temporarily update config to test
    Config.update(provider, deepseek_key, gemini_key, openai_key, deepseek_model, gemini_model, openai_model, ollama_model, ollama_host)
    
    try:
        from app.backend.llm import get_llm
        # Get appropriate model
        if provider == "deepseek":
            api_key = deepseek_key
            model_name = deepseek_model
        elif provider == "gemini":
            api_key = gemini_key
            model_name = gemini_model
        elif provider == "openai":
            api_key = openai_key
            model_name = openai_model
        else:
            api_key = ""
            model_name = ollama_model
            
        llm = get_llm(
            provider=provider,
            api_key=api_key,
            model_name=model_name
        )
        # Test call
        test_msg = [HumanMessage(content="Hello. Reply with 'Connection successful!'")]
        res = llm.invoke(test_msg)
        return f"🟢 Connection Successful!\n\nResponse from {provider} model: '{res.content}'"
    except Exception as e:
        return f"🔴 Connection Failed:\n\n{str(e)}"

def apply_new_settings(provider, deepseek_key, gemini_key, openai_key, deepseek_model, gemini_model, openai_model, ollama_model, ollama_host):
    """Saves settings into Config class."""
    Config.update(provider, deepseek_key, gemini_key, openai_key, deepseek_model, gemini_model, openai_model, ollama_model, ollama_host)
    return "✅ Settings saved successfully!"


# --- Build Gradio Interface ---

with gr.Blocks(css=CUSTOM_CSS, theme=gr.themes.Default()) as demo:
    
    # Session ID stored in client-side state
    session_id_state = gr.State("")
    
    # Title Banner
    gr.HTML(
        """
        <div id="title-header">
            <h1>Citizen Primary Healthcare & Triage Agentic AI Assistant</h1>
            <p>Empowering citizens with Multi Agent & Multilingual AI-triage, diagnostics, and remote doctor consultations</p>
        </div>
        """
    )
    
    with gr.Tabs(elem_id="main-tabs"):
        
        # TAB 1: Patient Consultation
        with gr.Tab("Patient Portal", id="patient-tab"):
            with gr.Row():
                # Left Column: Config and Status
                with gr.Column(scale=4, elem_classes=["glass-card"]):
                    gr.Markdown("### 🌍 Select Language / ಭಾಷೆ ಆಯ್ಕೆ / भाषा चुनें")
                    with gr.Row():
                        btn_en = gr.Button("🇬🇧 English", variant="secondary", elem_classes=["lang-btn"])
                        btn_hi = gr.Button("🇮🇳 हिंदी (Hindi)", variant="secondary", elem_classes=["lang-btn"])
                        btn_kn = gr.Button("🇮🇳 ಕನ್ನಡ (Kannada)", variant="secondary", elem_classes=["lang-btn"])
                        
                    gr.HTML("<hr style='border: 0; height: 1px; background: rgba(255,255,255,0.1); margin: 15px 0;'>")
                    
                    # Markdown component to render HTML dashboard status
                    patient_status_display = gr.HTML(
                        "<div style='text-align:center; padding: 20px;'>Select a language to initialize your consultation.</div>"
                    )
                    
                    # New Session trigger
                    btn_new_session = gr.Button("🔄 Reset / New Session", variant="stop")
                    
                # Right Column: Chatbot
                with gr.Column(scale=8, elem_classes=["glass-card"]):
                    chatbot_disp = gr.Chatbot(
                        label="AI Healthcare Triage Chat",
                        elem_id="healthcare-chatbot",
                        height=450,
                        bubble_full_width=False,
                    )
                    
                    with gr.Row():
                        txt_input = gr.Textbox(
                            show_label=False,
                            placeholder="Type your message here and press Enter...",
                            container=False,
                            scale=10
                        )
                        btn_send = gr.Button("Send", variant="primary", scale=2, elem_classes=["btn-primary"])
                        
                    # Referral booking popup box
                    with gr.Group(visible=False, elem_id="referral-box", elem_classes=["dark-group"]) as referral_box:
                        referral_summary = gr.Markdown("")
                        with gr.Row():
                            btn_accept_ref = gr.Button("Yes, Connect to Doctor Remotely", variant="primary", elem_classes=["btn-primary"])
                        referral_result_msg = gr.Markdown("")
                        
        # TAB 2: Doctor Referral Portal
        with gr.Tab("Doctor Portal", id="doctor-tab"):
            with gr.Row():
                # Left Column: Referral queue
                with gr.Column(scale=4, elem_classes=["glass-card"]):
                    gr.Markdown("### 🩺 Pending Referrals Queue")
                    specialty_filter = gr.Dropdown(
                        choices=["All", "General Physician", "Cardiologist", "Pediatrician", "Pulmonologist", "Gynecologist", "Dermatologist", "Neurologist", "Orthopedician"],
                        value="All",
                        label="Filter by Specialty"
                    )
                    
                    btn_refresh_refs = gr.Button("🔄 Refresh List", variant="secondary")
                    
                    referral_dropdown = gr.Dropdown(
                        choices=[],
                        label="Select Referral to Review",
                        interactive=True
                    )
                    
                # Right Column: Review Details & Consultation
                with gr.Column(scale=8, elem_classes=["glass-card"]):
                    with gr.Group(visible=False, elem_classes=["dark-group"]) as review_panel:
                        with gr.Row():
                            with gr.Column(scale=6):
                                patient_info_display = gr.Markdown("### 📋 Patient Details")
                            with gr.Column(scale=6):
                                triage_summary_display = gr.Markdown("### 🩺 AI Diagnostic Assessment")
                                
                        gr.HTML("<hr style='border: 0; height: 1px; background: rgba(255,255,255,0.1); margin: 15px 0;'>")
                        
                        chat_transcript_display = gr.Markdown("### 💬 Triage Conversation History")
                        
                        gr.HTML("<hr style='border: 0; height: 1px; background: rgba(255,255,255,0.1); margin: 15px 0;'>")
                        
                        # Doctor consultation inputs
                        gr.Markdown("### 📝 Remote Doctor Actions")
                        with gr.Row():
                            doctor_name_input = gr.Textbox(label="Doctor Name", placeholder="Dr. Smith")
                            referral_status = gr.Dropdown(choices=["PENDING", "ACCEPTED", "COMPLETED"], label="Referral Status", value="ACCEPTED")
                            
                        doctor_prescription = gr.Textbox(
                            label="Medical Advice / Prescription Notes",
                            placeholder="Enter diagnosis notes, prescriptions, or advice for the patient here...",
                            lines=4
                        )
                        
                        btn_save_consult = gr.Button("💾 Submit Diagnostic Evaluation & Advice", variant="primary", elem_classes=["btn-primary"])
                        consult_save_status = gr.Markdown("")
                    
                    # Empty state display
                    no_ref_display = gr.Markdown("Select a referral from the list on the left to begin review.")
                    
        # TAB 3: Admin Configuration Panel
        with gr.Tab("Configuration Settings", id="settings-tab"):
            with gr.Column(elem_classes=["glass-card"]):
                gr.Markdown("### ⚙️ System Config / API Keys Setup")
                provider_select = gr.Dropdown(
                    choices=["deepseek", "gemini", "openai", "ollama"],
                    value=Config.DEFAULT_PROVIDER,
                    label="Frontier LLM Provider"
                )
                
                with gr.Row():
                    deepseek_key_input = gr.Textbox(
                        label="DEEPSEEK API KEY",
                        value=Config.DEEPSEEK_API_KEY,
                        type="password",
                        placeholder="sk-..."
                    )
                    gemini_key_input = gr.Textbox(
                        label="GEMINI API KEY",
                        value=Config.GEMINI_API_KEY,
                        type="password",
                        placeholder="AIzaSy..."
                    )
                    openai_key_input = gr.Textbox(
                        label="OPENAI API KEY",
                        value=Config.OPENAI_API_KEY,
                        type="password",
                        placeholder="sk-proj-..."
                    )
                    
                with gr.Row():
                    deepseek_model_input = gr.Textbox(label="DeepSeek Model Name", value=Config.DEEPSEEK_MODEL)
                    gemini_model_input = gr.Textbox(label="Gemini Model Name", value=Config.GEMINI_MODEL)
                    openai_model_input = gr.Textbox(label="OpenAI Model Name", value=Config.OPENAI_MODEL)
                    ollama_model_input = gr.Textbox(label="Ollama Model Name", value=Config.OLLAMA_MODEL)
                    
                ollama_host_input = gr.Textbox(
                    label="Ollama Host Endpoint",
                    value=Config.OLLAMA_HOST,
                    placeholder="http://localhost:11434"
                )
                
                with gr.Row():
                    btn_save_settings = gr.Button("💾 Save Configuration", variant="primary", elem_classes=["btn-primary"])
                    btn_test_conn = gr.Button("🔌 Test LLM Connection", variant="secondary")
                    
                settings_status_msg = gr.Markdown("")
                connection_test_msg = gr.Markdown("")
                
    # --- Gradio Event Triggers ---
    
    # 1. Language triggers
    btn_en.click(
        fn=lambda: start_new_session("en"),
        inputs=[],
        outputs=[session_id_state, chatbot_disp, patient_status_display, referral_box, referral_result_msg]
    )
    btn_hi.click(
        fn=lambda: start_new_session("hi"),
        inputs=[],
        outputs=[session_id_state, chatbot_disp, patient_status_display, referral_box, referral_result_msg]
    )
    btn_kn.click(
        fn=lambda: start_new_session("kn"),
        inputs=[],
        outputs=[session_id_state, chatbot_disp, patient_status_display, referral_box, referral_result_msg]
    )
    
    btn_new_session.click(
        fn=lambda: ("", None, "<div style='text-align:center; padding: 20px;'>Select a language to initialize your consultation.</div>", gr.update(visible=False), ""),
        inputs=[],
        outputs=[session_id_state, chatbot_disp, patient_status_display, referral_box, referral_result_msg]
    )
    
    # 2. Chat triggers
    txt_input.submit(
        fn=process_patient_chat,
        inputs=[txt_input, chatbot_disp, session_id_state],
        outputs=[txt_input, chatbot_disp, patient_status_display, referral_box, referral_summary]
    )
    btn_send.click(
        fn=process_patient_chat,
        inputs=[txt_input, chatbot_disp, session_id_state],
        outputs=[txt_input, chatbot_disp, patient_status_display, referral_box, referral_summary]
    )
    
    # 3. Patient Doctor Referral Booking
    btn_accept_ref.click(
        fn=accept_remote_referral,
        inputs=[session_id_state],
        outputs=[referral_box, referral_result_msg, patient_status_display, chatbot_disp]
    )
    
    # 4. Doctor Portal Triggers
    btn_refresh_refs.click(
        fn=refresh_referral_list,
        inputs=[specialty_filter],
        outputs=[referral_dropdown]
    )
    
    specialty_filter.change(
        fn=refresh_referral_list,
        inputs=[specialty_filter],
        outputs=[referral_dropdown]
    )
    
    def on_referral_select(ref_id):
        patient_info, summary, panel_visible, chat, status = select_referral_to_review(ref_id)
        # Hide empty state message, show review panel
        return patient_info, summary, panel_visible, chat, status, gr.update(visible=False if ref_id else True)
        
    referral_dropdown.change(
        fn=on_referral_select,
        inputs=[referral_dropdown],
        outputs=[patient_info_display, triage_summary_display, review_panel, chat_transcript_display, referral_status, no_ref_display]
    )
    
    btn_save_consult.click(
        fn=save_doctor_consultation,
        inputs=[referral_dropdown, doctor_name_input, referral_status, doctor_prescription],
        outputs=[consult_save_status, review_panel]
    ).then(
        # Refresh referral dropdown list after saving
        fn=refresh_referral_list,
        inputs=[specialty_filter],
        outputs=[referral_dropdown]
    )
    
    # 5. Settings triggers
    btn_save_settings.click(
        fn=apply_new_settings,
        inputs=[provider_select, deepseek_key_input, gemini_key_input, openai_key_input, deepseek_model_input, gemini_model_input, openai_model_input, ollama_model_input, ollama_host_input],
        outputs=[settings_status_msg]
    )
    
    btn_test_conn.click(
        fn=test_llm_connection,
        inputs=[provider_select, deepseek_key_input, gemini_key_input, openai_key_input, deepseek_model_input, gemini_model_input, openai_model_input, ollama_model_input, ollama_host_input],
        outputs=[connection_test_msg]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
