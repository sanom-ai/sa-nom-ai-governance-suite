from sa_nom_governance.utils.config import AppConfig
from sa_nom_governance.utils.persistence import build_state_store
from sa_nom_governance.studio.role_private_studio_models import RolePrivateStudioRequest, utc_now


class RolePrivateStudioStore:
    def __init__(self, config: AppConfig, store_path) -> None:
        self.store = build_state_store(config, store_path, logical_name="role_private_studio")
        self.store_path = self.store.path
        self.requests: dict[str, RolePrivateStudioRequest] = {}
        self._load()

    def list_requests(self, status: str | None = None) -> list[RolePrivateStudioRequest]:
        items = sorted(self.requests.values(), key=lambda item: item.updated_at, reverse=True)
        if status is None:
            return items
        return [item for item in items if item.status == status]

    def get_request(self, request_id: str) -> RolePrivateStudioRequest:
        if request_id not in self.requests:
            raise KeyError(f'Role Private Studio request not found: {request_id}')
        return self.requests[request_id]

    def save_request(self, request: RolePrivateStudioRequest) -> RolePrivateStudioRequest:
        self.requests[request.request_id] = request
        self._save()
        return request

    def _load(self) -> None:
        data = self.store.read(default={})
        self.requests = {
            request_id: RolePrivateStudioRequest.from_dict(item)
            for request_id, item in data.get('requests', {}).items()
        }

    def _save(self) -> None:
        payload = {
            'generated_at': utc_now(),
            'requests': {request_id: request.to_dict() for request_id, request in sorted(self.requests.items())},
        }
        self.store.write(payload)
