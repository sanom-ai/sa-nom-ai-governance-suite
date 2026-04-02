from __future__ import annotations

from sa_nom_governance.documents.document_models import GovernedDocumentRecord, utc_now
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.persistence import build_state_store


class GovernedDocumentStore:
    def __init__(self, config: AppConfig, store_path) -> None:
        self.store = build_state_store(config, store_path, logical_name="document_center")
        self.store_path = self.store.path
        self.documents: dict[str, GovernedDocumentRecord] = {}
        self.sequences: dict[str, int] = {}
        self._load()

    def list_documents(self) -> list[GovernedDocumentRecord]:
        return sorted(self.documents.values(), key=lambda item: item.updated_at, reverse=True)

    def get_document(self, document_id: str) -> GovernedDocumentRecord:
        if document_id not in self.documents:
            raise KeyError(f"Governed document not found: {document_id}")
        return self.documents[document_id]

    def save_document(self, document: GovernedDocumentRecord) -> GovernedDocumentRecord:
        self.documents[document.document_id] = document
        self._save()
        return document

    def next_sequence(self, document_class: str) -> int:
        current = int(self.sequences.get(document_class, 0) or 0) + 1
        self.sequences[document_class] = current
        self._save()
        return current

    def _load(self) -> None:
        data = self.store.read(default={})
        sequences = data.get("sequences", {}) if isinstance(data.get("sequences", {}), dict) else {}
        self.sequences = {str(key): int(value or 0) for key, value in sequences.items()}
        raw_documents = data.get("documents", {}) if isinstance(data.get("documents", {}), dict) else {}
        self.documents = {
            document_id: GovernedDocumentRecord.from_dict(item)
            for document_id, item in raw_documents.items()
            if isinstance(item, dict)
        }

    def _save(self) -> None:
        payload = {
            "generated_at": utc_now(),
            "sequences": {key: int(value or 0) for key, value in sorted(self.sequences.items())},
            "documents": {document_id: document.to_dict() for document_id, document in sorted(self.documents.items())},
        }
        self.store.write(payload)
