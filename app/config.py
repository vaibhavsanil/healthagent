import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

class Config:
    DEFAULT_PROVIDER = os.environ.get("DEFAULT_PROVIDER", "deepseek")
    
    # API Keys
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    
    # Models
    DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
    
    # Connection endpoints
    OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///data/healthcare.db")

    @classmethod
    def update(cls, provider, deepseek_key, gemini_key, openai_key, deepseek_model, gemini_model, openai_model, ollama_model, ollama_host):
        """Update configurations dynamically from the UI."""
        cls.DEFAULT_PROVIDER = provider
        if deepseek_key:
            cls.DEEPSEEK_API_KEY = deepseek_key
            os.environ["DEEPSEEK_API_KEY"] = deepseek_key
        if gemini_key:
            cls.GEMINI_API_KEY = gemini_key
            os.environ["GEMINI_API_KEY"] = gemini_key
        if openai_key:
            cls.OPENAI_API_KEY = openai_key
            os.environ["OPENAI_API_KEY"] = openai_key
        if deepseek_model:
            cls.DEEPSEEK_MODEL = deepseek_model
            os.environ["DEEPSEEK_MODEL"] = deepseek_model
        if gemini_model:
            cls.GEMINI_MODEL = gemini_model
            os.environ["GEMINI_MODEL"] = gemini_model
        if openai_model:
            cls.OPENAI_MODEL = openai_model
            os.environ["OPENAI_MODEL"] = openai_model
        if ollama_model:
            cls.OLLAMA_MODEL = ollama_model
            os.environ["OLLAMA_MODEL"] = ollama_model
        if ollama_host:
            cls.OLLAMA_HOST = ollama_host
            os.environ["OLLAMA_HOST"] = ollama_host
