from typing import Any, Protocol, runtime_checkable


# Type aliases
QueryResult = dict[str, Any]
DocumentMetadata = dict[str, str]


@runtime_checkable
class VectorStoreProtocol(Protocol):
    """Protocol defining the interface for vector store implementations.
    
    This protocol allows for different vector store backends (ChromaDB, Pinecone, etc.)
    to be used interchangeably through dependency injection.
    """
    
    def initialize_chroma_db(self) -> Any:
        """Initialize the vector store connection and collection.
        
        Returns:
            The initialized collection or client.
        """
        ...
    
    def create_documents(
        self, 
        documents: list[str], 
        metadata: list[DocumentMetadata], 
        ids: list[str]
    ) -> None:
        """Create and index new documents in the vector store.
        
        Args:
            documents: List of document texts to index.
            metadata: List of metadata dictionaries for each document.
            ids: List of unique identifiers for each document.
        """
        ...
    
    def fetch_chunk(self, query: str, n_results: int = 2) -> QueryResult:
        """Fetch relevant document chunks based on a query.
        
        Args:
            query: The search query string.
            n_results: Maximum number of results to return.
            
        Returns:
            Dictionary containing query results with 'documents' key.
        """
        ...
    
    def delete_collection(self) -> None:
        """Delete the current collection from the vector store."""
        ...
