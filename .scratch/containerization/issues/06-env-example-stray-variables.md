# 06 Unrelated variables in .env.example

Status: resolved
Type: cleanup

`.env.example` contains `SHARED_DOCKER_NETWORK` and `DEFAULT_STORAGE_FOLDER=/storage/stirling-pdf`, which no code or compose file in this project uses. They look left over from another project.
Question for the owner: remove them, or are they used by something outside this repo?

## Answer
2026-10-11: kept. The owner uses `SHARED_DOCKER_NETWORK` (shared network with Cloudflare, to expose the API) and `DEFAULT_STORAGE_FOLDER` (local storage folder) in their own deployment. Nothing in this repo reads them. Commit `9597386` adds a comment in `.env.example` saying so.
