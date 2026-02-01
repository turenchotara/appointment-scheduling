import json
from typing import Any

import aiofiles

from backend import logger, settings
from backend.protocols import VectorStoreProtocol
from .vector_store import DocumentMetadata, QueryResult, VectorStore

# Type aliases
FAQData = dict[str, Any]
FAQItem = dict[str, str]


class FAQ:
    """FAQ knowledge base for indexing and querying frequently asked questions.
    
    This class supports dependency injection for the vector store, allowing
    for different vector store implementations to be used.
    """
    
    def __init__(self, vector_client: VectorStoreProtocol | None = None) -> None:
        """Initialize the FAQ handler with a vector store client.
        
        Args:
            vector_client: Optional vector store implementation. If not provided,
                          defaults to the ChromaDB VectorStore.
        """
        self.vector_client: VectorStoreProtocol = vector_client or VectorStore()

    @staticmethod
    async def fetch_faqs() -> FAQData:
        """Loads FAQ data from the configured file path.
        
        Returns:
            Dictionary containing FAQ data, or empty dict if file not found.
        """
        try:
            async with aiofiles.open(settings.FAQ_DATA_PATH, 'r') as f:
                data: FAQData = json.loads(await f.read())
            return data
        except FileNotFoundError:
            logger.exception(f"Error: FAQ data file not found at {settings.FAQ_DATA_PATH}")
            return {}

    async def index_faqs(self) -> None:
        """Loads FAQ data, prepares it for indexing, and adds it to the vector store."""
        # Data Preparation
        documents: list[str] = []
        metadata: list[DocumentMetadata] = []
        ids: list[str] = []

        data: FAQData = await self.fetch_faqs()
        faqs: list[FAQItem] = data.get('faqs', [])
        supplementary: list[FAQItem] = data.get('faqs_supplementary', [])
        
        for i, item in enumerate(faqs + supplementary):
            document: str = f"Question: {item['question']}\nAnswer: {item['answer']}"
            documents.append(document)
            metadata.append({"category": item['category']})
            ids.append(f"faq-{i + 1}")

        if documents:
            logger.info(f"Indexing {len(documents)} FAQ documents...")
            self.vector_client.create_documents(documents, metadata, ids)
            logger.info("Indexing complete!")
        else:
            logger.warning("No FAQ data found to index.")

    def answer_faq_query(self, query: str) -> str:
        """Performs a RAG lookup on the FAQ knowledge base.
        
        Args:
            query: The user's question to search for.
            
        Returns:
            The relevant FAQ context or a fallback message.
        """
        logger.info(f"Query: {query} Search relevant documents...")

        try:
            results: QueryResult = self.vector_client.fetch_chunk(query)
        except Exception as e:
            logger.exception(f"Error while fetching documents: {e}")
            results = {}
            
        if not results or not results.get('documents') or not results['documents'][0]:
            return (
                "I'm sorry, I couldn't find an answer to that specific question "
                "in my knowledge base. Can I help you schedule an appointment instead?"
            )

        documents: list[str] = results['documents'][0]
        context: str = "\n---\n".join(documents)

        return context
