from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.human_ask.human_ask_models import HumanAskSession, utc_now
from sa_nom_governance.utils.persistence import build_state_store


class HumanAskStore:
    def __init__(self, config: AppConfig, store_path) -> None:
        self.store = build_state_store(config, store_path, logical_name="human_ask")
        self.store_path = self.store.path
        self.sessions: dict[str, HumanAskSession] = {}
        self._load()

    def list_sessions(self, status: str | None = None) -> list[HumanAskSession]:
        items = sorted(self.sessions.values(), key=lambda item: item.updated_at, reverse=True)
        if status is None:
            return items
        return [item for item in items if item.status == status]

    def get_session(self, session_id: str) -> HumanAskSession:
        if session_id not in self.sessions:
            raise KeyError(f"Human Ask session not found: {session_id}")
        return self.sessions[session_id]

    def save_session(self, session: HumanAskSession) -> HumanAskSession:
        self.sessions[session.session_id] = session
        self._save()
        return session

    def _load(self) -> None:
        data = self.store.read(default={})
        self.sessions = {
            session_id: HumanAskSession.from_dict(item)
            for session_id, item in data.get("sessions", {}).items()
        }

    def _save(self) -> None:
        payload = {
            "generated_at": utc_now(),
            "sessions": {session_id: session.to_dict() for session_id, session in sorted(self.sessions.items())},
        }
        self.store.write(payload)
