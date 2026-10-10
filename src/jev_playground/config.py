from typing import Annotated, Any, Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

MIN_CLIENT_KEY_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="JEV_", extra="ignore", populate_by_name=True
    )

    # "hf" runs a local model, "jev" calls the hosted Jev (TypeSafe) API.
    # "mock" is deterministic and only meant for tests.
    backend: Literal["hf", "jev", "mock"] = "hf"

    # hf backend
    model_id: str = "Qwen/Qwen2.5-0.5B-Instruct"

    # jev backend
    api_key: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("JEV_API_KEY", "TYPESAFE_API_KEY")
    )
    base_url: str = Field(
        default="https://api.typesafe.ai",
        validation_alias=AliasChoices("JEV_BASE_URL", "TYPESAFE_BASE_URL"),
    )
    jev_model: str = "jev-latest"
    jev_timeout_s: float = 30.0

    # Keys that *clients* must send in `X-API-Key` to call this service (inbound).
    # Not to be confused with `api_key`, which this service uses to call Jev (outbound).
    client_api_keys: Annotated[list[SecretStr], NoDecode] = []
    # Set to false to run /api/v1/* without a key (local development only).
    auth_enabled: bool = True

    # Interactive docs and the OpenAPI schema are off unless asked for (local development).
    expose_docs: bool = False
    # Largest accepted request body. A full batch is well under 1 MiB; field limits only
    # apply after the body is read, so this bounds memory first.
    max_request_bytes: int = Field(default=2_097_152, ge=1_024)
    log_level: str = "INFO"
    host: str = "127.0.0.1"
    port: int = 8000

    @field_validator("client_api_keys", mode="before")
    @classmethod
    def _split_keys(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value

    @field_validator("client_api_keys")
    @classmethod
    def _check_key_strength(cls, keys: list[SecretStr]) -> list[SecretStr]:
        for key in keys:
            if len(key.get_secret_value()) < MIN_CLIENT_KEY_LENGTH:
                raise ValueError(
                    f"each client API key must be at least {MIN_CLIENT_KEY_LENGTH} characters"
                )
        return keys
