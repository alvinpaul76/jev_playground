# 02 Review against the documentation guidelines

Status: resolved
Type: task

## Findings and fixes
- Facts were restated (size limit in 4 places, batch cap in 6, key length in 3, `.env` notes twice, start-up refusal in 6). Each now lives on one page and the others link to it.
- Troubleshooting lacked the exact `code` strings; it now lists them with one real 401 body. The API page has one real 422 body; architecture has the health answers.
- Only the README linked the glossary; every page now has a "New to a word?" line. Glossary gained Image, Log, Proxy, Volume.
- Deployment gained a "Which settings matter for production?" table.
- The skill's own template conflicted with "facts live once" (architecture error table); the skill was fixed. The checker now also validates heading anchors.
