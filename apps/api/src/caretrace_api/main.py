from collections.abc import Callable
from importlib.metadata import version
from typing import Literal

from fastapi import APIRouter, FastAPI, Response
from pydantic import BaseModel

from caretrace_api.settings import Settings


class Liveness(BaseModel):
    status: Literal["alive"] = "alive"


class Readiness(BaseModel):
    status: Literal["ready", "unavailable"]


class BuildInformation(BaseModel):
    service: Literal["caretrace-api"] = "caretrace-api"
    version: str


def create_app(
    settings: Settings | None = None,
    *,
    readiness_check: Callable[[], bool] | None = None,
) -> FastAPI:
    settings = settings if settings is not None else Settings()
    local_docs = settings.environment != "production"
    app = FastAPI(
        title="CareTrace API",
        version=version("caretrace-api"),
        description=(
            "Discovery-stage inspection-readiness review aids. CareTrace does not provide legal "
            "advice or certify compliance. Use only public, synthetic, or explicitly authorized "
            "de-identified materials. Qualified human review is required."
        ),
        docs_url="/docs" if local_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if local_docs else None,
    )

    @app.get("/livez", summary="Process liveness")
    def liveness() -> Liveness:
        return Liveness()

    @app.get(
        "/readyz", responses={503: {"model": Readiness}}, summary="Service readiness"
    )
    def readiness(response: Response) -> Readiness:
        if readiness_check is not None and not readiness_check():
            response.status_code = 503
            return Readiness(status="unavailable")
        return Readiness(status="ready")

    router = APIRouter(prefix="/api/v1")

    @router.get("/build")
    def build_information() -> BuildInformation:
        return BuildInformation(version=app.version)

    app.include_router(router)
    return app
