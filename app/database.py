import os
from datetime import datetime
import uuid
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

Base = declarative_base()

class PatientSession(Base):
    __tablename__ = 'patient_sessions'
    
    session_id = Column(String(50), primary_key=True)
    language = Column(String(10), default='en')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", lazy="selectin")
    triage_records = relationship("TriageRecord", back_populates="session", cascade="all, delete-orphan", lazy="selectin")

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey('patient_sessions.session_id'), nullable=False)
    sender = Column(String(20), nullable=False)  # 'patient', 'bot', 'doctor'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("PatientSession", back_populates="messages", lazy="selectin")

class TriageRecord(Base):
    __tablename__ = 'triage_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey('patient_sessions.session_id'), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    symptoms = Column(Text, nullable=True)
    duration = Column(String(50), nullable=True)
    severity = Column(String(20), nullable=True)  # 'Low', 'Medium', 'High'
    triage_summary = Column(Text, nullable=True)
    suggested_specialty = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("PatientSession", back_populates="triage_records", lazy="selectin")
    referral = relationship("Referral", back_populates="triage_record", uselist=False, cascade="all, delete-orphan", lazy="selectin")

class Referral(Base):
    __tablename__ = 'referrals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    triage_record_id = Column(Integer, ForeignKey('triage_records.id'), nullable=False)
    specialty = Column(String(50), nullable=False)
    status = Column(String(20), default='PENDING')  # 'PENDING', 'ACCEPTED', 'COMPLETED'
    doctor_name = Column(String(100), nullable=True)
    doctor_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    triage_record = relationship("TriageRecord", back_populates="referral", lazy="selectin")

# Database setup
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///data/healthcare.db")

# Parse sqlite path and ensure dir exists
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

# CRUD Helper functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_or_create_session(session_id: str, language: str = 'en') -> PatientSession:
    db = SessionLocal()
    try:
        session = db.query(PatientSession).filter(PatientSession.session_id == session_id).first()
        if not session:
            session = PatientSession(session_id=session_id, language=language)
            db.add(session)
            db.commit()
            db.refresh(session)
        return session
    finally:
        db.close()

def update_session_language(session_id: str, language: str):
    db = SessionLocal()
    try:
        session = db.query(PatientSession).filter(PatientSession.session_id == session_id).first()
        if session:
            session.language = language
            db.commit()
    finally:
        db.close()

def add_chat_message(session_id: str, sender: str, message: str) -> ChatMessage:
    db = SessionLocal()
    try:
        # Ensure session exists
        get_or_create_session(session_id)
        
        chat_msg = ChatMessage(session_id=session_id, sender=sender, message=message)
        db.add(chat_msg)
        db.commit()
        db.refresh(chat_msg)
        return chat_msg
    finally:
        db.close()

def get_chat_history(session_id: str):
    db = SessionLocal()
    try:
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
        return [(m.sender, m.message) for m in messages]
    finally:
        db.close()

def create_triage_record(session_id: str, age: int, gender: str, symptoms: str, duration: str, severity: str, triage_summary: str, suggested_specialty: str) -> TriageRecord:
    db = SessionLocal()
    try:
        record = TriageRecord(
            session_id=session_id,
            age=age,
            gender=gender,
            symptoms=symptoms,
            duration=duration,
            severity=severity,
            triage_summary=triage_summary,
            suggested_specialty=suggested_specialty
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()

def create_referral(triage_record_id: int, specialty: str) -> Referral:
    db = SessionLocal()
    try:
        # Check if already exists
        existing = db.query(Referral).filter(Referral.triage_record_id == triage_record_id).first()
        if existing:
            return existing
            
        referral = Referral(triage_record_id=triage_record_id, specialty=specialty, status='PENDING')
        db.add(referral)
        db.commit()
        db.refresh(referral)
        return referral
    finally:
        db.close()

def get_pending_referrals(specialty: str = None):
    db = SessionLocal()
    try:
        query = db.query(Referral).filter(Referral.status == 'PENDING')
        if specialty and specialty != "All":
            query = query.filter(Referral.specialty == specialty)
        return query.order_by(Referral.created_at.desc()).all()
    finally:
        db.close()

def get_all_referrals():
    db = SessionLocal()
    try:
        return db.query(Referral).order_by(Referral.created_at.desc()).all()
    finally:
        db.close()

def get_referral_by_id(referral_id: int):
    db = SessionLocal()
    try:
        return db.query(Referral).filter(Referral.id == referral_id).first()
    finally:
        db.close()

def update_referral_status(referral_id: int, status: str, doctor_name: str = None, doctor_notes: str = None):
    db = SessionLocal()
    try:
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if referral:
            referral.status = status
            if doctor_name:
                referral.doctor_name = doctor_name
            if doctor_notes:
                referral.doctor_notes = doctor_notes
            referral.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(referral)
        return referral
    finally:
        db.close()
