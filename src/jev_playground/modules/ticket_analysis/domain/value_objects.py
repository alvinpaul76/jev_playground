from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class Category(StrEnum):
    INCIDENT = "incident"
    SECURITY = "security"
    UI = "ui"
    PERFORMANCE = "performance"
    FINANCIAL_INTEGRITY = "financial_integrity"
    FEATURE_REQUEST = "feature_request"
    REGRESSION = "regression"
    AUTHENTICATION = "authentication"


@dataclass(frozen=True, slots=True)
class Probability:
    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Probability must be within [0, 1], got {self.value}")
