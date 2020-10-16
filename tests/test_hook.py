import re
from functools import partial
from itertools import chain
from pathlib import Path
from traceback import print_tb, format_tb

import pytest

from typing import List
from rossum.hook import list_command, change_command, delete_command, create_command
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
ROOT_DIR = Path(__file__).absolute().parents[1]
CONFIG_CODE = str(ROOT_DIR / "tests" / "data" / "snippet_code.js")
CONFIG_RUNTIME = "nodejs12.x"
CONFIG_INSECURE_SSL = False
ACTIVE = True


def get_params(hook_type, value):
    required_params = {
        "webhook": {
            "config": {
                "url": CONFIG_URL,
                "secret": CONFIG_SECRET,
                "insecure_ssl": CONFIG_INSECURE_SSL,
            },
            "expected_result": (f", {CONFIG_URL}, {CONFIG_SECRET}"),
            "illegal_usage_result": "--config_runtime cannot be used for the hook type webhook",
            "missing_option_result": "'--config-insecure-ssl'.  Required if hook type is webhook",
            "expected_table_without_secret": f"""\
  id  name           events                              queues  active    sideload    url                             insecure_ssl
----  -------------  --------------------------------  --------  --------  ----------  ------------------------------  --------------
 {HOOK_ID}  {HOOK_NAME}  {", ".join(e for e in EVENTS)}     {QUEUE_ID}  {ACTIVE}      ['queues']  {CONFIG_URL}  {CONFIG_INSECURE_SSL}
""",
            "expected_table": f"""\
  id  name           events                              queues  active    sideload    url                             insecure_ssl    secret
----  -------------  --------------------------------  --------  --------  ----------  ------------------------------  --------------  ---------------
 {HOOK_ID}  {HOOK_NAME}  {", ".join(e for e in EVENTS)}     {QUEUE_ID}  {ACTIVE}      ['queues']  {CONFIG_URL}  {CONFIG_INSECURE_SSL}           {CONFIG_SECRET}
""",
        },
        "function": {
            "config": {"code": Path(CONFIG_CODE).read_text(), "runtime": CONFIG_RUNTIME},
            "expected_result": "",
            "illegal_usage_result": "--config_url cannot be used for the hook type function",
            "missing_option_result": "'--config-runtime'.  Required if hook type is function",
            "expected_table": f"""\
  id  name           events                              queues  active    sideload
----  -------------  --------------------------------  --------  --------  ----------
 {HOOK_ID}  {HOOK_NAME}  {", ".join(e for e in EVENTS)}     {QUEUE_ID}  {ACTIVE}      ['queues']
""",
        },
    }

    config = required_params.get(hook_type).get("config")
    expected_result = required_params.get(hook_type).get(value)

    result = hook_type, config, expected_result

    return result


def get_options(hook_type: str, config: dict, tmp_path) -> List:
    option_list = []
    if hook_type == "function":
        p = tmp_path / "test"
        p.write_text(config["code"])
        option_list = ["--config-code", str(p), "--config-runtime", config["runtime"]]

    elif hook_type == "webhook":
        option_list = [
            "--config-secret",
            config["secret"],
            "--config-url",
            config["url"],
            "--config-insecure-ssl",
            config["insecure_ssl"],
        ]
    return option_list


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
class TestCreate:
    @pytest.mark.parametrize(
        "hook_type,config,expected",
        [(get_params("webhook", "expected_result")), (get_params("function", "expected_result"))],
    )
    def test_success(self, requests_mock, cli_runner, tmp_path, hook_type, config, expected):

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
                    "type": hook_type,
                    "queues": QUEUES_URLS,
                    "active": ACTIVE,
                    "events": EVENTS,
                    "config": config,
                    "sideload": ["queues"],
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "type": hook_type,
                "queues": [DEFAULT_QUEUE_URL],
                "events": EVENTS,
                "config": config,
                "sideload": ["queues"],
            },
        )

        result = cli_runner.invoke(
            create_command,
            [HOOK_NAME]
            + list(chain.from_iterable(("-q", q) for q in QUEUES))
            + list(chain.from_iterable(("-e", e) for e in EVENTS))
            + get_options(hook_type, config, tmp_path)
            + ["--active", ACTIVE, "--hook-type", hook_type, "--sideload", "queues"],
        )

        assert not result.exit_code, print_tb(result.exc_info[2])
        assert result.output == (
            f"{HOOK_ID}, {HOOK_NAME}, ['{DEFAULT_QUEUE_URL}'], {EVENTS}, ['queues']{expected}\n"
        )

    @pytest.mark.parametrize(
        "hook_type,config,expected",
        [
            (get_params("webhook", "illegal_usage_result")),
            (get_params("function", "illegal_usage_result")),
        ],
    )
    def test_illegal_usage(self, requests_mock, cli_runner, tmp_path, hook_type, config, expected):

        requests_mock.get(
            re.compile(fr"{QUEUES_URL}/\d$"),
            json=lambda request, context: {"url": request.url},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )
        options = get_options(hook_type, config, tmp_path)

        if hook_type == "function":
            config["url"] = CONFIG_URL
            options = options + ["--config-url", CONFIG_URL]

        elif hook_type == "webhook":
            config["runtime"] = CONFIG_RUNTIME
            options = options + ["--config-runtime", CONFIG_RUNTIME]

        requests_mock.post(
            HOOKS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": HOOK_NAME,
                    "type": hook_type,
                    "queues": QUEUES_URLS,
                    "active": ACTIVE,
                    "events": EVENTS,
                    "config": config,
                    "sideload": ["queues"],
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "type": hook_type,
                "queues": [DEFAULT_QUEUE_URL],
                "events": EVENTS,
                "config": config,
                "sideload": ["queues"],
            },
        )

        result = cli_runner.invoke(
            create_command,
            [HOOK_NAME]
            + list(chain.from_iterable(("-q", q) for q in QUEUES))
            + list(chain.from_iterable(("-e", e) for e in EVENTS))
            + ["--active", ACTIVE, "--hook-type", hook_type, "--sideload", "queues"]
            + options,
        )

        assert result.exit_code, print_tb(result.exc_info[2])
        assert result.output == (
            f"Usage: create [OPTIONS] NAME\n"
            f"Try 'create --help' for help.\n\n"
            f"Error: Illegal usage: {expected}\n"
        )

    @pytest.mark.parametrize(
        "hook_type,config,expected",
        [
            (get_params("webhook", "missing_option_result")),
            (get_params("function", "missing_option_result")),
        ],
    )
    def test_missing_option(self, requests_mock, cli_runner, tmp_path, hook_type, config, expected):

        requests_mock.get(
            re.compile(fr"{QUEUES_URL}/\d$"),
            json=lambda request, context: {"url": request.url},
            request_headers={"Authorization": f"Token {TOKEN}"},
        )
        options = get_options(hook_type, config, tmp_path)

        if hook_type == "function":
            del config["runtime"]
            options = options[:-2]

        elif hook_type == "webhook":
            del config["insecure_ssl"]
            options = options[:-2]

        requests_mock.post(
            HOOKS_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "name": HOOK_NAME,
                    "type": hook_type,
                    "queues": QUEUES_URLS,
                    "active": ACTIVE,
                    "events": EVENTS,
                    "config": config,
                    "sideload": ["queues"],
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "type": hook_type,
                "queues": [DEFAULT_QUEUE_URL],
                "events": EVENTS,
                "config": config,
                "sideload": ["queues"],
            },
        )

        result = cli_runner.invoke(
            create_command,
            [HOOK_NAME]
            + list(chain.from_iterable(("-q", q) for q in QUEUES))
            + list(chain.from_iterable(("-e", e) for e in EVENTS))
            + ["--active", ACTIVE, "--hook-type", hook_type, "--sideload", "queues"]
            + options,
        )

        assert result.exit_code, print_tb(result.exc_info[2])
        assert result.output == (
            "Usage: create [OPTIONS] NAME\n"
            "Try 'create --help' for help.\n\n"
            f"Error: Missing option {expected}\n"
        )

    @pytest.mark.parametrize(
        "hook_type,config,expected",
        [(get_params("webhook", "expected_result")), (get_params("function", "expected_result"))],
    )
    def test_missing_queue_id(
        self, requests_mock, cli_runner, tmp_path, hook_type, config, expected
    ):

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
                    "type": hook_type,
                    "queues": [DEFAULT_QUEUE_URL],
                    "active": ACTIVE,
                    "events": EVENTS,
                    "config": config,
                    "sideload": [],
                },
            ),
            request_headers={"Authorization": f"Token {TOKEN}"},
            status_code=201,
            json={
                "id": HOOK_ID,
                "name": HOOK_NAME,
                "type": hook_type,
                "queues": [f"{QUEUES_URL}/{QUEUE_ID}"],
                "events": EVENTS,
                "config": config,
                "sideload": [],
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
            + ["--active", ACTIVE, "--hook-type", hook_type]
            + get_options(hook_type, config, tmp_path),
        )
        assert not result.exit_code, print_tb(result.exc_info[2])
        assert (
            f"{HOOK_ID}, {HOOK_NAME}, ['{DEFAULT_QUEUE_URL}'], {EVENTS}, []{expected}\n"
            == result.output
        )


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
class TestList:
    @pytest.mark.parametrize(
        "hook_type,config,expected",
        [(get_params("webhook", "expected_table")), (get_params("function", "expected_table"))],
    )
    def test_success(self, requests_mock, cli_runner, hook_type, config, expected):
        result = self._test_list(cli_runner, requests_mock, True, hook_type, config)

        assert result.output == expected

    @pytest.mark.parametrize(
        "hook_type,config,expected",
        [
            (get_params("webhook", "expected_table_without_secret")),
            (get_params("function", "expected_table")),
        ],
    )
    def test_non_admin_does_not_see_auth_token(
        self, requests_mock, cli_runner, hook_type, config, expected
    ):
        result = self._test_list(cli_runner, requests_mock, False, hook_type, config)

        assert result.output == expected

    @staticmethod
    def _test_list(cli_runner, requests_mock, include_secret: bool, hook_type, config):
        queue_url = f"{QUEUES_URL}/{QUEUE_ID}"
        requests_mock.get(
            f"{QUEUES_URL}",
            json={
                "pagination": {"total": 1, "next": None},
                "results": [{"url": queue_url, "id": QUEUE_ID}],
            },
        )

        hook_result = {
            "id": HOOK_ID,
            "name": HOOK_NAME,
            "queues": [queue_url],
            "active": ACTIVE,
            "events": EVENTS,
            "config": config,
            "sideload": ["queues"],
        }

        if include_secret is False and hook_type == "webhook":
            hook_result["config"].pop("secret")  # type: ignore

        requests_mock.get(
            HOOKS_URL, json={"pagination": {"total": 1, "next": None}, "results": [hook_result]}
        )
        result = cli_runner.invoke(list_command)
        assert not result.exit_code, format_tb(result.exc_info[2])
        return result


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
class TestChange:
    new_hook_name = "My patched new name"
    new_event = "new_event"

    @pytest.mark.parametrize(
        "hook_type,config,expected",
        [(get_params("webhook", "expected_result")), (get_params("function", "expected_result"))],
    )
    def test_success(self, requests_mock, cli_runner, tmp_path, hook_type, config, expected):

        requests_mock.get(f"{QUEUES_URL}/{QUEUE_ID}", json={"url": f"{QUEUES_URL}/{QUEUE_ID}"})

        requests_mock.patch(
            f"{HOOKS_URL}/{HOOK_ID}",
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "queues": [f"{QUEUES_URL}/{QUEUE_ID}"],
                    "name": self.new_hook_name,
                    "type": hook_type,
                    "events": [self.new_event],
                    "active": True,
                    "config": config,
                    "sideload": ["queues"],
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
                hook_type,
                "-s",
                "queues",
            ]
            + get_options(hook_type, config, tmp_path),
        )

        assert not result.exit_code, print_tb(result.exc_info[2])
        assert not result.output

    def test_noop(self, requests_mock, cli_runner):
        cli_runner.invoke(change_command, [HOOK_ID])
        assert not requests_mock.called


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
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
