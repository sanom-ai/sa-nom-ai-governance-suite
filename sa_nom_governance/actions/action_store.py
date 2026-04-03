from __future__ import annotations

from sa_nom_governance.actions.action_models import GovernedActionRecord, utc_now
from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.persistence import build_state_store


class GovernedActionStore:
    def __init__(self, config: AppConfig, store_path) -> None:
        self.store = build_state_store(config, store_path, logical_name="action_runtime")
        self.store_path = self.store.path
        self.actions: dict[str, GovernedActionRecord] = {}
        self._load()

    def list_actions(
        self,
        *,
        status: str | None = None,
        action_type: str | None = None,
        case_id: str | None = None,
        limit: int | None = None,
    ) -> list[GovernedActionRecord]:
        items = sorted(self.actions.values(), key=lambda item: item.updated_at, reverse=True)
        if status is not None:
            items = [item for item in items if item.status == status]
        if action_type is not None:
            items = [item for item in items if item.action_type == action_type]
        if case_id is not None:
            items = [item for item in items if item.case_id == case_id]
        if limit is not None:
            items = items[:limit]
        return items

    def get_action(self, action_id: str) -> GovernedActionRecord:
        if action_id not in self.actions:
            raise KeyError(f"AI action not found: {action_id}")
        return self.actions[action_id]

    def save_action(self, action: GovernedActionRecord) -> GovernedActionRecord:
        self.actions[action.action_id] = action
        self._save()
        return action

    def _load(self) -> None:
        data = self.store.read(default={})
        self.actions = {
            action_id: GovernedActionRecord.from_dict(item)
            for action_id, item in data.get("actions", {}).items()
            if isinstance(item, dict)
        }

    def _save(self) -> None:
        self.store.write(
            {
                "generated_at": utc_now(),
                "actions": {
                    action_id: action.to_dict()
                    for action_id, action in sorted(self.actions.items())
                },
            }
        )