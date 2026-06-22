from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.research import router as research_router
from routers.chat import router as chat_router
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(title="CodeAtlas API", description="Backend for Repository Intelligence Workspace")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev only, update for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router)
app.include_router(chat_router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
