from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.file_parser_service import build_upload_response
from app.utils.file_utils import save_uploaded_file

router = APIRouter(prefix="/api", tags=["Upload"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    context: str = Form(default=""),
):
    try:
        file_info = await save_uploaded_file(file)

        response = build_upload_response(file_info)
        response["context"] = context

        return response

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(exc)}") from exc