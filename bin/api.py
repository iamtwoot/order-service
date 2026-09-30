import uvicorn

from src.log_config import configure_logging

if __name__ == "__main__":
    configure_logging()
    uvicorn.run("src.fastapi:create_app", factory=True, host="0.0.0.0", port=8000)
