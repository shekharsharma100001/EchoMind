from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
PROCESSED_DIR = STORAGE_DIR / "processed"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".aac"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi"}
ALLOWED_DOCUMENT_EXTENSIONS = {".txt", ".pdf", ".doc", ".docx"}

ALL_ALLOWED_EXTENSIONS = (
    ALLOWED_AUDIO_EXTENSIONS
    | ALLOWED_VIDEO_EXTENSIONS
    | ALLOWED_DOCUMENT_EXTENSIONS
)

MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
FFMPEG_BINARY = os.getenv("FFMPEG_BINARY", "ffmpeg")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "stepfun/step-3.5-flash:free")
OPENROUTER_SUMMARY_MODEL = os.getenv(
    "OPENROUTER_SUMMARY_MODEL",
    "nvidia/nemotron-3-super-120b-a12b:free"
)