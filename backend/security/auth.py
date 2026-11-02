from __future__ import annotations

from typing import Any

import httpx
from authlib.jose import JsonWebKey, jwt
from fastapi import HTTPException, Security, status
from fastapi.security import OAuth2AuthorizationCodeBearer

from config.settings import settings


oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=settings.OIDC_AUTHORIZATION_URL or "/oauth/authorize",
    tokenUrl=settings.OIDC_TOKEN_URL or "/oauth/token",
    auto_error=False,
)


def _unauthorized(detail: str = "A valid access token is required.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _configured() -> None:
    missing = [
        name
        for name, value in (
            ("OIDC_ISSUER_URL", settings.OIDC_ISSUER_URL),
            ("OIDC_JWKS_URL", settings.OIDC_JWKS_URL),
            ("OIDC_AUDIENCE", settings.OIDC_AUDIENCE),
        )
        if not value
    ]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"OIDC authentication is not configured: {', '.join(missing)}",
        )


def _roles(claims: dict[str, Any]) -> list[str]:
    value: Any = claims
    for part in settings.OIDC_ROLE_CLAIM.split("."):
        if not isinstance(value, dict):
            return []
        value = value.get(part)
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(role) for role in value]
    return []


def _fetch_jwks() -> dict[str, Any]:
    try:
        response = httpx.get(settings.OIDC_JWKS_URL, timeout=5.0)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve OIDC signing keys.",
        ) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("keys"), list):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC signing-key response is invalid.",
        )
    return payload


def _decode_token(token: str) -> dict[str, Any]:
    _configured()
    try:
        key_set = JsonWebKey.import_key_set(_fetch_jwks())

        # Authlib's claim validators read their requirements from
        # claims_options; validate_iss()/validate_aud() do not accept values
        # as positional arguments in the installed Authlib release.
        claims = jwt.decode(
            token,
            key_set,
            claims_options={
                "iss": {"essential": True, "value": settings.OIDC_ISSUER_URL},
                "aud": {"essential": True, "values": [settings.OIDC_AUDIENCE]},
                "exp": {"essential": True},
            },
        )
        claims.validate()

    except Exception as exc:
        raise _unauthorized("The access token is invalid, expired, or poorly scoped.") from exc

    return dict(claims)



def get_current_user(token: str | None = Security(oauth2_scheme)) -> dict[str, Any]:
    if not token:
        raise _unauthorized()
    return _decode_token(token)


def require_reviewer(user: dict[str, Any] = Security(get_current_user)) -> dict[str, Any]:
    if settings.OIDC_REVIEWER_ROLE not in _roles(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer role is required for this operation.",
        )
    return user
