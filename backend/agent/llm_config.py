from typing import Any, Sequence

from langchain_core.language_models import BaseChatModel

from backend import settings


def create_gemini_llm() -> "BaseChatModel":
    """Create and configure a Google Gemini LLM instance.
    
    Returns:
        Configured ChatGoogleGenerativeAI instance.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.1,
        max_retries=2,
        google_api_key=getattr(settings, 'GOOGLE_API_KEY', "") or ""
    )


def create_azure_openai_llm() -> "BaseChatModel":
    """Create and configure an Azure OpenAI LLM instance.
    
    Returns:
        Configured AzureChatOpenAI instance.
    """
    from langchain_openai import AzureChatOpenAI
    
    return AzureChatOpenAI(
        azure_endpoint=getattr(settings, 'AZURE_ENDPOINT', "") or "",
        azure_deployment=getattr(settings, 'AZURE_DEPLOYMENT', "gpt-4.1") or "gpt-4.1",
        api_key=getattr(settings, 'AZURE_API_KEY', "") or "",
        api_version=getattr(settings, 'AZURE_API_VERSION', "") or ""
    )


def get_llm_with_tools(tools: Sequence[Any], provider: str = "azure") -> BaseChatModel:
    """Get an LLM instance with tools bound.
    
    Args:
        tools: Sequence of tools to bind to the LLM.
        provider: LLM provider to use ("azure" or "gemini").
        
    Returns:
        LLM instance with tools bound.
        
    Raises:
        ValueError: If an unknown provider is specified.
    """
    if provider == "azure":
        llm = create_azure_openai_llm()
    elif provider == "gemini":
        llm = create_gemini_llm()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
    
    return llm.bind_tools(tools)
