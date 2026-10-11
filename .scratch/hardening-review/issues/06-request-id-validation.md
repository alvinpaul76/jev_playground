# 06 Validate client X-Request-ID

Status: resolved
Type: task

## Fix
A client `X-Request-ID` is used only if it matches `[A-Za-z0-9_-]{1,64}`; otherwise a new UUID hex is generated. The id lands in logs and a response header, so unchecked input allowed log injection.

## Verified by
Tests for a safe id (echoed) and unsafe ids (too long, spaces, `;`, tab) which are replaced by a 32-character id.
