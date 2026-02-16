"""ChromaDB Vector Store for Triage AI.

Manages three collections:
- triage_protocols: Manchester Triage criteria
- routing_rules: Symptom-to-department mappings
- preliminary_orders: Standard initial orders by condition
"""

import os
import chromadb
from chromadb.config import Settings


class VectorStore:
    """ChromaDB vector store manager for triage data."""

    def __init__(self, persist_directory: str = "chroma_data"):
        """Initialize ChromaDB with persistent storage.

        Args:
            persist_directory: Directory for ChromaDB data persistence
        """
        self.persist_directory = persist_directory

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
            ),
        )

        # Get or create collections
        self.triage_protocols = self.client.get_or_create_collection(
            name="triage_protocols",
            metadata={"description": "Manchester Triage Protocol criteria"}
        )

        self.routing_rules = self.client.get_or_create_collection(
            name="routing_rules",
            metadata={"description": "Symptom to department routing rules"}
        )

        self.preliminary_orders = self.client.get_or_create_collection(
            name="preliminary_orders",
            metadata={"description": "Standard preliminary orders by condition"}
        )

    def search_triage_protocols(
        self,
        query: str,
        n_results: int = 5
    ) -> list[str]:
        """Search triage protocols collection.

        Args:
            query: Search query (symptoms, complaints)
            n_results: Number of results to return

        Returns:
            List of matching protocol documents
        """
        if self.triage_protocols.count() == 0:
            return ["No protocols loaded. Run seed_data.py first."]

        results = self.triage_protocols.query(
            query_texts=[query],
            n_results=n_results,
        )

        return results["documents"][0] if results["documents"] else []

    def search_routing_rules(
        self,
        query: str,
        n_results: int = 5
    ) -> list[str]:
        """Search routing rules collection.

        Args:
            query: Search query (symptoms, classification)
            n_results: Number of results to return

        Returns:
            List of matching routing rules
        """
        if self.routing_rules.count() == 0:
            return ["No routing rules loaded. Run seed_data.py first."]

        results = self.routing_rules.query(
            query_texts=[query],
            n_results=n_results,
        )

        return results["documents"][0] if results["documents"] else []

    def search_preliminary_orders(
        self,
        query: str,
        n_results: int = 5
    ) -> list[str]:
        """Search preliminary orders collection.

        Args:
            query: Search query (condition, symptoms)
            n_results: Number of results to return

        Returns:
            List of matching preliminary orders
        """
        if self.preliminary_orders.count() == 0:
            return ["No orders loaded. Run seed_data.py first."]

        results = self.preliminary_orders.query(
            query_texts=[query],
            n_results=n_results,
        )

        return results["documents"][0] if results["documents"] else []

    def add_triage_protocol(self, document: str, doc_id: str) -> None:
        """Add a triage protocol to the collection."""
        self.triage_protocols.add(
            documents=[document],
            ids=[doc_id],
        )

    def add_routing_rule(self, document: str, doc_id: str) -> None:
        """Add a routing rule to the collection."""
        self.routing_rules.add(
            documents=[document],
            ids=[doc_id],
        )

    def add_preliminary_order(self, document: str, doc_id: str) -> None:
        """Add a preliminary order to the collection."""
        self.preliminary_orders.add(
            documents=[document],
            ids=[doc_id],
        )

    def get_stats(self) -> dict:
        """Get statistics about the collections."""
        return {
            "triage_protocols": self.triage_protocols.count(),
            "routing_rules": self.routing_rules.count(),
            "preliminary_orders": self.preliminary_orders.count(),
        }

    def clear_all(self) -> None:
        """Clear all collections (for re-seeding)."""
        self.client.delete_collection("triage_protocols")
        self.client.delete_collection("routing_rules")
        self.client.delete_collection("preliminary_orders")

        # Recreate empty collections
        self.triage_protocols = self.client.create_collection(
            name="triage_protocols",
            metadata={"description": "Manchester Triage Protocol criteria"}
        )
        self.routing_rules = self.client.create_collection(
            name="routing_rules",
            metadata={"description": "Symptom to department routing rules"}
        )
        self.preliminary_orders = self.client.create_collection(
            name="preliminary_orders",
            metadata={"description": "Standard preliminary orders by condition"}
        )
