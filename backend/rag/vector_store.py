import chromadb
from chromadb.types import Collection
from chromadb.utils import embedding_functions

from backend import logger, settings


class VectorStore:
    DB_PATH = settings.DB_PATH
    COLLECTION_NAME = settings.COLLECTION_NAME

    def __init__(self):
        self._collection = None
        self.initialize_chroma_db()

    @property
    def collection(self) -> Collection:
        """Returns the ChromaDB collection."""
        return self._collection

    @staticmethod
    def get_embedding_function():
        """Returns the local Sentence Transformer embedding function."""
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

    def initialize_chroma_db(self):
        """Initializes the ChromaDB client and collection synchronously."""
        if self.collection is not None:
            return self.collection

        client = chromadb.PersistentClient(path=self.DB_PATH)

        logger.info("Fetch embedding model.")
        embedding_function = self.get_embedding_function()

        # Get or create the collection
        self._collection = client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=embedding_function
        )

        logger.info(f"ChromaDB collection '{self.COLLECTION_NAME}' initialized.")
        return self.collection

    def create_documents(self, documents, metadata, ids):
        """Deletes existing collection and creates new documents."""
        self.delete_collection()
        # Reinitialize after deletion
        self.initialize_chroma_db()
        self.collection.add(
            documents=documents,
            metadatas=metadata,
            ids=ids
        )

    def fetch_chunk(self, query: str, n_results: int = 2) -> dict:
        """Fetches relevant chunks from the vector store based on query."""
        results = {}
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

    def delete_collection(self):
        """Deletes the ChromaDB collection."""
        try:
            if self.collection is not None:
                self.collection.delete_collection(self.COLLECTION_NAME)
                logger.info(f"ChromaDB collection '{self.COLLECTION_NAME}' deleted.")
        except Exception as e:
            logger.exception(f"Error deleting collection: {e}")
