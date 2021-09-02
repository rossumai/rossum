from functools import partial

import pytest

from rossum.lib.api_client import RossumClient, RossumException
from tests.conftest import INBOXES_URL, match_uploaded_json, QUEUES_URL


@pytest.mark.usefixtures("rossum_credentials")
class TestRossumClient:
    rossum_client = RossumClient(None)

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
