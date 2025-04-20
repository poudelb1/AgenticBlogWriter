import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from generate_blog import generate_blog, BlogGenerationError  # Import custom exception
import json # Import json for detailed error logging

from dotenv import load_dotenv
load_dotenv()

# --- Centralized Logging Configuration ---
# Configure logging basic settings once at the application start
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# Get the root logger used by FastAPI/Uvicorn
logger = logging.getLogger("uvicorn.error")
logger.propagate = False # Prevent duplicate logging if uvicorn adds its own handlers
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers: # Avoid adding handler multiple times on reload
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
# ---------------------------------------

# Instantiate FastAPI
app = FastAPI(
    title="CrewAI Blog Generator API",
    description="API to generate blog posts using a multi-agent CrewAI pipeline.",
    version="1.0.1" # Incremented version
)

# --- CORS Configuration ---
# Allows requests from the frontend (running on any origin in dev).
# For production, restrict this to your frontend's actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Be more restrictive in production! e.g., ["http://localhost:xxxx", "https://yourfrontend.com"]
    allow_credentials=True, # Usually needed with specific origins if cookies/auth are involved
    allow_methods=["POST", "OPTIONS"], # Allow POST and preflight OPTIONS requests
    allow_headers=["*"], # Allow common headers like Content-Type
)
# ------------------------

# --- Pydantic Models ---
# Define the structure for request and response data
class BlogRequest(BaseModel):
    topic: str

class BlogResponse(BaseModel):
    title: str
    body_markdown: str
    image_url: str | None # Allow image_url to be None if generation fails
# ---------------------

@app.post("/api/generate-blog", response_model=BlogResponse)
async def generate_blog_endpoint(request: BlogRequest, http_request: Request):
    """
    Generate a full blog post (title, body, image) for the given topic.
    """
    client_host = http_request.client.host if http_request.client else "unknown"
    logger.info(f"Received request for topic: '{request.topic}' from {client_host}")

    try:
        # Call the core generation logic
        result = generate_blog(request.topic)
        logger.info(f"Successfully generated blog for topic: '{request.topic}'")
        # Ensure result dictionary keys match BlogResponse fields before unpacking
        return BlogResponse(
            title=result.get("title", f"Blog on {request.topic}"),
            body_markdown=result.get("body_markdown", "Error: Could not generate body."),
            image_url=result.get("image_url") # Will be None if not present or empty
        )
    except BlogGenerationError as bge:
        # Catch specific errors from the generation process (e.g., missing keys, agent failure)
        logger.error(f"Blog generation error for topic '{request.topic}': {bge}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate blog: {bge}")
    except EnvironmentError as ee:
        # Catch missing API key errors specifically
        logger.error(f"Configuration error during blog generation: {ee}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server configuration error: {ee}")
    except Exception as e:
        # Catch any other unexpected errors
        logger.exception(f"Unexpected error during blog generation for topic '{request.topic}'") # Use logger.exception to include traceback
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")


# Add a simple root endpoint for health checks or info
@app.get("/")
async def read_root():
    return {"message": "CrewAI Blog Generator API is running."}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0") # Corrected typo "}" -> "0"
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        log_level="info", # Uvicorn's log level
        reload=True # Enable auto-reload for development convenience
    )