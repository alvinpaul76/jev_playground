from typing import Protocol

from openjev import SystemOneRequest, SystemOneResponse


class Decider(Protocol):
    """All the classifier needs: answer one request."""

    def decide(self, request: SystemOneRequest) -> SystemOneResponse: ...


class Backend(Decider, Protocol):
    """A model backend the app can load and name.

    OpenJev's backends and `JevBackend` both satisfy it without inheriting from it.
    """

    name: str

    def load(self) -> None: ...
