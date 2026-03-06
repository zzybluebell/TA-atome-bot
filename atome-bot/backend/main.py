import logging
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

def _resolve_runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent.parent
    return Path(__file__).resolve().parent

RUNTIME_ROOT = _resolve_runtime_root()
load_dotenv(RUNTIME_ROOT / ".env")
os.environ.setdefault("CHROMA_PERSIST_DIR", str(RUNTIME_ROOT / "chroma_db"))
if getattr(sys, "frozen", False):
    os.environ.setdefault("CHROMA_DISABLED", "1")

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from app.agent import get_bot_instance
from app.manager import meta_agent_instance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
MAX_UPLOAD_FILES = 10
MAX_UPLOAD_FILE_SIZE = 10 * 1024 * 1024


def _parse_bool_form_value(raw_value: str) -> bool:
    return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}

app = FastAPI(title="Atome AI Bot API")

def _resolve_static_dir() -> Path | None:
    if getattr(sys, "frozen", False):
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        packaged_dist = base_dir / "frontend_dist"
        if packaged_dist.exists():
            return packaged_dist
    local_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if local_dist.exists():
        return local_dist
    return None

STATIC_DIR = _resolve_static_dir()
if STATIC_DIR:
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List] = []

class ConfigUpdateRequest(BaseModel):
    url: Optional[str] = None
    guidelines: Optional[List[str]] = None
    force_recrawl: Optional[bool] = False

class FeedbackRequest(BaseModel):
    user_query: str
    bot_response: str
    feedback: str

class ManagerInstructionRequest(BaseModel):
    instruction: str

@app.get("/")
def read_root():
    if STATIC_DIR:
        return FileResponse(STATIC_DIR / "index.html")
    return {"status": "ok", "service": "Atome AI Bot"}

@app.on_event("startup")
def startup_event():
    """Initialize bot on startup."""
    if os.getenv("CHROMA_DISABLED") == "1":
        return
    logger.info("Starting up Atome AI Bot...")
    try:
        get_bot_instance().initialize()
    except Exception as e:
        logger.error(f"Failed to initialize bot knowledge base: {e}")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Chat with the customer service bot."""
    try:
        response = get_bot_instance().chat(request.message, request.chat_history)
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
def get_config():
    """Get current bot configuration."""
    return {
        "url": get_bot_instance().knowledge_base_url,
        "guidelines": get_bot_instance().additional_guidelines
    }

@app.post("/api/config")
def update_config(config: ConfigUpdateRequest):
    """Update bot configuration (URL or guidelines)."""
    try:
        result = get_bot_instance().update_config(
            url=config.url,
            guidelines=config.guidelines,
            force_recrawl=bool(config.force_recrawl),
        )
        return {"status": "success", "message": "Configuration updated", **result}
    except Exception as e:
        logger.error(f"Config update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
def report_mistake(feedback: FeedbackRequest):
    """Report a mistake and auto-fix the bot."""
    try:
        new_rule = meta_agent_instance.auto_fix_mistake(
            feedback.user_query, 
            feedback.bot_response, 
            feedback.feedback
        )
        return {
            "status": "success", 
            "message": "Feedback processed. Auto-fix applied.",
            "new_rule": new_rule
        }
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/manager/instruct")
def manager_instruction(req: ManagerInstructionRequest):
    """Process manager's natural language instruction."""
    try:
        summary = meta_agent_instance.process_manager_instruction(req.instruction)
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.error(f"Manager instruction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/manager/upload-docs")
async def manager_upload_docs(
    files: List[UploadFile] = File(...),
    replace_existing: str = Form("false"),
):
    try:
        replace_existing_enabled = _parse_bool_form_value(replace_existing)
        if len(files) > MAX_UPLOAD_FILES:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files. Maximum allowed is {MAX_UPLOAD_FILES}.",
            )

        payloads: List[tuple[str, bytes]] = []
        for file in files:
            content = await file.read()
            if not content:
                continue
            if len(content) > MAX_UPLOAD_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{file.filename}' exceeds size limit ({MAX_UPLOAD_FILE_SIZE // (1024 * 1024)}MB).",
                )
            payloads.append((file.filename or "uploaded_file", content))

        if not payloads:
            raise HTTPException(status_code=400, detail="No valid file content found in upload.")

        result = get_bot_instance().ingest_documents(payloads, replace_existing=replace_existing_enabled)
        return {"status": "success", "replace_existing_applied": replace_existing_enabled, **result}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload docs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if STATIC_DIR:
    @app.get("/{path:path}")
    def serve_spa(path: str):
        file_path = STATIC_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")

if __name__ == "__main__":
    import uvicorn

    def _open_browser():
        time.sleep(1.2)
        webbrowser.open("http://127.0.0.1:8000")

    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
