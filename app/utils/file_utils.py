import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import (
    ALL_ALLOWED_EXTENSIONS,
    ALLOWED_AUDIO_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    ALLOWED_DOCUMENT_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    UPLOAD_DIR,
    PROCESSED_DIR,
)


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def detect_file_type(filename: str) -> str:
    extension = get_file_extension(filename)

    if extension in ALLOWED_AUDIO_EXTENSIONS:
        return "audio"
    if extension in ALLOWED_VIDEO_EXTENSIONS:
        return "video"
    if extension in ALLOWED_DOCUMENT_EXTENSIONS:
        return "document"

    return "unsupported"


def validate_file_extension(filename: str) -> None:
    extension = get_file_extension(filename)
    if extension not in ALL_ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension}")


async def validate_file_size(file: UploadFile) -> None:
    contents = await file.read()
    size = len(contents)
    await file.seek(0)

    if size > MAX_FILE_SIZE_BYTES:
        raise ValueError("File size exceeds allowed limit")


async def save_uploaded_file(file: UploadFile) -> dict:
    validate_file_extension(file.filename)
    await validate_file_size(file)

    file_id = str(uuid.uuid4())
    extension = get_file_extension(file.filename)
    file_type = detect_file_type(file.filename)

    upload_dir = UPLOAD_DIR / file_id
    processed_dir = PROCESSED_DIR / file_id

    upload_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    saved_path = upload_dir / f"original{extension}"

    with saved_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "file_id": file_id,
        "original_filename": file.filename,
        "saved_path": str(saved_path),
        "file_type": file_type,
        "extension": extension,
        "upload_dir": str(upload_dir),
        "processed_dir": str(processed_dir),
    }