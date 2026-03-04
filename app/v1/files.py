# file_download.py
# Basic file download endpoint using FileResponse
from fastapi import FastAPI, HTTPException, APIRouter, Depends
from fastapi.responses import FileResponse
from pathlib import Path

from app.v1.users import verify_token

router=APIRouter()

# Base directory for downloadable files
DOWNLOADS_DIR = Path("D:/ПУ/II курс/Python/PyPDFSearcher/generated_reports")

@router.get("/download/{filename}",tags=["files"])
async def download_file(filename: str):
    """
    Download a file by name from the downloads directory.
    FileResponse handles streaming and content-type automatically.
    """
    # Construct full path and validate it exists
    file_path = DOWNLOADS_DIR / filename

    # Security check - prevent directory traversal attacks
    if not file_path.resolve().is_relative_to(DOWNLOADS_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # FileResponse streams the file and sets Content-Type based on extension
    return FileResponse(
        path=file_path,
        filename=filename,  # Sets Content-Disposition header
        media_type="application/octet-stream"  # Force download instead of display
    )