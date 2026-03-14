from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import basic, agents, files

app = FastAPI(title="SSE Task Runner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

app.include_router(basic.router)
app.include_router(agents.router)
app.include_router(files.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
