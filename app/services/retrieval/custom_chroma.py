"""Custom ChromaDB client with sentence-transformers embeddings."""
import os
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from spoon_ai.retrieval.base import BaseRetrievalClient, Document
from app.core.config import settings


class CustomChromaClient(BaseRetrievalClient):
    """Custom ChromaDB client with sentence-transformers embeddings.
    
    This client uses sentence-transformers (free) instead of OpenAI embeddings.
    Model: paraphrase-multilingual-MiniLM-L12-v2 (supports Vietnamese)
    """
    
    EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    COLLECTION_NAME = "chatbot_documents"
    
    def __init__(self, config_dir: Optional[str] = None, collection_name: Optional[str] = None):
        """Initialize custom ChromaDB client.
        
        Args:
            config_dir: Directory to store ChromaDB data. Defaults to settings.CHROMADB_PATH.
            collection_name: Name of the collection. Defaults to COLLECTION_NAME.
        """
        try:
            import chromadb
        except ImportError as e:
            raise ImportError("ChromaDB is not installed. Please install it with 'pip install chromadb'.") from e
        
        # Use config_dir from settings if not provided
        if config_dir is None:
            config_dir = settings.CHROMADB_PATH
        
        # Create directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        # Initialize ChromaDB client
        self._chromadb = chromadb
        self.client = chromadb.PersistentClient(
            path=config_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection_name = collection_name or self.COLLECTION_NAME
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        # Initialize sentence-transformer model
        # This will download the model on first use (may take time)
        # Model will be cached for subsequent uses
        try:
            self.embedding_model = SentenceTransformer(self.EMBEDDING_MODEL)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load sentence-transformer model '{self.EMBEDDING_MODEL}'. "
                f"This may be due to network issues or missing dependencies. "
                f"Error: {str(e)}"
            ) from e
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text.
        
        Args:
            text: Text to embed.
        
        Returns:
            Embedding vector as a list of floats.
        """
        embedding = self.embedding_model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    
    def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed.
        
        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []
        
        embeddings = self.embedding_model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
    
    def add_documents(self, documents: List[Document], batch_size: int = 32):
        """Add documents to the collection.
        
        Args:
            documents: List of Document objects to add.
            batch_size: Batch size for processing. Defaults to 32.
        """
        if not documents:
            return
        
        # Process in batches
        for start in range(0, len(documents), batch_size):
            chunk = documents[start:start + batch_size]
            texts = [doc.page_content for doc in chunk]
            metadatas = [dict(doc.metadata or {}) for doc in chunk]
            
            # Generate IDs from metadata or UUID
            ids = []
            for md in metadatas:
                if "id" in md and isinstance(md["id"], str):
                    ids.append(md["id"])
                else:
                    ids.append(str(uuid.uuid4()))
            
            # Get embeddings
            embeddings = self._get_embeddings_batch(texts)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings,
            )
    
    def query(
        self,
        query: str,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Query documents from the collection.
        
        Args:
            query: Query string.
            k: Number of results to return. Defaults to 5.
        
        Returns:
            List of Document objects.
        """
        # Get query embedding
        query_embedding = self._get_embedding(query)
        
        # Query collection
        # ChromaDB 1.3.4+: "ids" is always returned automatically and should NOT be in include parameter
        # Valid include values: "documents", "embeddings", "metadatas", "distances", "uris", "data"
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
            where=where or None,
        )
        
        # Parse results
        # Results structure:
        # {
        #   "ids": [[id1, id2, ...]],  # Always returned, even if not in include
        #   "documents": [[doc1, doc2, ...]],
        #   "metadatas": [[meta1, meta2, ...]],
        #   "distances": [[dist1, dist2, ...]]
        # }
        # Extract first (and only) query result list
        ids = results.get("ids", [])
        if ids and isinstance(ids, list) and len(ids) > 0:
            ids = ids[0] if isinstance(ids[0], list) else ids
        else:
            ids = []
        
        docs = results.get("documents", [])
        if docs and isinstance(docs, list) and len(docs) > 0:
            docs = docs[0] if isinstance(docs[0], list) else docs
        else:
            docs = []
        
        metas = results.get("metadatas", [])
        if metas and isinstance(metas, list) and len(metas) > 0:
            metas = metas[0] if isinstance(metas[0], list) else metas
        else:
            metas = []
        
        distances = results.get("distances", [])
        if distances and isinstance(distances, list) and len(distances) > 0:
            distances = distances[0] if isinstance(distances[0], list) else distances
        else:
            distances = []
        
        # Build Document objects
        out = []
        for i in range(min(len(docs), len(metas), len(ids))):
            meta = dict(metas[i] or {})
            if "id" not in meta and i < len(ids):
                meta["id"] = ids[i]
            if i < len(distances):
                meta["distance"] = distances[i]
            
            out.append(Document(page_content=docs[i], metadata=meta))
        
        return out
    
    def delete_documents_by_metadata(self, document_id: int):
        """Delete all documents with a specific document_id in metadata.
        
        Args:
            document_id: Document ID to delete.
        """
        try:
            # Query for documents with this document_id
            # ChromaDB uses where clause with $eq operator
            # Note: In ChromaDB 1.3.4+, "ids" is always returned, so we don't need to include it
            results = self.collection.get(
                where={"document_id": {"$eq": document_id}},
                include=["metadatas"]  # Only include metadatas, ids are always returned
            )
            
            if results and results.get("ids") and len(results["ids"]) > 0:
                # Delete documents
                self.collection.delete(ids=results["ids"])
        except Exception as e:
            # If query fails (e.g., document_id might be stored as string or int)
            # Try to get all documents and filter
            # This is a fallback method
            try:
                # Get all documents (ids are always returned)
                all_results = self.collection.get(include=["metadatas"])
                if all_results and all_results.get("ids"):
                    ids_to_delete = []
                    metadatas = all_results.get("metadatas", [])
                    
                    for i, metadata in enumerate(metadatas):
                        if metadata:
                            # Try both int and string comparison
                            doc_id = metadata.get("document_id")
                            if doc_id == document_id or str(doc_id) == str(document_id):
                                ids_to_delete.append(all_results["ids"][i])
                    
                    if ids_to_delete:
                        self.collection.delete(ids=ids_to_delete)
            except Exception as ex:
                # If everything fails, log the error but don't raise
                # This allows the deletion to continue even if vector DB cleanup fails
                print(f"Warning: Failed to delete documents from vector database: {ex}")
                pass
    
    def delete_collection(self):
        """Delete the collection."""
        self.client.delete_collection(name=self.collection_name)
        # Recreate collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

