import json

import aiofiles

from backend import logger, settings
from .vector_store import VectorStore


class FAQ:
    def __init__(self):
        self.vector_client = VectorStore()

    @staticmethod
    async def fetch_faqs():
        """Loads FAQ data, prepares it for indexing, and adds it to ChromaDB."""
        try:
            async with aiofiles.open(settings.FAQ_DATA_PATH, 'r') as f:
                data = json.loads(await f.read())
            return data
        except FileNotFoundError:
            logger.exception(f"Error: FAQ data file not found at {settings.FAQ_DATA_PATH}")
            return {}

    async def index_faqs(self):
        """Loads FAQ data, prepares it for indexing, and adds it to ChromaDB."""
        # --- Data Preparation ---
        documents = []
        metadata = []
        ids = []

        data = await self.fetch_faqs()
        for i, item in enumerate(data.get('faqs', []) + data.get('faqs_supplementary', [])):
            document = f"Question: {item['question']}\nAnswer: {item['answer']}"

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
        """Performs a RAG lookup on the FAQ knowledge base."""
        logger.info(f"Query: {query} Search relevant documents...")

        results = self.vector_client.fetch_chunk(query)

        if not results or not results.get('documents') or not results['documents'][0]:
            return "I'm sorry, I couldn't find an answer to that specific question in my knowledge base. Can I help you schedule an appointment instead?"

        context = "\n---\n".join(results['documents'][0])

        return context
