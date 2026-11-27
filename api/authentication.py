"""Verify credentials and enforce permissions on tenant routes."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.app import AppPorts
from kernel.auth.roles import Principal, RoleError, enforce_role_boundary
from kernel.auth.sessions import COOKIE_NAME, SessionError, verify_session_cookie
from kernel.auth.tokens import TokenError

_bearer = HTTPBearer(auto_error=False)


async def tenant_principal(
    request: Request,
    bearer: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    """Derive the tenant and role from a verified credential."""
    ports: AppPorts = request.app.state.ports
    now = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    session = request.cookies.get(COOKIE_NAME)
    try:
        if bearer is not None and ports.tokens is not None:
            principal = await ports.tokens.verify_token(bearer.credentials, current_time=now)
        elif "authorization" not in request.headers and session and ports.session_signer:
            principal = verify_session_cookie(
                session, signer=ports.session_signer, current_time=now
            )
        else:
            raise TokenError("credential required")
    except TokenError, SessionError, RoleError:
        raise HTTPException(
            status_code=401, detail="AUTH_REQUIRED", headers={"WWW-Authenticate": "Bearer"}
        ) from None
    try:
        enforce_role_boundary(principal, request.url.path, is_tenant_scoped=True)
    except RoleError:
        raise HTTPException(status_code=403, detail="ROLE_DENIED") from None
    return principal


TenantPrincipal = Annotated[Principal, Depends(tenant_principal)]


def operator_principal(principal: TenantPrincipal) -> Principal:
    """Require permission to run an operator command."""
    if not principal.can_operate():
        raise HTTPException(status_code=403, detail="ROLE_DENIED")
    return principal


def reviewer_principal(principal: TenantPrincipal) -> Principal:
    """Require the reviewer role for approval."""
    if not principal.can_approve():
        raise HTTPException(status_code=403, detail="ROLE_DENIED")
    return principal
