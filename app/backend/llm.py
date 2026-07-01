import os
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama

def get_llm(provider: str, api_key: str = None, model_name: str = None, temperature: float = 0.2):
    """
    Factory function to initialize and return a LangChain Chat Model.
    Supports DeepSeek, OpenAI, Gemini, and local Ollama.
    """
    provider = provider.lower()
    
    if provider == "deepseek":
        # Check API Key
        key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not key or key == "your_deepseek_api_key_here":
            raise ValueError("DeepSeek API Key is not configured. Please set it in the Settings panel or .env file.")
        
        model = model_name or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        return ChatOpenAI(
            model=model,
            api_key=key,
            base_url="https://api.deepseek.com",
            temperature=temperature
        )
        
    elif provider == "gemini":
        # Check API Key
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key or key == "your_gemini_api_key_here":
            raise ValueError("Gemini API Key is not configured. Please set it in the Settings panel or .env file.")
        
        model = model_name or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=key,
            temperature=temperature,
            max_output_tokens=1024
        )
        
    elif provider == "openai":
        # Check API Key
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key or key == "your_openai_api_key_here":
            raise ValueError("OpenAI API Key is not configured. Please set it in the Settings panel or .env file.")
            
        model = model_name or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(
            model=model,
            api_key=key,
            temperature=temperature
        )
        
    elif provider == "ollama":
        base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        model = model_name or os.environ.get("OLLAMA_MODEL", "llama3")
        return ChatOllama(
            base_url=base_url,
            model=model,
            temperature=temperature
        )
        
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
