from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import traceback

from app.services.file_parser_service import build_upload_response
from app.services.pipeline_service import process_uploaded_file
from app.utils.file_utils import save_uploaded_file

router = APIRouter(prefix="/api", tags=["Upload"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    context: str = Form(default=""),
    generate_transcript: str = Form(default="true"),
    refine_transcript: str = Form(default="true"),
    speaker_diarization: str = Form(default="true"),
    generate_summary: str = Form(default="true"),
    sentiment_analysis: str = Form(default="true"),
    enable_rag: str = Form(default="true"),
):
    try:
        file_info = await save_uploaded_file(file)
        file_info["context"] = context or ""
        result = process_uploaded_file(file_info)
        print("CONVERSATION RETURNED:", repr(result.get("conversation", ""))[:500])

        return {
            "message": "File uploaded and processed successfully",
            "file_id": file_info["file_id"],
            "filename": file_info["original_filename"],
            "file_type": file_info["file_type"],
            "context": context,
            "options": {
                "generate_transcript": generate_transcript,
                "refine_transcript": refine_transcript,
                "speaker_diarization": speaker_diarization,
                "generate_summary": generate_summary,
                "sentiment_analysis": sentiment_analysis,
                "enable_rag": enable_rag,
            },
            "transcript": result.get("transcript", ""),
            "utterances": result.get("utterances", []),
            "pipeline": result.get("pipeline"),
            "paths": result,
            "cleaned_transcript": result.get("cleaned_transcript", ""),
            "needs_cleanup": result.get("needs_cleanup", False),
            "summary": result.get("structured_summary", {}),
            "conversation": result.get("conversation", ""),
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(exc)}") from exc