import os
import uuid
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set test database URL
os.environ["DATABASE_URL"] = "sqlite:///data/test_healthcare.db"

def run_tests():
    print("--- Starting Backend Validation Tests ---")
    
    # Test 1: Verify Database Initialization
    print("Test 1: Initializing database...", end=" ")
    try:
        from app.database import (
            init_db,
            get_or_create_session,
            add_chat_message,
            get_chat_history,
            create_triage_record,
            create_referral,
            get_pending_referrals,
            update_referral_status
        )
        init_db()
        print("PASS")
    except Exception as e:
        print(f"FAIL\nReason: {e}")
        return False
        
    # Test 2: Test Database CRUD
    print("Test 2: Testing Database CRUD operations...", end=" ")
    try:
        session_id = f"test-{uuid.uuid4()}"
        
        # Create session
        session = get_or_create_session(session_id, "kn")
        assert session.language == "kn", "Session language mismatch"
        
        # Add messages
        msg1 = add_chat_message(session_id, "patient", "ನನಗೆ ಜ್ವರ ಇದೆ")
        msg2 = add_chat_message(session_id, "bot", "ನಿಮ್ಮ ವಯಸ್ಸು ಎಷ್ಟು?")
        
        history = get_chat_history(session_id)
        assert len(history) == 2, "Chat history length mismatch"
        assert history[0] == ("patient", "ನನಗೆ ಜ್ವರ ಇದೆ"), "Chat history content mismatch"
        
        # Create triage record
        triage_rec = create_triage_record(
            session_id=session_id,
            age=25,
            gender="Male",
            symptoms="Mild fever",
            duration="2 days",
            severity="Low",
            triage_summary="Take rest, hydrate.",
            suggested_specialty="General Physician"
        )
        assert triage_rec.age == 25
        assert triage_rec.severity == "Low"
        
        # Create referral
        ref = create_referral(triage_rec.id, "General Physician")
        assert ref.status == "PENDING"
        
        # Fetch pending
        pending = get_pending_referrals("General Physician")
        assert len(pending) >= 1
        
        # Update referral
        update_referral_status(ref.id, "ACCEPTED", doctor_name="Dr. Patil", doctor_notes="Rest recommended")
        ref_updated = get_pending_referrals("General Physician")
        # should not be in pending anymore
        assert ref.id not in [r.id for r in ref_updated]
        
        print("PASS")
    except Exception as e:
        print(f"FAIL\nReason: {e}")
        return False
        
    # Test 3: Test LangGraph compilation
    print("Test 3: Testing LangGraph compilation and router structure...", end=" ")
    try:
        from app.backend.agent import agent_graph, route_next, parse_extracted_json
        
        # Verify graph is compiled
        assert agent_graph is not None, "Agent graph should not be None"
        
        # Verify router logic
        route1 = route_next({"triage_stage": "GATHERING"})
        assert route1 == "triage"
        
        route2 = route_next({"triage_stage": "DIAGNOSED"})
        assert route2 == "__end__"
        
        # Verify parse JSON helper
        parsed = parse_extracted_json('```json\n{"age": 30, "gender": "Female"}\n```')
        assert parsed.get("age") == 30
        assert parsed.get("gender") == "Female"
        
        print("PASS")
    except Exception as e:
        print(f"FAIL\nReason: {e}")
        return False
        
    # Clean up test DB
    try:
        if os.path.exists("data/test_healthcare.db"):
            os.remove("data/test_healthcare.db")
    except Exception:
        pass
        
    print("--- All Backend Tests Passed Successfully! ---")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
