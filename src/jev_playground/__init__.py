def main() -> None:
    import uvicorn

    from jev_playground.config import Settings

    settings = Settings()
    uvicorn.run(
        "jev_playground.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
    )
