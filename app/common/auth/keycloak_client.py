from __future__ import annotations

import asyncio
import json
from contextlib import suppress
from dataclasses import dataclass, field
from time import monotonic
from types import MappingProxyType
from typing import Any, Mapping
from urllib.parse import quote

import aiohttp


class KeycloakAuthError(Exception):
    """Base error for service-to-service Keycloak authentication failures."""


class TokenRequestError(KeycloakAuthError):
    """Raised when the token endpoint request cannot be completed."""


class TokenResponseError(KeycloakAuthError):
    """Raised when Keycloak returns an invalid or unsuccessful token response."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class TokenClientClosedError(KeycloakAuthError):
    """Raised when a closed token client is used."""


@dataclass(frozen=True)
class KeycloakTokenConfig:
    auth_server_url: str
    realm: str
    client_id: str
    client_secret: str = field(repr=False)
    scope: str | None = None
    extra_token_params: Mapping[str, str] = field(default_factory=dict)
    request_timeout_seconds: float = 10.0
    refresh_before_expiry_seconds: float = 30.0
    background_refresh: bool = False

    def __post_init__(self) -> None:
        auth_server_url = self.auth_server_url.strip().rstrip("/")
        realm = self.realm.strip().strip("/")
        client_id = self.client_id.strip()

        if not auth_server_url:
            raise ValueError("auth_server_url must not be empty")
        if not realm:
            raise ValueError("realm must not be empty")
        if not client_id:
            raise ValueError("client_id must not be empty")
        if not self.client_secret:
            raise ValueError("client_secret must not be empty")
        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be positive")
        if self.refresh_before_expiry_seconds < 0:
            raise ValueError("refresh_before_expiry_seconds must not be negative")

        object.__setattr__(self, "auth_server_url", auth_server_url)
        object.__setattr__(self, "realm", realm)
        object.__setattr__(self, "client_id", client_id)
        object.__setattr__(
            self,
            "extra_token_params",
            MappingProxyType(dict(self.extra_token_params)),
        )

    @property
    def token_url(self) -> str:
        encoded_realm = quote(self.realm, safe="")
        return (
            f"{self.auth_server_url}/realms/"
            f"{encoded_realm}/protocol/openid-connect/token"
        )


@dataclass(frozen=True)
class AccessToken:
    access_token: str = field(repr=False)
    token_type: str
    expires_in: float
    obtained_at: float
    expires_at: float
    scope: str | None = None

    @property
    def authorization_header(self) -> str:
        return f"{self.token_type} {self.access_token}"

    def refresh_margin(self, refresh_before_expiry_seconds: float) -> float:
        return min(refresh_before_expiry_seconds, self.expires_in * 0.2)

    def needs_refresh(self, now: float, refresh_before_expiry_seconds: float) -> bool:
        return now >= self.expires_at - self.refresh_margin(refresh_before_expiry_seconds)

    def is_expired(self, now: float) -> bool:
        return now >= self.expires_at


class KeycloakTokenClient:
    _BACKGROUND_RETRY_DELAYS_SECONDS = (1.0, 2.0, 5.0, 10.0, 30.0)

    def __init__(
        self,
        token_config: KeycloakTokenConfig,
        *,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._config = token_config
        self._session = session
        self._owns_session = session is None
        self._token: AccessToken | None = None
        self._refresh_lock = asyncio.Lock()
        self._background_task: asyncio.Task | None = None
        self._closed = False

    async def __aenter__(self) -> KeycloakTokenClient:
        await self._ensure_session()
        if self._config.background_refresh:
            await self.start_background_refresh()
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        await self.aclose()

    async def get_access_token(self, force_refresh: bool = False) -> str:
        token = await self._get_token(force_refresh=force_refresh)
        return token.access_token

    async def get_authorization_header(self, force_refresh: bool = False) -> str:
        token = await self._get_token(force_refresh=force_refresh)
        return token.authorization_header

    async def get_authorization_headers(
        self,
        force_refresh: bool = False,
    ) -> dict[str, str]:
        return {
            "Authorization": await self.get_authorization_header(
                force_refresh=force_refresh,
            )
        }

    async def refresh(self) -> AccessToken:
        self._ensure_open()
        async with self._refresh_lock:
            return await self._request_token()

    async def start_background_refresh(self) -> None:
        self._ensure_open()
        await self._ensure_session()
        if self._background_task is not None and not self._background_task.done():
            return

        self._background_task = asyncio.create_task(
            self._run_background_refresh(),
            name="keycloak-token-refresh",
        )

    async def stop_background_refresh(self) -> None:
        task = self._background_task
        self._background_task = None
        if task is None or task.done():
            return

        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    async def aclose(self) -> None:
        if self._closed:
            return

        await self.stop_background_refresh()
        if (
            self._owns_session
            and self._session is not None
            and not self._session.closed
        ):
            await self._session.close()
        self._closed = True

    async def _get_token(self, force_refresh: bool) -> AccessToken:
        self._ensure_open()
        now = monotonic()
        token = self._token
        if (
            not force_refresh
            and token is not None
            and not token.needs_refresh(now, self._config.refresh_before_expiry_seconds)
        ):
            return token

        async with self._refresh_lock:
            now = monotonic()
            token = self._token
            if (
                not force_refresh
                and token is not None
                and not token.needs_refresh(now, self._config.refresh_before_expiry_seconds)
            ):
                return token

            try:
                return await self._request_token()
            except KeycloakAuthError:
                fallback = self._token
                if (
                    not force_refresh
                    and fallback is not None
                    and not fallback.is_expired(monotonic())
                ):
                    return fallback
                raise

    async def _request_token(self) -> AccessToken:
        session = await self._ensure_session()
        timeout = aiohttp.ClientTimeout(total=self._config.request_timeout_seconds)
        try:
            async with session.post(
                self._config.token_url,
                data=self._build_token_request_data(),
                headers={
                    "Accept": "application/json",
                    "Authorization": aiohttp.BasicAuth(
                        self._config.client_id,
                        self._config.client_secret,
                    ).encode(),
                },
                timeout=timeout,
            ) as response:
                response_text = await response.text()
                if response.status >= 400:
                    raise TokenResponseError(
                        self._format_error_response(response.status, response_text),
                        status_code=response.status,
                    )
                payload = self._decode_token_response(response_text, response.status)
        except TokenResponseError:
            raise
        except (TimeoutError, aiohttp.ClientError) as exc:
            raise TokenRequestError(f"Failed to request Keycloak token: {exc}") from exc

        token = self._build_access_token(payload)
        self._token = token
        return token

    def _build_token_request_data(self) -> dict[str, str]:
        data = dict(self._config.extra_token_params)
        data["grant_type"] = "client_credentials"
        if self._config.scope:
            data["scope"] = self._config.scope
        return data

    @staticmethod
    def _decode_token_response(response_text: str, status_code: int) -> dict[str, Any]:
        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise TokenResponseError(
                "Keycloak token response is not valid JSON",
                status_code=status_code,
            ) from exc
        if not isinstance(payload, dict):
            raise TokenResponseError(
                "Keycloak token response must be a JSON object",
                status_code=status_code,
            )
        return payload

    @staticmethod
    def _build_access_token(payload: dict[str, Any]) -> AccessToken:
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise TokenResponseError(
                "Keycloak token response does not contain access_token"
            )

        expires_in = payload.get("expires_in")
        if not isinstance(expires_in, (int, float)) or expires_in <= 0:
            raise TokenResponseError(
                "Keycloak token response does not contain valid expires_in"
            )

        token_type = payload.get("token_type", "Bearer")
        if not isinstance(token_type, str) or not token_type:
            token_type = "Bearer"

        scope = payload.get("scope")
        if not isinstance(scope, str):
            scope = None

        obtained_at = monotonic()
        return AccessToken(
            access_token=access_token,
            token_type=token_type,
            expires_in=float(expires_in),
            obtained_at=obtained_at,
            expires_at=obtained_at + float(expires_in),
            scope=scope,
        )

    async def _run_background_refresh(self) -> None:
        retry_index = 0
        while True:
            delay = self._seconds_until_refresh()
            if delay > 0:
                await asyncio.sleep(delay)
            try:
                await self.refresh()
                retry_index = 0
            except asyncio.CancelledError:
                raise
            except KeycloakAuthError:
                retry_delay = self._BACKGROUND_RETRY_DELAYS_SECONDS[
                    min(retry_index, len(self._BACKGROUND_RETRY_DELAYS_SECONDS) - 1)
                ]
                retry_index += 1
                await asyncio.sleep(retry_delay)

    def _seconds_until_refresh(self) -> float:
        token = self._token
        if token is None:
            return 0.0
        now = monotonic()
        return max(
            0.0,
            token.expires_at
            - token.refresh_margin(self._config.refresh_before_expiry_seconds)
            - now,
        )

    async def _ensure_session(self) -> aiohttp.ClientSession:
        self._ensure_open()
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(
                    total=self._config.request_timeout_seconds,
                ),
            )
        if self._session.closed:
            raise TokenClientClosedError("The aiohttp session is closed")
        return self._session

    def _ensure_open(self) -> None:
        if self._closed:
            raise TokenClientClosedError("The Keycloak token client is closed")

    @staticmethod
    def _format_error_response(status_code: int, response_text: str) -> str:
        text = response_text.strip()
        if len(text) > 500:
            text = f"{text[:500]}..."
        if not text:
            text = "<empty response body>"
        return f"Keycloak token endpoint returned HTTP {status_code}: {text}"
