# 05 Unfixed Debian findings in the runtime image

Status: resolved
Type: monitoring

A scan that includes unfixed issues still lists HIGH findings in Debian packages with no fix yet (`util-linux`/`bsdutils`/`mount`, `libacl1`, `ncurses`, `perl-base`, `libsystemd0` and others). They are in tools the
app does not run; exposure is limited by the non-root user, `cap_drop: ALL`, `no-new-privileges` and the read-only filesystem. `apt` is still present in the runtime image.

Options: accept and rebuild on a schedule (issue 02), or move to a distroless or otherwise smaller base.

## Comments
2026-10-11: the weekly rebuild-and-scan from CI (ci/issues/01) now exists, so the "accept and rebuild on a schedule" option is available. Still needs a human decision between that and a smaller base image, so left at `needs-triage`.

## Answer
2026-10-11: accepted. Rebuild and rescan weekly (ci/issues/01) and fail the build on any fixable HIGH or CRITICAL finding; do not change the base image.
- The findings are in tools the app does not run, have no upstream fix, and exposure is limited by the non-root user, `cap_drop: ALL`, `no-new-privileges` and the read-only filesystem.
- A distroless base is not a good fit: it likely lacks Python 3.14 (unverified), Alpine has no torch wheels, `CMD` needs a shell, and torch dominates the image anyway.
- Revisit if a requirement demands zero findings, a fixable finding the base cannot take appears, or a Python 3.14 distroless/Chainguard image is confirmed to exist.
