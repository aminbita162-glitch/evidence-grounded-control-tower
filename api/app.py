"""Application factory — FastAPI with injected ports and no module-level state (P10-T01).

The factory creates a FastAPI instance with versioned paths (``/api/v1``),
registered problem-detail handlers, and pagination conventions.  No
module-level state is held; the caller injects ports at construction time.
Later tasks (T02, T05) register the uniform capability route and health
endpoints.

Spec: Part 3 §3.17, §3.24; P10-T01.
"""

from __future__ import annotations

from fastapi import FastAPI

__all__ = [
    "API_VERSION",
    "API_PREFIX",
    "AppPorts",
    "create_app",
]

API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"


class AppPorts:
    """Injected ports for the application factory.

    A test principal provider is used in this phase; the production
    configuration check refuses it (P10 exit condition 9).
    """

    def __init__(
        self,
        *,
        use_test_principal: bool = True,
        storage: object | None = None,
    ) -> None:
        """Store injected ports.

        Args:
            use_test_principal: Whether the test principal is active
                (excluded from production by a startup check).
            storage: An optional storage port.
        """
        self.use_test_principal = use_test_principal
        self.storage = storage


def create_app(ports: AppPorts | None = None) -> FastAPI:
    """Create a FastAPI application with injected ports.

    Args:
        ports: Injected ports (defaults to a test-principal configuration).

    Returns:
        A configured :class:`FastAPI` instance.
    """
    if ports is None:
        ports = AppPorts()

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

    Later tasks add the uniform capability route (T02), idempotency
    middleware (T03), and health endpoints (T05).  This hook lets each
    task extend the app without modifying the factory.
    """
    # T02 will add the uniform capability route.
    # T05 will add health endpoints.
    # For T01 the app exposes only the OpenAPI document and problem handlers.
