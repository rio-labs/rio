import uvicorn

import showcase

if __name__ == "__main__":
    uvicorn.run(
        showcase.fastapi_app,
        port=8001,
    )
