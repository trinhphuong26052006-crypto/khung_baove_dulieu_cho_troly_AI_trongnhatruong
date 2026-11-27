"""Document policy shared by retrieval, model context and displayed sources."""
import json
from dataclasses import dataclass
from pathlib import Path

CLASSIFICATION_ROLES = {
    "Public": frozenset(("SinhVien", "GiangVien", "QuanTri")),
    "Internal": frozenset(("GiangVien", "QuanTri")),
    "Restricted": frozenset(("QuanTri",)),
}
VALID_ROLES = CLASSIFICATION_ROLES["Public"]
CHAT_ACTIONS = frozenset(("read", "retrieve", "use_in_context"))


@dataclass(frozen=True)
class PermissionDecision:
    doc_id: str
    role: str
    allowed: bool
    reason: str


class PermissionChecker:
    DEFAULT_METADATA_PATH = Path(__file__).resolve().parents[2] / "data/metadata/documents_metadata.json"

    def __init__(self, metadata_path=None, valid_roles=None):
        self.metadata_path = Path(metadata_path or self.DEFAULT_METADATA_PATH)
        self.valid_roles = VALID_ROLES if valid_roles is None else VALID_ROLES.intersection(valid_roles)
        self.load_metadata()

    def load_metadata(self):
        self._metadata_by_id = {}
        try:
            documents = json.loads(self.metadata_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            return
        if not isinstance(documents, list):
            return

        duplicates = set()
        for document in documents:
            if not isinstance(document, dict):
                continue
            doc_id = document.get("doc_id")
            if not isinstance(doc_id, str) or not doc_id.strip():
                continue
            if doc_id in self._metadata_by_id:
                duplicates.add(doc_id)
            self._metadata_by_id[doc_id] = document
        for doc_id in duplicates:
            self._metadata_by_id.pop(doc_id)

    def check_document(self, user_role, document_metadata, action="retrieve"):
        doc = document_metadata if isinstance(document_metadata, dict) else {}
        doc_id = doc.get("doc_id")
        level = doc.get("classification")
        acl = doc.get("allowed_roles")

        def decision(allowed, reason):
            return PermissionDecision(str(doc_id or "UNKNOWN"), str(user_role), allowed, reason)

        if not isinstance(user_role, str) or user_role not in self.valid_roles:
            return decision(False, "invalid_role")
        if not isinstance(action, str) or action not in CHAT_ACTIONS:
            return decision(False, "action_not_enabled")
        if not isinstance(doc_id, str) or not doc_id.strip():
            return decision(False, "invalid_doc_id")
        if not isinstance(level, str) or level not in CLASSIFICATION_ROLES:
            return decision(False, "invalid_classification")
        expected = CLASSIFICATION_ROLES[level]
        if not isinstance(acl, list) or any(not isinstance(role, str) for role in acl):
            return decision(False, "invalid_allowed_roles")
        if len(acl) != len(expected) or set(acl) != expected:
            return decision(False, "acl_policy_mismatch")
        allowed = user_role in expected
        return decision(allowed, "policy_allow" if allowed else "policy_deny")

    def filter_authorized_metadata(self, user_role, documents):
        authorized, denied = [], []
        for document in documents:
            decision = self.check_document(user_role, document)
            if decision.allowed:
                authorized.append(document)
            else:
                denied.append(decision)
        return authorized, denied

    def filter_retrieved_results(self, user_role, results):
        authorized, denied = [], []
        for document in results:
            doc_id = document.get("doc_id")
            metadata = self._metadata_by_id.get(doc_id)
            decision = self.check_document(user_role, metadata, "use_in_context")
            if decision.allowed:
                authorized.append(document)
            else:
                denied.append(decision)
        return authorized, denied

    def get_all_documents(self):
        return [dict(doc, allowed_roles=list(doc["allowed_roles"]))
                if isinstance(doc.get("allowed_roles"), list) else dict(doc)
                for doc in self._metadata_by_id.values()]

    def get_allowed_documents(self, user_role, action="retrieve"):
        return [doc for doc in self.get_all_documents()
                if self.check_document(user_role, doc, action).allowed]

    def get_allowed_doc_ids(self, user_role, action="retrieve"):
        return {doc["doc_id"] for doc in self.get_allowed_documents(user_role, action)}

    def get_allowed_classifications(self, user_role):
        return [level for level, roles in CLASSIFICATION_ROLES.items()
                if isinstance(user_role, str) and user_role in self.valid_roles and user_role in roles]

    def is_access_allowed(self, doc_id, user_role, action="retrieve"):
        if not isinstance(doc_id, str):
            return False
        return self.check_document(user_role, self._metadata_by_id.get(doc_id), action).allowed

    def filter_documents_by_role(self, documents, user_role):
        authorized, _ = self.filter_retrieved_results(user_role, documents)
        return authorized
