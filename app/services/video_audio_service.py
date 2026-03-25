import subprocess
from pathlib import Path

from app.config import FFMPEG_BINARY


def extract_audio_from_video(video_path: str, output_dir: str) -> str:
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_audio_path = output_dir / "extracted_audio.wav"

    command = [
        FFMPEG_BINARY,
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_audio_path),
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Video to audio extraction failed: {result.stderr}")

    return str(output_audio_path)