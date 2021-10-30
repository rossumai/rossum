from functools import partial

import pytest

from rossum.lib.api_client import RossumClient, RossumException
from tests.conftest import INBOXES_URL, match_uploaded_json, QUEUES_URL, EMPTY_PDF_FILE, HOOKS_URL

QUEUE_ID = 600500


@pytest.mark.usefixtures("rossum_credentials")
class TestRossumClient:
    rossum_client = RossumClient(None)

    @pytest.mark.usefixtures("mock_login_request")
    def test_create_hook_extension_source(self, requests_mock):
        kwargs = dict(
            name="name1",
            hook_type="hook_type1",
            queues=[24412],
            active=True,
            events=["annotation_content.initialize", "annotation_content.user_update"],
            sideload=[],
            config={"url": "httpmock:/adfa.asdf", "secret": "sdf", "insecure_ssl": False},
            token_owner="httpmock://tokenowner.url",
            extension_source="rossum_store",
        )

        def matcher(request):
            request_dict = request.json()
            for key in kwargs:
                if key == "hook_type":
                    assert request_dict["type"] == kwargs[key]
                else:
                    assert request_dict[key] == kwargs[key]
            return {"id": 100200}

        requests_mock.post(
            HOOKS_URL, json={"id": 100200}, status_code=201, additional_matcher=matcher
        )
        self.rossum_client.create_hook(**kwargs)

    @pytest.mark.usefixtures("mock_login_request")
    def test_create_inbox_with_email_prefix(self, requests_mock):
        queue_url = f"{QUEUES_URL}/1"
        requests_mock.post(
            INBOXES_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": "My Email",
                    "email_prefix": "my-email-prefix",
                    "bounce_email_to": None,
                    "bounce_unprocessable_attachments": False,
                    "queues": [queue_url],
                },
            ),
            json={"id": 100200},
            status_code=201,
        )
        self.rossum_client.create_inbox(
            name="My Email",
            email_prefix="my-email-prefix",
            bounce_email=None,
            queue_url=queue_url,
            email=None,
        )
        assert requests_mock.called

    @pytest.mark.usefixtures("mock_login_request")
    def test_create_inbox_with_email(self, requests_mock):
        queue_url = f"{QUEUES_URL}/1"
        requests_mock.post(
            INBOXES_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": "My Email",
                    "email_prefix": None,
                    "email": "my_email@my_company.com",
                    "bounce_email_to": None,
                    "bounce_unprocessable_attachments": False,
                    "queues": [queue_url],
                },
            ),
            json={"id": 100200},
            status_code=201,
        )
        self.rossum_client.create_inbox(
            name="My Email",
            email_prefix=None,
            bounce_email=None,
            queue_url=queue_url,
            email="my_email@my_company.com",
        )
        assert requests_mock.called

    @pytest.mark.usefixtures("mock_login_request")
    def test_create_inbox_failed(self, requests_mock):
        queue_url = f"{QUEUES_URL}/1"
        with pytest.raises(RossumException):
            self.rossum_client.create_inbox(
                name="My Email", email_prefix=None, bounce_email=None, queue_url=queue_url, email=""
            )

    def test_upload_document_as_bytes_success(self, requests_mock):
        requests_mock.post(f"{QUEUES_URL}/{QUEUE_ID}/upload", json={"id": 100200}, status_code=201)
        self.rossum_client.upload_document(
            id_=QUEUE_ID,
            filename_overwrite="My Invoice.pdf",
            values={"upload:organization_unit": "Sales"},
            metadata={"SAP_ID": 123456},
            file_bytes=EMPTY_PDF_FILE,
        )
        assert requests_mock.called

    def test_upload_document_filename_not_passed(self):
        with pytest.raises(RossumException):
            self.rossum_client.upload_document(
                id_=QUEUE_ID,
                values={"upload:organization_unit": "Sales"},
                metadata={"SAP_ID": 123456},
                file_bytes=EMPTY_PDF_FILE,
            )

    def test_upload_document_files_not_passed(self):
        with pytest.raises(RossumException):
            self.rossum_client.upload_document(
                id_=QUEUE_ID,
                values={"upload:organization_unit": "Sales"},
                metadata={"SAP_ID": 123456},
            )

    def test_get_paginated_with_ambiguous_sideloading(self):
        with pytest.raises(RossumException) as ex:
            self.rossum_client.get_paginated(
                QUEUES_URL, query={"sideload": "workspaces"}, sideloads=["workspaces"]
            )
        assert "sideloading cannot be specified both in query and sideloads" == str(ex.value)
