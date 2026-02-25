import uvicorn


def main() -> None:
    """
    Entry point for the concierge OS server.

    Run with: `python main.py`
    """
    uvicorn.run(
        "concierge_os.server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()

