import os
import shutil
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self, persist_dir: str | None = None):
        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vector_store = None
        self._init_db()

    def _init_db(self):
        if os.getenv("CHROMA_DISABLED") == "1":
            self.vector_store = None
            return
        try:
            from langchain_chroma import Chroma
            self.vector_store = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
                collection_name="atome_help_center"
            )
        except Exception as e:
            logger.error(f"Chroma init failed: {e}")
            self.vector_store = None

    def add_documents(self, documents: List[Document]):
        """Add documents to the vector store."""
        if not documents or not self.vector_store:
            return
        logger.info(f"Adding {len(documents)} documents to vector store...")
        self.vector_store.add_documents(documents)
        logger.info("Documents added.")

    def clear(self):
        """Clear the vector store."""
        logger.info("Clearing vector store...")
        try:
            # Attempt to delete all documents instead of nuking the directory
            # This avoids file locking issues with SQLite
            if self.vector_store:
                ids = self.vector_store.get()['ids']
                if ids:
                    self.vector_store.delete(ids=ids)
                    logger.info(f"Deleted {len(ids)} documents from vector store.")
            else:
                # If vector_store is not initialized, try to remove directory
                if os.path.exists(self.persist_dir):
                    shutil.rmtree(self.persist_dir)
                self._init_db()
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            # Fallback: try to re-init anyway
            self._init_db()

    def as_retriever(self):
        if not self.vector_store:
            return None
        return self.vector_store.as_retriever()
