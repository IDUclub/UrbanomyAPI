from fastapi import Depends, HTTPException, Request

from app.common.auth.keycloak_client import (
    KeycloakAuthError,
    KeycloakTokenClient,
    KeycloakTokenConfig,
)
from app.dependencies import config


def _get_optional_config(name: str) -> str | None:
    try:
        return config.get(name)
    except ValueError:
        return None


def build_keycloak_config() -> KeycloakTokenConfig:
    return KeycloakTokenConfig(
        auth_server_url=config.get("KEYCLOAK_URL"),
        realm=config.get("KEYCLOAK_REALM"),
        client_id=config.get("KEYCLOAK_CLIENT_ID"),
        client_secret=config.get("KEYCLOAK_CLIENT_SECRET"),
        scope=_get_optional_config("KEYCLOAK_SCOPE"),
        background_refresh=True,
    )


def get_keycloak_auth(request: Request) -> KeycloakTokenClient:
    auth = getattr(request.app.state, "keycloak_auth", None)
    if auth is None:
        raise HTTPException(status_code=503, detail="Keycloak auth client is not ready")
    return auth


async def get_service_access_token(
    auth: KeycloakTokenClient = Depends(get_keycloak_auth),
) -> str:
    try:
        return await auth.get_access_token()
    except KeycloakAuthError as exc:
        raise HTTPException(status_code=503, detail="Auth provider unavailable") from exc
