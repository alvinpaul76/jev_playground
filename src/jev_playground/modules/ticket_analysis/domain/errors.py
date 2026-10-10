class DomainError(Exception):
    """Base for business errors. Carries a stable code; knows nothing about HTTP."""

    code = "domain_error"
    title = "Domain error"

    def __init__(self, public_message: str) -> None:
        super().__init__(public_message)
        self.public_message = public_message


class InvalidTicket(DomainError):
    code = "invalid_ticket"
    title = "Invalid ticket"


class InvalidBatch(DomainError):
    code = "invalid_batch"
    title = "Invalid batch"


class ClassifierUnavailable(DomainError):
    code = "classifier_unavailable"
    title = "Classifier unavailable"

    def __init__(
        self, public_message: str = "Ticket classification is temporarily unavailable."
    ) -> None:
        super().__init__(public_message)
