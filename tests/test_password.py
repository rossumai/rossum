from functools import partial
from traceback import print_tb
import pytest

from rossum.password import change_command, reset_command
from tests.conftest import CHANGE_PASSWORD_URL, match_uploaded_json, RESET_PASSWORD_URL


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
class TestChangePassword:
    def test_success_change_password(self, requests_mock, cli_runner):
        new_password = "new_password"

        requests_mock.post(
            CHANGE_PASSWORD_URL,
            additional_matcher=partial(
                match_uploaded_json,
                {
                    "new_password1": new_password,
                    "new_password2": new_password,
                    "old_password": "secret",
                },
            ),
            status_code=200,
            json={"detail": "New password has been saved."},
        )

        result = cli_runner.invoke(change_command, ["--password", new_password])

        assert not result.exit_code, print_tb(result.exc_info[2])
        assert (
            result.output == "New password has been saved.\n"
            'Run "rossum configure" to update existing credentials.\n'
        )


@pytest.mark.usefixtures("mock_login_request", "rossum_credentials")
class TestResetPassword:
    def test_success_reset_password(self, requests_mock, cli_runner):
        email = "test-email@rossum.ai"
        requests_mock.post(
            RESET_PASSWORD_URL,
            additional_matcher=partial(match_uploaded_json, {"email": email}),
            status_code=200,
            json={"detail": "Password reset e-mail has been sent."},
        )

        result = cli_runner.invoke(reset_command, [email])

        assert not result.exit_code, print_tb(result.exc_info[2])
        assert result.output == "Password reset e-mail has been sent.\n"
