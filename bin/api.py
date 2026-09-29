import logging

import uvicorn

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    uvicorn.run("src.fastapi:create_app", factory=True, host="0.0.0.0", port=8000)
