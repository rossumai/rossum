import re
from functools import partial
from itertools import chain
from pathlib import Path
from traceback import print_tb, format_tb

import pytest

from elisctl.hook import list_command, change_command, delete_command, create_command
from tests.conftest import TOKEN, match_uploaded_json, QUEUES_URL, HOOKS_URL

QUEUES = ["1", "2"]
QUEUE_ID = "12345"
QUEUES_URLS = [f"{QUEUES_URL}/{id_}" for id_ in QUEUES]
DEFAULT_QUEUE_URL = f"{QUEUES_URL}/{QUEUE_ID}"

HOOK_ID = "101"
HOOK_NAME = "My First Hook"
EVENTS = ["annotation_status", "another_event"]
CONFIG_URL = "http://hook.somewhere.com:5000"
CONFIG_SECRET = "some_secret_key"
CONFIG_CODE = "tests/data/snippet_code.js"
CONFIG_RUNTIME = "nodejs12.x"
ACTIVE = True


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
class TestCreate:
    def test_success_if_type_webhook(self, requests_mock, cli_runner):
        requests_mock.get(
            re.compile(fr"{QUEUES_URL}/\d$"),
            json=lambda request, context: {"url": request.url},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            HOOKS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": HOOK_NAME,
                    "type": "webhook",
                    "queues": QUEUES_URLS,
                    "active": ACTIVE,
                    "events": EVENTS,
                    "config": {"url": CONFIG_URL, "secret": CONFIG_SECRET, "insecure_ssl": False},
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "type": "webhook",
                "queues": [DEFAULT_QUEUE_URL],
                "events": EVENTS,
                "config": {"url": CONFIG_URL, "secret": CONFIG_SECRET, "insecure_ssl": False},
            },
        )

        result = cli_runner.invoke(
            create_command,
            [HOOK_NAME]
            + list(chain.from_iterable(("-q", q) for q in QUEUES))
            + list(chain.from_iterable(("-e", e) for e in EVENTS))
            + [
                "--active",
                ACTIVE,
                "--hook-type",
                "webhook",
                "--config-url",
                CONFIG_URL,
                "--config-secret",
                CONFIG_SECRET,
                "--config_insecure_ssl",
                False,
            ],
        )

        assert not result.exit_code, print_tb(result.exc_info[2])
        assert result.output == (
            f"{HOOK_ID}, {HOOK_NAME}, ['{DEFAULT_QUEUE_URL}'], {EVENTS}, {CONFIG_URL}, {CONFIG_SECRET}\n"
        )

    def test_success_if_type_function(self, requests_mock, cli_runner):
        requests_mock.get(
            re.compile(fr"{QUEUES_URL}/\d$"),
            json=lambda request, context: {"url": request.url},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            HOOKS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": HOOK_NAME,
                    "type": "function",
                    "queues": QUEUES_URLS,
                    "active": ACTIVE,
                    "events": EVENTS,
                    "config": {"code": Path(CONFIG_CODE).read_text(), "runtime": CONFIG_RUNTIME},
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "type": "function",
                "queues": [DEFAULT_QUEUE_URL],
                "events": EVENTS,
                "config": {"code": CONFIG_CODE, "runtime": CONFIG_RUNTIME},
            },
        )

        result = cli_runner.invoke(
            create_command,
            [HOOK_NAME]
            + list(chain.from_iterable(("-q", q) for q in QUEUES))
            + list(chain.from_iterable(("-e", e) for e in EVENTS))
            + [
                "--active",
                ACTIVE,
                "--hook-type",
                "function",
                "--config-code",
                CONFIG_CODE,
                "--config-runtime",
                CONFIG_RUNTIME,
            ],
        )

        assert not result.exit_code, print_tb(result.exc_info[2])
        assert result.output == (f"{HOOK_ID}, {HOOK_NAME}, ['{DEFAULT_QUEUE_URL}'], {EVENTS}\n")

    def test_illegal_usage_if_type_webhook(self, requests_mock, cli_runner):
        requests_mock.get(
            re.compile(fr"{QUEUES_URL}/\d$"),
            json=lambda request, context: {"url": request.url},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            HOOKS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": HOOK_NAME,
                    "type": "webhook",
                    "queues": QUEUES_URLS,
                    "active": ACTIVE,
                    "events": EVENTS,
                    "config": {
                        "url": CONFIG_URL,
                        "secret": CONFIG_SECRET,
                        "insecure_ssl": False,
                        "config_runtime": CONFIG_RUNTIME,
                    },
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "type": "webhook",
                "queues": [DEFAULT_QUEUE_URL],
                "events": EVENTS,
                "config": {
                    "url": CONFIG_URL,
                    "secret": CONFIG_SECRET,
                    "insecure_ssl": False,
                    "config_runtime": CONFIG_RUNTIME,
                },
            },
        )

        result = cli_runner.invoke(
            create_command,
            [HOOK_NAME]
            + list(chain.from_iterable(("-q", q) for q in QUEUES))
            + list(chain.from_iterable(("-e", e) for e in EVENTS))
            + [
                "--active",
                ACTIVE,
                "--hook-type",
                "webhook",
                "--config-url",
                CONFIG_URL,
                "--config-secret",
                CONFIG_SECRET,
                "--config_insecure_ssl",
                False,
                "--config-runtime",
                CONFIG_RUNTIME,
            ],
        )

        assert result.exit_code, print_tb(result.exc_info[2])
        assert result.output == (
            "Usage: create [OPTIONS] NAME\n"
            "Try 'create --help' for help.\n\n"
            "Error: Illegal usage: --config_runtime is mutually exclusive with --hook-type=webhook\n"
            ""
        )

    def test_illegal_usage_if_type_function(self, requests_mock, cli_runner):
        requests_mock.get(
            re.compile(fr"{QUEUES_URL}/\d$"),
            json=lambda request, context: {"url": request.url},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            HOOKS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": HOOK_NAME,
                    "type": "function",
                    "queues": QUEUES_URLS,
                    "active": ACTIVE,
                    "events": EVENTS,
                    "config": {
                        "code": Path(CONFIG_CODE).read_text(),
                        "runtime": CONFIG_RUNTIME,
                        "url": CONFIG_URL,
                    },
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "type": "function",
                "queues": [DEFAULT_QUEUE_URL],
                "events": EVENTS,
                "config": {"code": CONFIG_CODE, "runtime": CONFIG_RUNTIME, "url": CONFIG_URL},
            },
        )

        result = cli_runner.invoke(
            create_command,
            [HOOK_NAME]
            + list(chain.from_iterable(("-q", q) for q in QUEUES))
            + list(chain.from_iterable(("-e", e) for e in EVENTS))
            + [
                "--active",
                ACTIVE,
                "--hook-type",
                "function",
                "--config-code",
                CONFIG_CODE,
                "--config-runtime",
                CONFIG_RUNTIME,
                "--config-url",
                CONFIG_URL,
            ],
        )

        assert result.exit_code, print_tb(result.exc_info[2])
        assert result.output == (
            "Usage: create [OPTIONS] NAME\n"
            "Try 'create --help' for help.\n\n"
            "Error: Illegal usage: --config_url is mutually exclusive with --hook-type=function\n"
            ""
        )

    def test_missing_option_if_type_webhook(self, requests_mock, cli_runner):
        requests_mock.get(
            re.compile(fr"{QUEUES_URL}/\d$"),
            json=lambda request, context: {"url": request.url},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            HOOKS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": HOOK_NAME,
                    "type": "webhook",
                    "queues": QUEUES_URLS,
                    "active": ACTIVE,
                    "events": EVENTS,
                    "config": {"url": CONFIG_URL, "secret": CONFIG_SECRET},
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "type": "webhook",
                "queues": [DEFAULT_QUEUE_URL],
                "events": EVENTS,
                "config": {"url": CONFIG_URL, "secret": CONFIG_SECRET},
            },
        )

        result = cli_runner.invoke(
            create_command,
            [HOOK_NAME]
            + list(chain.from_iterable(("-q", q) for q in QUEUES))
            + list(chain.from_iterable(("-e", e) for e in EVENTS))
            + [
                "--active",
                ACTIVE,
                "--hook-type",
                "webhook",
                "--config-url",
                CONFIG_URL,
                "--config-secret",
                CONFIG_SECRET,
            ],
        )

        assert result.exit_code, print_tb(result.exc_info[2])
        assert result.output == (
            "Usage: create [OPTIONS] NAME\n"
            "Try 'create --help' for help.\n\n"
            "Error: Missing option '--config_insecure_ssl'.  Required if --hook-type=webhook\n"
        )

    def test_missing_option_if_type_function(self, requests_mock, cli_runner):
        requests_mock.get(
            re.compile(fr"{QUEUES_URL}/\d$"),
            json=lambda request, context: {"url": request.url},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        requests_mock.post(
            HOOKS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": HOOK_NAME,
                    "type": "function",
                    "queues": QUEUES_URLS,
                    "active": ACTIVE,
                    "events": EVENTS,
                    "config": {"code": CONFIG_CODE},
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "type": "function",
                "queues": [DEFAULT_QUEUE_URL],
                "events": EVENTS,
                "config": {"code": CONFIG_CODE},
            },
        )

        result = cli_runner.invoke(
            create_command,
            [HOOK_NAME]
            + list(chain.from_iterable(("-q", q) for q in QUEUES))
            + list(chain.from_iterable(("-e", e) for e in EVENTS))
            + ["--active", ACTIVE, "--hook-type", "function", "--config-code", CONFIG_CODE],
        )

        assert result.exit_code, print_tb(result.exc_info[2])
        assert result.output == (
            "Usage: create [OPTIONS] NAME\n"
            "Try 'create --help' for help.\n\n"
            "Error: Missing option '--config-runtime'.  Required if --hook-type=function\n"
        )

    def test_missing_queue_id(self, requests_mock, cli_runner):
        requests_mock.get(
            QUEUES_URL,
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"id": QUEUE_ID, "url": DEFAULT_QUEUE_URL}],
            },
        )

        requests_mock.post(
            HOOKS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": HOOK_NAME,
                    "type": "webhook",
                    "queues": [DEFAULT_QUEUE_URL],
                    "active": ACTIVE,
                    "events": EVENTS,
                    "config": {"url": CONFIG_URL, "secret": CONFIG_SECRET, "insecure_ssl": False},
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "type": "webhook",
                "queues": [f"{QUEUES_URL}/{QUEUE_ID}"],
                "events": EVENTS,
                "config": {"url": CONFIG_URL, "secret": CONFIG_SECRET, "insecure_ssl": False},
            },
        )

        requests_mock.get(
            HOOKS_URL,
            json={"results": [{"id": HOOK_ID, "name": HOOK_NAME, "queues": [DEFAULT_QUEUE_URL]}]},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )

        result = cli_runner.invoke(
            create_command,
            [HOOK_NAME]
            + list(chain.from_iterable(("-e", e) for e in EVENTS))
            + [
                "--active",
                ACTIVE,
                "--hook-type",
                "webhook",
                "--config-url",
                CONFIG_URL,
                "--config-secret",
                CONFIG_SECRET,
                "--config_insecure_ssl",
                False,
            ],
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert (
            f"{HOOK_ID}, {HOOK_NAME}, ['{DEFAULT_QUEUE_URL}'], {EVENTS}, {CONFIG_URL}, {CONFIG_SECRET}\n"
            == result.output
        )


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
class TestList:
    def test_success_if_type_webhook(self, requests_mock, cli_runner):
        webhook_option = ["--hook-type", "webhook"]
        result = self._test_list(cli_runner, requests_mock, True, webhook_option)

        expected_table = f"""\
  id  name           events                              queues  active    url                             insecure_ssl    secret
----  -------------  --------------------------------  --------  --------  ------------------------------  --------------  ---------------
 {HOOK_ID}  {HOOK_NAME}  {", ".join(e for e in EVENTS)}     {QUEUE_ID}  {ACTIVE}      {CONFIG_URL}  False           {CONFIG_SECRET}
"""
        assert result.output == expected_table

    def test_non_admin_does_not_see_auth_token__if_type_webhook(self, requests_mock, cli_runner):
        webhook_option = ["--hook-type", "webhook"]
        result = self._test_list(cli_runner, requests_mock, False, webhook_option)

        expected_table = f"""\
  id  name           events                              queues  active    url                             insecure_ssl
----  -------------  --------------------------------  --------  --------  ------------------------------  --------------
 {HOOK_ID}  {HOOK_NAME}  {", ".join(e for e in EVENTS)}     {QUEUE_ID}  {ACTIVE}      {CONFIG_URL}  False
"""
        assert result.output == expected_table

    def test_success_if_type_function(self, requests_mock, cli_runner):
        function_option = ["--hook-type", "function"]
        result = self._test_list(cli_runner, requests_mock, True, function_option)

        expected_table = f"""\
  id  name           events                              queues  active
----  -------------  --------------------------------  --------  --------
 {HOOK_ID}  {HOOK_NAME}  {", ".join(e for e in EVENTS)}     {QUEUE_ID}  {ACTIVE}
"""
        assert result.output == expected_table

    def test_non_admin_does_not_see_auth_token_if_type_function(self, requests_mock, cli_runner):
        function_option = ["--hook-type", "function"]
        result = self._test_list(cli_runner, requests_mock, False, function_option)
        expected_table = f"""\
  id  name           events                              queues  active
----  -------------  --------------------------------  --------  --------
 {HOOK_ID}  {HOOK_NAME}  {", ".join(e for e in EVENTS)}     {QUEUE_ID}  {ACTIVE}
"""
        assert result.output == expected_table

    @staticmethod
    def _test_list(cli_runner, requests_mock, include_secret: bool, option):
        queue_url = f"{QUEUES_URL}/{QUEUE_ID}"
        requests_mock.get(
            f"{QUEUES_URL}",
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"url": queue_url, "id": QUEUE_ID}],
            },
        )
        if option[1] == "webhook":
            hook_result = {
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "type": "webhook",
                "queues": [queue_url],
                "active": ACTIVE,
                "events": EVENTS,
                "config": {"url": CONFIG_URL, "insecure_ssl": False},
            }

            if include_secret:
                hook_result["config"].update({"secret": CONFIG_SECRET})  # type: ignore

            requests_mock.get(
                HOOKS_URL, json={"pagination": {"total": 1, "next": None}, "results": [hook_result]}
            )

        elif option[1] == "function":

            hook_result = {
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "type": "function",
                "queues": [queue_url],
                "active": ACTIVE,
                "events": EVENTS,
                "config": {"code": Path(CONFIG_CODE).read_text(), "runtime": CONFIG_RUNTIME},
            }

            requests_mock.get(
                HOOKS_URL, json={"pagination": {"total": 1, "next": None}, "results": [hook_result]}
            )

        result = cli_runner.invoke(list_command, option)
        assert not result.exit_code, format_tb(result.exc_info[2])
        return result


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
class TestChange:
    new_hook_name = "My patched new name"
    new_event = "new_event"

    def test_success_if_type_webhook(self, requests_mock, cli_runner):

        requests_mock.get(f"{QUEUES_URL}/{QUEUE_ID}", json={"url": f"{QUEUES_URL}/{QUEUE_ID}"})

        requests_mock.patch(
            f"{HOOKS_URL}/{HOOK_ID}",
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "queues": [f"{QUEUES_URL}/{QUEUE_ID}"],
                    "name": self.new_hook_name,
                    "type": "webhook",
                    "events": [self.new_event],
                    "active": True,
                    "config": {"url": CONFIG_URL, "secret": CONFIG_SECRET, "insecure_ssl": False},
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=200,
        )

        result = cli_runner.invoke(
            change_command,
            [
                HOOK_ID,
                "-q",
                QUEUE_ID,
                "-n",
                self.new_hook_name,
                "-e",
                self.new_event,
                "--hook-type",
                "webhook",
                "--config-url",
                CONFIG_URL,
                "--config-secret",
                CONFIG_SECRET,
                "--config_insecure_ssl",
                False,
            ],
        )

        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output

    def test_noop_if_type_webhook(self, requests_mock, cli_runner):
        cli_runner.invoke(change_command, [HOOK_ID])
        assert not requests_mock.called

    def test_success_if_type_function(self, requests_mock, cli_runner):

        requests_mock.get(f"{QUEUES_URL}/{QUEUE_ID}", json={"url": f"{QUEUES_URL}/{QUEUE_ID}"})

        requests_mock.patch(
            f"{HOOKS_URL}/{HOOK_ID}",
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "queues": [f"{QUEUES_URL}/{QUEUE_ID}"],
                    "name": self.new_hook_name,
                    "type": "function",
                    "events": [self.new_event],
                    "active": True,
                    "config": {"code": Path(CONFIG_CODE).read_text(), "runtime": CONFIG_RUNTIME},
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=200,
        )

        result = cli_runner.invoke(
            change_command,
            [
                HOOK_ID,
                "-q",
                QUEUE_ID,
                "-n",
                self.new_hook_name,
                "-e",
                self.new_event,
                "--hook-type",
                "function",
                "--config-code",
                CONFIG_CODE,
                "--config-runtime",
                CONFIG_RUNTIME,
            ],
        )

        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output

    def test_noop_if_type_function(self, requests_mock, cli_runner):
        cli_runner.invoke(change_command, [HOOK_ID])
        assert not requests_mock.called


@pytest.mark.usefixtures("mock_login_request", "elis_credentials")
class TestDelete:
    def test_success(self, requests_mock, cli_runner):

        requests_mock.get(
            f"{HOOKS_URL}/{HOOK_ID}",
            request_headers={"Authorization": f"Token {TOKEN}"},
            json={"id": HOOK_ID, "url": HOOKS_URL},
        )

        requests_mock.delete(
            f"{HOOKS_URL}/{HOOK_ID}",
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=204,
        )

        result = cli_runner.invoke(delete_command, [HOOK_ID, "--yes"])
        assert not result.exit_code, print_tb(result.exc_info[2])
