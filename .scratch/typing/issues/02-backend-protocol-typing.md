# 02 Type the backend with a Protocol

Status: resolved
Type: task

`build_backend` has no return type, and `JevBackend` and OpenJev backends share only a duck-typed `decide()` / `load()` surface. Add a small `Backend` `Protocol` in the application or infrastructure layer
and use it in `build_backend`, the classifier and `lifespan.py`.

## Result
Commit `c0a7892`. `infrastructure/backend.py` has two Protocols: `Decider` (just `decide()`, used by the classifier, so test fakes need only that) and `Backend(Decider)` adding `name` and `load()` (used by `build_backend` and `lifespan`). Slightly narrower than the ticket's single Protocol on purpose. `build_backend` now returns `Backend`; OpenJev's untyped `get_backend` result is `cast`.
