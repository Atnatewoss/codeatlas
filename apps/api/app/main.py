import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.log import setup_logging, get_logger
from app.routers.chat import router as chat_router

setup_logging()

_api_env = Path(__file__).parent.parent / ".env"
if _api_env.exists():
    load_dotenv(_api_env, override=False)
    get_logger(__name__).info("Loaded env from %s", _api_env)

app = FastAPI(title="CodeAtlas API", description="Backend for Repository Intelligence Workspace")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
