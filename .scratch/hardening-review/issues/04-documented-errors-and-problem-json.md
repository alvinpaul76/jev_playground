# 04 Document error responses and make validation errors problem+json

Status: resolved
Type: task

## Fix
- `api/problem.py`: `Problem` model and `problem_response()`; the v1 router documents 401, 413 and 500 and the ticket route documents 422 and 503, all as `application/problem+json`.
- FastAPI validation errors now use the same shape (`code: validation_error`) and list only `loc` and `msg`, never the submitted values (the default body echoes input).

## Verified by
OpenAPI test for all five statuses; tests that private text is not echoed and that malformed JSON is `validation_error`.
