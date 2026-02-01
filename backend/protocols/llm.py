from typing import Any, Protocol, Sequence, runtime_checkable

from langchain_core.messages import BaseMessage


@runtime_checkable
class LLMProtocol(Protocol):
    """Protocol defining the interface for LLM implementations.
    
    This protocol allows for different LLM providers (OpenAI, Google, Anthropic, etc.)
    to be used interchangeably through dependency injection.
    """
    
    def invoke(self, messages: Sequence[BaseMessage]) -> BaseMessage:
        """Invoke the LLM with a sequence of messages.
        
        Args:
            messages: Sequence of chat messages to send to the LLM.
            
        Returns:
            The LLM's response message.
        """
        ...
    
    async def ainvoke(self, messages: Sequence[BaseMessage]) -> BaseMessage:
        """Asynchronously invoke the LLM with a sequence of messages.
        
        Args:
            messages: Sequence of chat messages to send to the LLM.
            
        Returns:
            The LLM's response message.
        """
        ...
    
    def bind_tools(self, tools: Sequence[Any]) -> "LLMProtocol":
        """Bind tools to the LLM for function calling.
        
        Args:
            tools: Sequence of tools to bind to the LLM.
            
        Returns:
            A new LLM instance with tools bound.
        """
        ...
