import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from jev_playground.api.problem import PROBLEM_JSON


class BodySizeLimitMiddleware:
    """Rejects bodies over `max_bytes` with 413, before they are parsed or buffered.

    Checks Content-Length up front. For chunked uploads it counts streamed bytes, stops
    feeding the app once the limit is passed, and swaps whatever the app answers for a 413
    (raising from `receive` would be swallowed by the framework's body parsing).
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = dict(scope["headers"]).get(b"content-length")
        if (
            declared is not None
            and declared.isdigit()
            and int(declared) > self.max_bytes
        ):
            await self._reject(scope, send)
            return

        received = 0
        too_large = False
        replied = False

        async def limited_receive() -> Message:
            nonlocal received, too_large
            if too_large:
                return {"type": "http.request", "body": b"", "more_body": False}
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    too_large = True
                    return {"type": "http.request", "body": b"", "more_body": False}
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal replied
            if not too_large:
                await send(message)
            elif not replied:
                replied = True
                await self._reject(scope, send)

        await self.app(scope, limited_receive, guarded_send)

    async def _reject(self, scope: Scope, send: Send) -> None:
        body = json.dumps(
            {
                "type": "about:blank",
                "title": "Payload too large",
                "status": 413,
                "detail": f"The request body must be at most {self.max_bytes} bytes.",
                "code": "payload_too_large",
                "request_id": scope.get("state", {}).get("request_id"),
            }
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", PROBLEM_JSON.encode()),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
