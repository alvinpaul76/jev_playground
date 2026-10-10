from typing import cast

from openjev.backends import get_backend

from jev_playground.config import Settings
from jev_playground.modules.ticket_analysis.infrastructure.backend import Backend
from jev_playground.modules.ticket_analysis.infrastructure.jev_backend import JevBackend


def build_backend(settings: Settings) -> Backend:
    if settings.backend == "jev":
        if settings.api_key is None or not settings.api_key.get_secret_value():
            raise RuntimeError(
                "JEV_BACKEND=jev requires JEV_API_KEY (or TYPESAFE_API_KEY) to be set."
            )
        return JevBackend(
            api_key=settings.api_key.get_secret_value(),
            base_url=settings.base_url,
            model=settings.jev_model,
            timeout_s=settings.jev_timeout_s,
        )
    if settings.backend == "hf":
        return cast(Backend, get_backend("hf", model_id=settings.model_id))
    return cast(Backend, get_backend("mock"))
