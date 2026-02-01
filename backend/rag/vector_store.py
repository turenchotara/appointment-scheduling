from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from backend import logger, settings

# Type aliases for ChromaDB query results
QueryResult = dict[str, Any]
DocumentMetadata = dict[str, str]


class VectorStore:
    """ChromaDB-based vector store for document embeddings and retrieval."""
    
    DB_PATH: str = settings.DB_PATH
    COLLECTION_NAME: str = settings.COLLECTION_NAME

    def __init__(self) -> None:
        """Initialize the vector store and connect to ChromaDB."""
        self._collection: Collection | None = None
        self.initialize_chroma_db()

    @property
    def collection(self) -> Collection | None:
        """Returns the ChromaDB collection.
        
        Returns:
            The ChromaDB collection instance or None if not initialized.
        """
        return self._collection

    @staticmethod
    def get_embedding_function() -> SentenceTransformerEmbeddingFunction:
        """Returns the local Sentence Transformer embedding function.
        
        Returns:
            SentenceTransformerEmbeddingFunction configured with all-MiniLM-L6-v2.
        """
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

    def initialize_chroma_db(self) -> Collection | None:
        """Initializes the ChromaDB client and collection synchronously.
        
        Returns:
            The initialized ChromaDB collection.
        """
        if self.collection is not None:
            return self.collection

        client: chromadb.PersistentClient = chromadb.PersistentClient(path=self.DB_PATH)

        logger.info("Fetch embedding model.")
        embedding_function: SentenceTransformerEmbeddingFunction = self.get_embedding_function()

        # Get or create the collection
        self._collection = client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=embedding_function
        )

        logger.info(f"ChromaDB collection '{self.COLLECTION_NAME}' initialized.")
        return self.collection

    def create_documents(
        self, 
        documents: list[str], 
        metadata: list[DocumentMetadata], 
        ids: list[str]
    ) -> None:
        """Deletes existing collection and creates new documents.
        
        Args:
            documents: List of document texts to index.
            metadata: List of metadata dictionaries for each document.
            ids: List of unique identifiers for each document.
        """
        self.delete_collection()
        # Reinitialize after deletion
        self.initialize_chroma_db()
        if self.collection is not None:
            self.collection.add(
                documents=documents,
                metadatas=metadata,
                ids=ids
            )

    def fetch_chunk(self, query: str, n_results: int = 2) -> QueryResult:
        """Fetches relevant chunks from the vector store based on query.
        
        Args:
            query: The search query string.
            n_results: Maximum number of results to return.
            
        Returns:
            Dictionary containing query results with 'documents' key.
        """
        results: QueryResult = {}
        try:
            if self.collection is None:
                logger.error("Collection not initialized. Cannot fetch chunks.")
                return results

            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
        except Exception as e:
            logger.exception(f"Error fetching chunks: {e}")
        return results

    def delete_collection(self) -> None:
        """Deletes all documents from the ChromaDB collection."""
        try:
            if self.collection is not None:
                # Get all existing IDs to delete
                existing = self.collection.get()
                existing_ids: list[str] = existing.get("ids", [])
                
                if existing_ids:
                    self.collection.delete(ids=existing_ids)
                    logger.info(f"Deleted {len(existing_ids)} documents from collection '{self.COLLECTION_NAME}'.")
                else:
                    logger.info(f"Collection '{self.COLLECTION_NAME}' is already empty.")
        except Exception as e:
            logger.exception(f"Error deleting collection: {e}")
