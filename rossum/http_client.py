from typing import Optional, Dict, List, Iterable, Union

import urllib3
import requests
from requests import Response
from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_fixed,
    retry_if_exception_type,
)


class HTTPClient:
    def __init__(
        self,
        context: Optional[dict],
        url: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        use_api_version: bool = True,
        auth_using_token: bool = True,
        max_token_lifetime: Optional[int] = None,
        retry_logic_rules: Optional[Dict] = None,
    ):
        """The APIClient for communication with Rossum API.
        :param context Used for switching profile. Send None for usual requests done for your default profile.
        :param url Rossum API URL. Leave None for communication with the currently used publicly available Rossum API.
        :param user Your username.
        :param password Your password.
        :param use_api_version Leave True if you want to use the latest API version. If set to false,
        specify the Rossum API URL including its version in the url parameter explicitly.
        :param auth_using_token To avoid using login request for each call, leave set to True.
        :param max_token_lifetime Set custom max token lifetime in seconds. Default is the maximum lifetime: 583200s
        or until the Rossum client logs out. Logging out is made when CLI is exited or if RossumClient() is used
        with a with statement.
        :param retry_logic_rules Pass logic rules for built-in retry mechanism that is called when it is currently
        not possible to communicate with Rossum API. The default shape of the dictionary is:
        {"attempts": 3, "wait_s": 5}. "attempts" key states the number of retry attempts. "wait_s" is time in seconds
        the APIClient will wait before retrying again.
        """
        self._url = url
        self._user = user
        self._password = password
        self._use_api_version = use_api_version
        self._auth_using_token = auth_using_token
        self._max_token_lifetime = max_token_lifetime

        self.token: Optional[str] = None
        self.timeout: Optional[float] = None

        self._retry_logic_rules = self.get_retry_logic(retry_logic_rules)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.logout()

    @staticmethod
    def get_retry_logic(retry_logic_rules: Optional[Dict]):
        retry_logic_rules = retry_logic_rules or {}
        attempts_no = retry_logic_rules.get("attempts", 3)
        wait_s = retry_logic_rules.get("wait_s", 5)
        retry_logic = {
            "reraise": True,
            "stop": (stop_after_attempt(attempts_no) | stop_after_delay(55)),
            "wait": wait_fixed(wait_s),
            "retry": (
                retry_if_exception_type(requests.exceptions.ProxyError)
                | retry_if_exception_type(requests.exceptions.ConnectionError)
                | retry_if_exception_type(urllib3.exceptions.NewConnectionError)
                | retry_if_exception_type(urllib3.exceptions.ConnectTimeoutError)
            ),
        }
        return retry_logic

    def _login_to_api(self, login_data: Dict) -> Response:
        return requests.post(
            f"{self.url}/auth/login", json=login_data, timeout=self.timeout, headers=HEADERS
        )

    def get_token(self) -> str:
        # self.post cannot be used as it is dependent on self.get_token().
        login_data: Dict[str, Union[str, int]] = {"username": self.user, "password": self.password}
        if self._max_token_lifetime:
            login_data["max_token_lifetime_s"] = self._max_token_lifetime
        retry_request = retry(**self._retry_logic_rules)(self._login_to_api)
        response = retry_request(login_data)
        if response.status_code == 401:
            raise RossumException("Login failed with the provided credentials.", response=response)
        elif not response.ok:
            raise RossumException(
                f"Invalid response [{response.url}]: {response.text}", response=response
            )

        return response.json()["key"]

    def post(
        self,
        path: Union[str, APIObject],
        data: dict = None,
        expected_status_code: int = 201,
        files: Optional[RequestsFiles] = None,
    ) -> Response:
        return self._request_url(
            "post",
            f"{self.url}/{path}",
            json=data,
            expected_status_code=expected_status_code,
            files=files,
        )

    def patch(self, path: Union[str, APIObject], data: dict) -> Response:
        return self._request_url("patch", f"{self.url}/{path}", json=data)

    def get(self, path: Union[str, APIObject], query: dict = None) -> Response:
        return self._request_url("get", f"{self.url}/{path}", query)

    def get_url(self, url: str, query: dict = None) -> Response:
        return self._request_url("get", url, query)

    def delete_url(self, url: str) -> Response:
        return self._request_url("delete", url, expected_status_code=204)

    def _do_request(self, method: str, url: str, query: dict = None, **kwargs) -> Response:
        auth = self._authentication
        headers = {**HEADERS, **auth.pop("headers", {}), **kwargs.pop("headers", {})}
        response = requests.request(
            method,
            url,
            params=_encode_booleans(query),
            headers=headers,
            timeout=self.timeout,
            **auth,
            **kwargs,
        )
        return response

    def _request_url(
        self, method: str, url: str, query: dict = None, expected_status_code: int = 200, **kwargs
    ) -> Response:
        retry_request = retry(**self._retry_logic_rules)(self._do_request)
        response = retry_request(method, url, query, **kwargs)
        if response.status_code != expected_status_code:
            raise RossumException(
                f"Invalid response [{response.url}]: {response.text}", response=response
            )
        return response

    def delete(
        self, to_delete: Dict[str, str], verbose: int = 0, item: str = "annotation"
    ) -> None:
        for id_, url in to_delete.items():
            try:
                self.delete_url(url)
            except RossumException as exc:
                click.echo(f'Deleting {item} {id_} caused "{exc}".')
            except Exception as exc:
                click.echo(f'Deleting {item} {id_} caused an unexpected exception: "{exc}".')
                raise RossumException(str(exc))
            else:
                if verbose > 1:
                    click.echo(f"Deleted {item} {id_}.")

    def get_paginated(
        self,
        path: Union[str, APIObject],
        query: Optional[Dict[str, Any]] = None,
        *,
        key: str = "results",
        sideloads: Optional[Iterable[Union[Sideload, str]]] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        if query is None:
            query = {}

        sideloads = to_sideloads(sideloads)

        if sideloads:
            if "sideload" in query:
                raise RossumException(
                    "sideloading cannot be specified both in query and sideloads"
                )
            query = query.copy()
            for sideload in sideloads:
                sideload.setup_query(query)

        response = self.get(path, query)
        response_dict = response.json()

        res = response_dict
        next_page = response_dict["pagination"]["next"]

        while next_page:
            response = self.get_url(next_page)
            response_dict = response.json()

            for k, v in response_dict.items():
                if k != "pagination":
                    res.setdefault(k, []).extend(v)
            next_page = response_dict["pagination"]["next"]

        if sideloads:
            self._resolve_sideloads(res, sideloads)

        return res[key], response_dict["pagination"]["total"]

    def _sideload(
        self, objects: List[dict], sideloads: Optional[Iterable[APIObject]] = None
    ) -> List[dict]:
        response = {"results": objects}
        for sideload in sideloads or []:
            sideloaded, _ = self.get_paginated(sideload)
            response[sideload.plural] = sideloaded
        if sideloads:
            self._resolve_sideloads(response, to_sideloads(sideloads))
        return response["results"]

    def _resolve_sideloads(self, response: dict, sideloads: Iterable[Sideload]) -> None:
        """
        Resolve the dependency injections of sideloaded objects to corresponding
        results objects in the `response`.
        :param response Response object as returned from Rossum app for any
        paginated GET-like request.
        :param sideloads Optional list of object types to resolve dependency
        injection for.
        """
        for sideload in sideloads or []:
            sideloaded_dicts = sideload.get_mapping(response.get(sideload.plural, []))

            def inject_sideloaded(obj: dict) -> dict:
                try:
                    url = obj[sideload.singular]
                except KeyError:
                    obj[sideload.plural] = [
                        sideloaded_dicts[url]
                        for url in obj[sideload.plural]
                        if url in sideloaded_dicts
                    ]
                else:
                    obj[sideload.singular] = sideloaded_dicts.get(url, {})
                return obj

            for obj in response["results"]:
                inject_sideloaded(obj)

    @property
    def _authentication(self) -> dict:
        if self._auth_using_token:
            if self.token is None:
                self.token = self.get_token()
            return {"headers": {"Authorization": "Token " + self.token}}
        else:
            return {"auth": (self.user, self.password)}

    def logout(self) -> None:
        if self._auth_using_token:
            self.post("auth/logout", {}, expected_status_code=200)
