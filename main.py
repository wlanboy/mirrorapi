from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.routing import APIRoute
from contextlib import asynccontextmanager
from sqlalchemy import text
import logging
import signal
import sys

from header_api import header_router
from query_api import query_router
from echo_api import echo_router
from mirror_api import mirror_router, init_db, engine

logging.basicConfig()
logger = logging.getLogger('uvicorn')
logger.setLevel(logging.DEBUG)


def generate_unique_id(route: APIRoute) -> str:
    """Generate unique operation IDs including the HTTP method."""
    return f"{route.name}_{list(route.methods)[0].lower()}"


def handle_sigterm(signum, frame):
    print("SIGTERM received. Shutting down gracefully...")
    print("Cleanup complete. Exiting.")
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_sigterm)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Mirror Echo API",
    version="v1",
    docs_url="/swagger-ui",
    redoc_url="/redoc",
    lifespan=lifespan,
    generate_unique_id_function=generate_unique_id
)

# Register routers
app.include_router(header_router)
app.include_router(query_router)
app.include_router(echo_router)
app.include_router(mirror_router)


@app.get("/", response_class=HTMLResponse)
async def info_page():
    """Application information page."""
    return """
    <html>
    <body style="background-color:#121212; color:#e0e0e0; font-family:sans-serif;">
    <h3 style="color:#bb86fc;">Application Information</h3>
    <p><strong>OpenAPI URL:</strong> <a href="/swagger-ui" style="color:#BB86FC;">/swagger-ui</a></p>
    </body>
    </html>
    """


@app.get("/health")
async def health():
    """Liveness Probe: checks if the application is running."""
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    """Readiness Probe: checks application and database connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse(
            content={"status": "not ready", "error": str(e)},
            status_code=500
        )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4500)
