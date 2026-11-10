"""Authentication boundary.

Everything downstream depends on `Principal`, never on the identity provider.
Swapping Firebase for Auth0, Cognito, or a plain HS256 JWT means rewriting
`get_principal` and nothing else.
"""

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

bearer_scheme = HTTPBearer(auto_error=False)


class Principal(BaseModel):
    """The authenticated caller, normalized away from provider-specific claims."""

    user_id: str
    tenant_id: str | None = None
    email: str | None = None
    scopes: frozenset[str] = frozenset()
    claims: dict[str, Any] = {}

    def require_scope(self, scope: str) -> None:
        if scope not in self.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {scope}",
            )


def _verify_token(token: str) -> dict[str, Any]:
    """Replace with your provider's verification.

    Firebase:  firebase_admin.auth.verify_id_token(token, app=..., check_revoked=True)
    Auth0/OIDC: jwt.decode(token, key_from_jwks, audience=..., issuer=...)

    Whatever you use, verify the signature, issuer, audience, and expiry. A
    decode that skips verification is not authentication.
    """
    raise NotImplementedError("Wire this to your identity provider.")


async def get_principal(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Security(bearer_scheme)
    ],
) -> Principal:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = _verify_token(credentials.credentials)
    except NotImplementedError:
        raise
    except Exception as exc:
        # Never echo the provider's error text back to the caller; it can reveal
        # key ids and clock-skew details. Log it, return something opaque.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        ) from exc

    return Principal(
        user_id=claims["sub"],
        tenant_id=claims.get("tenant_id") or claims.get("firebase", {}).get("tenant"),
        email=claims.get("email"),
        scopes=frozenset(claims.get("scopes", [])),
        claims=claims,
    )


def require_scopes(*required: str):
    """Router-level guard: include_router(r, dependencies=[Depends(require_scopes("admin"))])"""

    async def _dependency(
        principal: Annotated[Principal, Depends(get_principal)]
    ) -> Principal:
        for scope in required:
            principal.require_scope(scope)
        return principal

    return _dependency
