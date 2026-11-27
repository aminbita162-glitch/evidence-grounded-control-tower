"""Application factory — FastAPI with injected ports and no module-level state (P10-T01).

The factory creates a FastAPI instance with versioned paths (``/api/v1``),
registered problem-detail handlers, and pagination conventions.  No
module-level state is held; the caller injects ports at construction time.
Later tasks (T02, T05) register the uniform capability route and health
endpoints.

Spec: Part 3 §3.17, §3.24; P10-T01.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from fastapi import FastAPI

from kernel.auth.sessions import SessionSigner
from kernel.auth.tokens import TokenService

if TYPE_CHECKING:
    from api.routes.capability import CapabilityInvocation

__all__ = [
    "API_VERSION",
    "API_PREFIX",
    "AppPorts",
    "create_app",
]

API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"


class AppPorts:
    """Injected ports for the application factory."""

    def __init__(
        self,
        *,
        tokens: TokenService | None = None,
        session_signer: SessionSigner | None = None,
        storage: object | None = None,
        capabilities: Mapping[str, CapabilityInvocation] | None = None,
    ) -> None:
        """Store injected ports.

        Args:
            tokens: Verifier for opaque API credentials.
            session_signer: Verifier for signed session cookies.
            storage: An optional storage port.
            capabilities: Optional capability handlers keyed by registration ID.
        """
        self.tokens = tokens
        self.session_signer = session_signer
        self.storage = storage
        self.capabilities = dict(capabilities or {})


def create_app(ports: AppPorts | None = None, *, production: bool = False) -> FastAPI:
    """Create a FastAPI application with injected ports.

    Args:
        ports: Injected ports. Tenant routes require a verified credential.
        production: Require a configured token verifier at startup.

    Returns:
        A configured :class:`FastAPI` instance.
    """
    if ports is None:
        ports = AppPorts()
    if production and ports.tokens is None:
        raise ValueError("AUTH_PROVIDER_REQUIRED")

    app = FastAPI(
        title="Customs & Transit Control Tower",
        version="0.0.0",
        docs_url=f"{API_PREFIX}/docs",
        openapi_url=f"{API_PREFIX}/openapi.json",
    )
    app.state.ports = ports

    # Register problem-detail handlers.
    from api.problems import register_problem_handlers

    register_problem_handlers(app)

    # Register routes (added by later tasks: T02 capability, T05 health).
    _register_routes(app, ports)

    return app


def _register_routes(app: FastAPI, ports: AppPorts) -> None:
    """Register all API routes on the app.

    Later tasks add idempotency middleware (T03) and health endpoints (T05).
    This hook lets each task extend the app without modifying the factory.
    """
    from api.routes.capability import register_capability_routes
    from api.routes.commands import register_command_routes

    register_capability_routes(app, ports.capabilities)
    register_command_routes(app)

    from api.health import register_health_routes

    register_health_routes(app)
