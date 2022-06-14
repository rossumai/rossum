from typing import Optional, Union, Dict, List, Iterable, Sequence, Any


class APIObject:
    pass


class Sideload:
    pass


class ElisAPIClient:
    def __init__(self, endpoint="https://api.elis.rossum.ai", auth_token=None, version="v1"):
        """Setups connection. If credentials is None, it reads $ELIS_CONFIG by configparser
        (default is config/elis.ini)
        """
        self.endpoint = endpoint.strip("/") + "/" + version
        self._auth_token = auth_token
        self._auth_header = None

    def get_queues(
        self,
        sideloads: Optional[Iterable[APIObject]] = None,
        *,
        any_of_ids: Optional[Iterable[int]] = None,
        workspace: Optional[int] = None,
        users: Optional[Iterable[int]] = None,
        hooks: Optional[Iterable[int]] = None,
    ) -> List[dict]:
        return [{}]

    def get_schema(self, schema):
        pass

    def get_paginated(
        self,
        url: str,
        params: Dict[str, Any] = None,
        sideloads: Sequence[str] = None,
        page_count: int = None,
    ):
        pass

    def get_organizations(self):
        pass

    def get_queue_metadata(self, queue):
        pass

    def update_queue_metadata(self, queue, data):
        pass

    def update_queue_metadata_key(self, queue, key, value):
        pass

    def update_annotation_metadata(self, annotation, data):
        pass

    def update_annotation(self, annotation, data):
        pass

    def upload(self, file_name, queue):
        pass

    def get_user(self):
        pass

    def get_workspaces(
        self,
        sideloads: Optional[Iterable[APIObject]] = None,
        *,
        organization: Optional[int] = None,
    ) -> List[dict]:
        return []

    def get_workspace(
        self, id_: Optional[int] = None, sideloads: Optional[Iterable[APIObject]] = None
    ) -> dict:
        return {}

    def get_queue(
        self, id_: Optional[int] = None, sideloads: Optional[Iterable[APIObject]] = None
    ) -> dict:
        return {}

    def get_users(
        self,
        sideloads: Optional[Iterable[APIObject]] = None,
        *,
        username: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[dict]:
        return []

    def get_groups(self, *, group_name: Optional[str]) -> List[dict]:
        return []

    def get_connectors(self, sideloads: Optional[Iterable[APIObject]] = None) -> List[dict]:
        return []

    def get_hooks(
        self, sideloads: Optional[Iterable[APIObject]] = None, query: Dict = None
    ) -> List[dict]:
        return []

    def get_annotation(self, id_: Optional[int] = None) -> dict:
        return {}

    def get_annotations(
        self,
        *,
        queue: Optional[int] = None,
        status: Optional[Iterable[str]] = None,
        sideloads: Optional[Iterable[Union[Sideload, str]]] = None,
    ):
        pass

    # def get_annotations(
    # self,
    # filters: Dict[str, Any] = None,
    # fields: Sequence[str] = None,
    # page_size: int = None,
    # sideload: Sequence[str] = None,
    # page_count: int = None,
    # ):
    # pass

    def create_workspace(
        self, name: str, organization: str, metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        return {}

    def create_schema(self, name: str, content: List[dict]) -> dict:
        return {}

    def create_queue(
        self,
        name: str,
        workspace_url: str,
        schema_url: str,
        connector_url: Optional[str] = None,
        hooks_urls: Optional[List] = None,
        locale: Optional[str] = None,
        rir_url: str = "https://all.rir.rossum.ai",
        rir_params: str = "",
    ) -> dict:
        return {}

    def create_inbox(
        self,
        name: str,
        email_prefix: Optional[str],
        bounce_email: Optional[str],
        queue_url: str,
        email: Optional[str] = None,
    ) -> dict:
        return {}

    def create_user(
        self,
        username: str,
        organization: str,
        queues: List[str],
        password: str,
        group: str,
        locale: str,
    ) -> dict:
        return {}

    def change_user_password(self, new_password: str) -> dict:
        return {}

    def reset_user_password(self, email: str) -> dict:
        return {}

    def create_connector(
        self,
        name: str,
        queues: List[str],
        service_url: str,
        authorization_token: str = None,
        params: Optional[str] = None,
        asynchronous: Optional[bool] = True,
    ) -> dict:
        return {}

    def create_hook(
        self,
        name: str,
        hook_type: str,
        queues: List[str],
        active: bool,
        events: List[str],
        sideload: List[str],
        config: Dict,
        run_after: List[str] = None,
        metadata: Optional[Dict] = None,
        token_owner: Optional[str] = "",
        test: Optional[Dict] = None,
        **kwargs: Any,
    ) -> dict:
        return {}

    def upload_document(
        self,
        id_: int,
        file: Optional[str] = "",
        filename_overwrite: str = "",
        values: Dict[str, str] = None,
        metadata: Optional[Dict] = None,
        file_bytes: Optional[bytes] = None,
    ) -> dict:
        return {}

    def set_metadata(self, object_type: APIObject, object_id: int, metadata: Dict[str, Any]):
        pass

    def export_data(self, id_: int, annotation_ids: Iterable[int], format_: str) -> dict:
        return {}

    def get_schemas(self, sideloads: Optional[Iterable[APIObject]] = None) -> List[dict]:
        return []
