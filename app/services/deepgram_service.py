from deepgram import DeepgramClient


def transcribe_audio(audio_bytes: bytes, api_key: str) -> dict:
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY is missing")

    dg = DeepgramClient(api_key=api_key)

    response = dg.listen.v1.media.transcribe_file(
        request=audio_bytes,
        model="nova-3",
        smart_format=True,
        diarize=True,
        utterances=True,
        punctuate=True,
    )

    if hasattr(response, "to_dict"):
        return response.to_dict()
    if hasattr(response, "model_dump"):
        return response.model_dump()

    raise TypeError("Unsupported Deepgram response type")


def extract_transcript_text(data: dict) -> str:
    try:
        return data["results"]["channels"][0]["alternatives"][0]["transcript"]
    except (KeyError, IndexError, TypeError):
        return ""


def extract_utterances(data: dict) -> list:
    try:
        utterances = data["results"].get("utterances", [])
        return utterances if isinstance(utterances, list) else []
    except (KeyError, TypeError, AttributeError):
        return []