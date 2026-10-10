from collections.abc import Sequence

from jev_playground.modules.ticket_analysis.domain.entities import Ticket
from jev_playground.modules.ticket_analysis.domain.errors import InvalidBatch

MAX_BATCH_SIZE = 20


def ensure_valid_batch(tickets: Sequence[Ticket]) -> None:
    """A batch is 1..MAX_BATCH_SIZE tickets with unique ids."""
    if not tickets:
        raise InvalidBatch("At least one ticket is required.")
    if len(tickets) > MAX_BATCH_SIZE:
        raise InvalidBatch(f"At most {MAX_BATCH_SIZE} tickets per request.")
    seen: set[str] = set()
    duplicates: list[str] = []
    for ticket in tickets:
        if ticket.id in seen and ticket.id not in duplicates:
            duplicates.append(ticket.id)
        seen.add(ticket.id)
    if duplicates:
        raise InvalidBatch(f"Duplicate ticket ids: {', '.join(duplicates)}.")
