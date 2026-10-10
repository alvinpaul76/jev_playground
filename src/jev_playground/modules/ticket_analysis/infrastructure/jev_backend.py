import time
from typing import Any

import httpx
from openjev import SystemOneRequest, SystemOneResponse
from openjev.core.primitives import Score


class JevBackend:
    """Calls the hosted Jev (TypeSafe) `POST /v1/systemone` API.

    Implements the same `decide()` / `load()` surface as OpenJev backends, so the
    classifier does not care which one it is given.
    """

    name = "jev"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.typesafe.ai",
        model: str = "jev-latest",
        timeout_s: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._model = model
        self._client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout_s,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
        )

    def load(self) -> None:
        return None

    def decide(self, request: SystemOneRequest) -> SystemOneResponse:
        t0 = time.perf_counter()
        http_response = self._client.post("/v1/systemone", json=self._body(request))
        http_response.raise_for_status()
        payload: dict[str, Any] = http_response.json()
        # The API may report unknown token counts as null; OpenJev's Usage wants ints.
        usage = payload.get("usage") or {}
        payload["usage"] = {k: v for k, v in usage.items() if v is not None}
        response = SystemOneResponse.model_validate(payload)
        if response.latency_ms is None:
            response.latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return response

    def _body(self, request: SystemOneRequest) -> dict[str, Any]:
        questions: dict[str, Any] = {}
        for name, question in request.questions.items():
            wire = question.model_dump(exclude_none=True)
            if isinstance(question, Score):
                wire.pop("legend", None)
                wire["criteria"] = [
                    question.legend[str(level)] for level in question.levels()
                ]
            questions[name] = wire
        return {"state": request.state, "model": self._model, "questions": questions}
