import json
from functools import partial

import click
import pytest
import requests

from rossum.lib import APIObject, ANNOTATIONS
from rossum.lib.api_client import APIClient, RossumClient
from tests.conftest import (
    ANNOTATIONS_URL,
    API_URL,
    SCHEMAS_URL,
    USERS_URL,
    ORGANIZATIONS_URL,
    PAGES_URL,
    TOKEN,
    LOGIN_URL,
    REQUEST_HEADERS,
    DOCUMENTS_URL,
    QUEUES_URL,
    match_uploaded_data,
    match_uploaded_json,
    match_uploaded_values,
    WORKSPACES_URL,
)

UPLOADED_DOC = f"{DOCUMENTS_URL}/12345"
SCHEMA_ID = 398431
SCHEMA_URL = f"{SCHEMAS_URL}/{SCHEMA_ID}"
QUEUE_ID = 20202
QUEUE_URL = f"{QUEUES_URL}/{QUEUE_ID}"
UPLOAD_ENDPOINT = f"{QUEUE_URL}/upload"
DOCUMENT_ID = 315511
DOCUMENT_URL = f"{DOCUMENTS_URL}/{DOCUMENT_ID}"
PAGE_ID = 4210254
PAGE_URL = f"{PAGES_URL}/{PAGE_ID}"
ANNOTATION_ID = 1863864
ANNOTATION_URL = f"{ANNOTATIONS_URL}/{ANNOTATION_ID}"
ORGANIZATION_ID = 1
ORGANIZATION_URL = f"{ORGANIZATIONS_URL}/{ORGANIZATION_ID}"


@pytest.mark.usefixtures("rossum_credentials")
class TestAPIClient:
    api_client = APIClient(None)
    username = "some"
    password = "secret"
    login_data = {"username": username, "password": password}

    def test_get_token_success(self, requests_mock, isolated_cli_runner):
        requests_mock.post(
            LOGIN_URL,
            additional_matcher=partial(match_uploaded_json, self.login_data),
            json={"key": TOKEN},
        )
        with isolated_cli_runner.isolation():
            assert TOKEN == self.api_client.get_token()

    def test_get_token_with_custom_lifetime(self, requests_mock):
        token_lifetime = 3600
        login_data = {
            "username": self.username,
            "password": self.password,
            "max_token_lifetime_s": token_lifetime,
        }
        requests_mock.post(
            LOGIN_URL,
            additional_matcher=partial(match_uploaded_json, login_data),
            json={"key": TOKEN},
        )
        assert TOKEN == APIClient(None, max_token_lifetime=token_lifetime).get_token()

    def test_get_token_failed(self, requests_mock):
        requests_mock.post(
            LOGIN_URL,
            additional_matcher=partial(match_uploaded_json, self.login_data),
            status_code=401,
        )
        with pytest.raises(click.ClickException) as e:
            self.api_client.get_token()
        assert "Login failed with the provided credentials." == str(e.value)

    def test_get_token_error(self, requests_mock):
        error_json = {"password": ["required"]}
        requests_mock.post(
            LOGIN_URL,
            additional_matcher=partial(match_uploaded_json, self.login_data),
            status_code=400,
            json=error_json,
        )
        with pytest.raises(click.ClickException) as e:
            self.api_client.get_token()
        assert f"Invalid response [{LOGIN_URL}]: {json.dumps(error_json)}" == str(e.value)

    @pytest.mark.usefixtures("mock_login_request")
    def test_user_agent_header(self, requests_mock, isolated_cli_runner):
        requests_mock.get(API_URL + "/v1/", request_headers=REQUEST_HEADERS)
        with isolated_cli_runner.isolation():
            self.api_client.get("")
        assert requests_mock.called


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
class TestSideload:
    api_client = APIClient(None)
    url = f"{API_URL}/v1/tests"
    obj_url = f"{url}/1"
    sideloaded_obj = {"url": obj_url, "some": "test"}
    TESTS = APIObject("tests")

    def test_sideload_singular(self, requests_mock):
        requests_mock.get(self.url, json=self._paginated_rsp())

        res = self.api_client._sideload([{"test": self.obj_url}], (self.TESTS,))
        assert res == [{"test": self.sideloaded_obj}]

    def test_sideload_plural(self, requests_mock):
        requests_mock.get(self.url, json=self._paginated_rsp())

        res = self.api_client._sideload([{"tests": [self.obj_url]}], (self.TESTS,))
        assert res == [{"tests": [self.sideloaded_obj]}]

    def test_sideload_not_reachable_singular(self, requests_mock):
        requests_mock.get(self.url, json=self._paginated_rsp(0))

        res = self.api_client._sideload([{"test": self.obj_url}], (self.TESTS,))
        assert res == [{"test": {}}]

    def test_sideload_not_reachable_plural(self, requests_mock):
        requests_mock.get(self.url, json=self._paginated_rsp(0))

        res = self.api_client._sideload([{"tests": [self.obj_url]}], (self.TESTS,))
        assert res == [{"tests": []}]

    def _paginated_rsp(self, total: int = 1):
        assert total <= 1, "URL in sideloaded_obj is not unique."
        return {
            "results": [self.sideloaded_obj for _ in range(total)],
            "pagination": {"next": None, "total": total},
        }


@pytest.mark.usefixtures("rossum_credentials")
class TestRossumClient:
    api_client = RossumClient(None)

    @pytest.mark.usefixtures("mock_login_request")
    def test_get_organization_old_api(self, requests_mock):
        organization_json = {"test": "test"}

        user_url = f"{USERS_URL}/1"
        organization_url = f"{ORGANIZATIONS_URL}/1"
        requests_mock.get(f"{API_URL}/v1/auth/user", json={"url": user_url})
        requests_mock.get(user_url, json={"organization": organization_url})
        requests_mock.get(organization_url, json=organization_json)

        assert organization_json == self.api_client.get_organization()
        assert requests_mock.called

    @pytest.mark.usefixtures("mock_login_request")
    def test_upload_overwrite_filename(self, requests_mock, mock_file):
        original_filename = "empty_file.pdf"
        overwritten_filename = "Overwritten filename.pdf"
        api_response = {"results": [{"document": DOCUMENT_URL}]}

        requests_mock.post(
            UPLOAD_ENDPOINT,
            additional_matcher=partial(match_uploaded_data, original_filename),
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={"results": [{"document": DOCUMENT_URL}]},
            status_code=201,
        )

        assert api_response == self.api_client.upload_document(QUEUE_ID, mock_file)

        requests_mock.post(
            UPLOAD_ENDPOINT,
            additional_matcher=partial(match_uploaded_data, overwritten_filename),
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={"results": [{"document": DOCUMENT_URL}]},
            status_code=201,
        )

        assert api_response == self.api_client.upload_document(
            QUEUE_ID, mock_file, overwritten_filename
        )

    @pytest.mark.usefixtures("mock_login_request")
    def test_upload_values(self, requests_mock, mock_file):
        values = {"upload:key_1": "value_1", "upload:key_2": "value_2"}
        api_response = {
            "document": DOCUMENT_URL,
            "annotation": ANNOTATION_URL,
            "results": [{"document": DOCUMENT_URL, "annotation": ANNOTATION_URL}],
        }

        requests_mock.post(
            UPLOAD_ENDPOINT,
            additional_matcher=partial(match_uploaded_values, values),
            request_headers={"Authorization": f"Token {TOKEN}"},
            json=api_response,
            status_code=201,
        )

        assert api_response == self.api_client.upload_document(QUEUE_ID, mock_file, values=values)

    @pytest.mark.usefixtures("mock_login_request")
    def test_set_metadata(self, requests_mock):
        metadata = {"key_1": 42, "key_2": "str_value", "nested_key": {"key_a": "value_a"}}
        api_response = {
            "document": DOCUMENT_URL,
            "id": DOCUMENT_ID,
            "queue": QUEUE_URL,
            "schema": SCHEMA_URL,
            "pages": [PAGE_URL],
            "modifier": None,
            "modified_at": None,
            "confirmed_at": None,
            "exported_at": None,
            "assigned_at": None,
            "status": "to_review",
            "rir_poll_id": "de8fb2e5877741bf97808eda",
            "messages": None,
            "url": ANNOTATION_URL,
            "content": f"{ANNOTATION_URL}/content",
            "time_spent": 0.0,
            "metadata": metadata,
        }

        requests_mock.patch(
            ANNOTATION_URL,
            additional_matcher=partial(match_uploaded_json, {"metadata": metadata}),
            request_headers={"Authorization": f"Token {TOKEN}"},
            json=api_response,
            status_code=200,
        )

        assert api_response == self.api_client.set_metadata(ANNOTATIONS, ANNOTATION_ID, metadata)

    @pytest.mark.usefixtures("mock_login_request")
    def test_create_workspace(self, requests_mock):
        name = "TestName"
        metadata = {"customer-id": "some-customer-id"}

        api_response = {"name": name, "organization": ORGANIZATION_URL, "metadata": metadata}

        requests_mock.post(
            WORKSPACES_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {"name": name, "organization": ORGANIZATION_URL, "metadata": metadata},
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json=api_response,
        )
        assert api_response == self.api_client.create_workspace(name, ORGANIZATION_URL, metadata)

    @pytest.mark.parametrize(
        "queue_id, status, sideloads",
        [
            (None, None, None),
            (QUEUE_ID, None, None),
            (QUEUE_ID, "exported", None),
            (QUEUE_ID, "exported", ["documents"]),
        ],
    )
    @pytest.mark.usefixtures("mock_login_request")
    def test_get_annotations(self, requests_mock, queue_id, status, sideloads):
        assert not sideloads or sideloads == [
            "documents"
        ], "test requires extention to more sideload types"

        def get_document(document_id: int, sideloaded: bool):
            document_obj = {"id": document_id, "url": f"{DOCUMENTS_URL}/{document_id}"}
            return document_obj if sideloaded else document_obj["url"]

        num_documents = 3
        annotations = [
            {
                "id": document_id,
                "url": f"{ANNOTATIONS_URL}/{document_id}",
                "queue": f"{QUEUES_URL}/{queue_id}",
                "document": f"{DOCUMENTS_URL}/{document_id}",
                "status": status,
            }
            for document_id in range(num_documents)
        ]
        documents = [get_document(document_id, True) for document_id in range(num_documents)]

        annotations_base_url = build_annotations_base_url(queue_id, status, sideloads)
        api_response_pages = {
            annotations_base_url: {
                "pagination": {
                    "total": num_documents,
                    "total_pages": 2,
                    "previous": None,
                    "next": f"{annotations_base_url}&page=2",
                },
                "results": annotations[:1],
                "documents": documents[:1],
            },
            f"{annotations_base_url}&page=2": {
                "pagination": {
                    "total": num_documents,
                    "total_pages": 2,
                    "previous": f"{annotations_base_url}",
                    "next": None,
                },
                "results": annotations[1:],
                "documents": documents[1:],
            },
        }

        for response_content in api_response_pages.values():
            if "documents" not in (sideloads or []):
                del response_content["documents"]

        expected = [
            {
                "id": document_id,
                "url": f"{ANNOTATIONS_URL}/{document_id}",
                "queue": f"{QUEUES_URL}/{queue_id}",
                "document": get_document(document_id, "documents" in (sideloads or [])),
                "status": status,
            }
            for document_id in range(num_documents)
        ]

        for mock_url, mock_data in api_response_pages.items():
            requests_mock.get(
                mock_url,
                request_headers={"Authorization": f"Token {TOKEN}"},
                json=mock_data,
                status_code=200,
            )

        assert expected == self.api_client.get_annotations(
            queue=queue_id, status=([status] if status else None), sideloads=sideloads
        )


@pytest.mark.usefixtures("rossum_credentials")
class TestRetryMechanism:
    api_client = RossumClient(None, retry_logic_rules={"attempts": 2, "wait_s": 0.1})

    @pytest.mark.usefixtures("mock_login_request")
    def test_retry_logic_if_api_responds_with_502(self, requests_mock):
        user_json = {"user": 123}
        get_user_called = requests_mock.get(
            f"{API_URL}/v1/auth/user",
            [
                {"exc": requests.exceptions.ConnectionError("Connection refused")},
                {"json": user_json, "status_code": 200},
            ],
        )
        assert user_json == self.api_client.get_user()
        assert get_user_called.call_count == 2


def build_annotations_base_url(queue_id, status, sideloads):
    query = {}
    if queue_id is not None:
        query["queue"] = queue_id
    if status is not None:
        query["status"] = status
    if sideloads is None:
        sideloads = []
    if sideloads:
        query["sideload"] = ",".join(str(s) for s in sideloads)
    query = "&".join(f"{k}={v}" for k, v in query.items())
    return ANNOTATIONS_URL + (f"?{query}" if query else "")
