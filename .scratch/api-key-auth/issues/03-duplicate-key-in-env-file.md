# 03 API key rejected because .env defined the key twice

Status: resolved
Type: bug

## Symptom
A valid-looking key was rejected with 401 even though it was in `.env`.

## Cause
`.env` defined `JEV_CLIENT_API_KEYS` twice (a 47-character key and a 43-character key I had appended). The last definition wins, so the container only accepted the second.
Found by comparing SHA-256 fingerprints of the file lines and of the container's value, without printing any key.

## Fix
The owner removed one definition (the file now has exactly one). Lessons were added to `docs/deployment.md` (recreate the container after editing `.env`; define each variable once;
compare keys by fingerprint) and to the `fastapi-docker` and `fastapi-standards` skills.
