# 05 Request body size limit

Status: resolved
Type: task

## Fix
`api/limits.py`: pure ASGI `BodySizeLimitMiddleware`, setting `JEV_MAX_REQUEST_BYTES` (default 2,097,152; minimum 1,024). It checks `Content-Length` up front and counts streamed bytes for chunked
uploads. It sits inside `RequestIdMiddleware`, so the 413 problem+json (`payload_too_large`) carries the request id.

## Lesson
Raising from `receive` was swallowed by FastAPI's body parsing and produced a 400. The middleware now stops feeding the app once over the limit and swaps the app's response for the 413. A chunked-body test caught this.

## Verified by
Tests for declared length, chunked bodies, bodies under the limit, and rejection before auth work. Live check: a 3 MB body returned 413.
