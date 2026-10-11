# 03 fastapi-documentation: rewrite for non-developers

Status: resolved
Type: task

Reviewed the skill and rewrote it: audience and plain-language rules (`references/plain-language.md`), page templates with "done when" checks (`references/templates.md`), a size rule, and a reading test.
`scripts/check_docs.py` checks links and heading anchors, code fences, title and purpose line, secret-looking text, README links to every API page, and warns about jargon. The skill was linked into `~/.claude/skills`
(it had not been, so Claude Code could not find it).
