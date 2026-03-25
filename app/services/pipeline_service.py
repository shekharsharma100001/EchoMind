import json
from pathlib import Path

from app.config import DEEPGRAM_API_KEY
from app.services.deepgram_service import (
    transcribe_audio,
    extract_transcript_text,
    extract_utterances,
)
from app.services.file_parser_service import extract_text_from_document
from app.services.video_audio_service import extract_audio_from_video
from app.services.llm_service import (
    transcript_needs_cleanup,
    clean_transcript_with_llm,
    generate_structured_summary,
)


def _save_json(data: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False, default=str)


def _save_text(text: str, path: str) -> None:
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)

def format_conversation(utterances: list) -> str:
    if not utterances:
        return ""

    speaker_map = {}
    speaker_count = 1
    conversation = []

    for utterance in utterances:
        raw_speaker = utterance.get("speaker", 0)

        if raw_speaker not in speaker_map:
            speaker_map[raw_speaker] = speaker_count
            speaker_count += 1

        speaker_number = speaker_map[raw_speaker]
        text = (utterance.get("transcript") or "").strip()

        if not text:
            continue

        conversation.append(f"Speaker {speaker_number}: {text}")

    return "\n".join(conversation)


def process_audio_file(file_info: dict) -> dict:
    saved_path = file_info["saved_path"]
    processed_dir = Path(file_info["processed_dir"])

    with open(saved_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    dg_response = transcribe_audio(audio_bytes=audio_bytes, api_key=DEEPGRAM_API_KEY)
    print("DEEPGRAM RESULTS KEYS:", dg_response.get("results", {}).keys())
    print("RAW UTTERANCES FIELD:", dg_response.get("results", {}).get("utterances"))
    transcript = extract_transcript_text(dg_response)
    utterances = extract_utterances(dg_response)
    print("UTTERANCES COUNT:", len(utterances))
    print("UTTERANCES SAMPLE:", utterances[:2] if utterances else utterances)
    conversation_text = format_conversation(utterances)
    if not conversation_text:
        conversation_text = "Diarized transcript could not be generated for this file."

    needs_cleanup = transcript_needs_cleanup(transcript)
    cleaned_transcript = transcript

    if needs_cleanup:
        cleaned_transcript = clean_transcript_with_llm(
        raw_transcript=transcript,
        context=file_info.get("context") or ""
    )

    raw_json_path = processed_dir / "raw_transcript.json"
    transcript_txt_path = processed_dir / "transcript.txt"
    cleaned_transcript_txt_path = processed_dir / "cleaned_transcript.txt"
    conversation_path = processed_dir / "conversation.txt"

    _save_text(conversation_text, str(conversation_path))
    _save_json(dg_response, str(raw_json_path))
    _save_text(transcript, str(transcript_txt_path))
    _save_text(cleaned_transcript, str(cleaned_transcript_txt_path))

    structured_summary = generate_structured_summary(
    transcript=cleaned_transcript,
    context=file_info.get("context") or ""
    )

    summary_json_path = processed_dir / "structured_summary.json"
    _save_structured_json(structured_summary, str(summary_json_path))

    return {
        "pipeline": "audio",
        "transcript": transcript,
        "utterances": utterances,
        "raw_transcript_path": str(raw_json_path),
        "transcript_path": str(transcript_txt_path),
        "cleaned_transcript": cleaned_transcript,
        "needs_cleanup": needs_cleanup,
        "structured_summary": structured_summary,
        "cleaned_transcript_path": str(cleaned_transcript_txt_path),
        "structured_summary_path": str(summary_json_path),
        "conversation": conversation_text,
        "conversation_path": str(conversation_path)
    }


def process_video_file(file_info: dict) -> dict:
    saved_path = file_info["saved_path"]
    processed_dir = Path(file_info["processed_dir"])

    extracted_audio_path = extract_audio_from_video(
        video_path=saved_path,
        output_dir=str(processed_dir),
    )

    with open(extracted_audio_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    dg_response = transcribe_audio(audio_bytes=audio_bytes, api_key=DEEPGRAM_API_KEY)
    transcript = extract_transcript_text(dg_response)
    utterances = extract_utterances(dg_response)
    conversation_text = format_conversation(utterances)
    if not conversation_text:
        conversation_text = "Diarized transcript could not be generated for this file."
    


    needs_cleanup = transcript_needs_cleanup(transcript)
    cleaned_transcript = transcript

    if needs_cleanup:
        cleaned_transcript = clean_transcript_with_llm(
        raw_transcript=transcript,
        context=file_info.get("context") or ""
        )

    raw_json_path = processed_dir / "raw_transcript.json"
    transcript_txt_path = processed_dir / "transcript.txt"
    cleaned_transcript_txt_path = processed_dir / "cleaned_transcript.txt"
    conversation_path = processed_dir / "conversation.txt"
    _save_text(conversation_text, str(conversation_path))
    _save_json(dg_response, str(raw_json_path))
    _save_text(transcript, str(transcript_txt_path))
    _save_text(cleaned_transcript, str(cleaned_transcript_txt_path))

    structured_summary = generate_structured_summary(
    transcript=cleaned_transcript,
    context=file_info.get("context") or ""
    )

    summary_json_path = processed_dir / "structured_summary.json"
    _save_structured_json(structured_summary, str(summary_json_path))

    return {
        "pipeline": "video",
        "extracted_audio_path": extracted_audio_path,
        "transcript": transcript,
        "utterances": utterances,
        "raw_transcript_path": str(raw_json_path),
        "transcript_path": str(transcript_txt_path),
        "cleaned_transcript": cleaned_transcript,
        "needs_cleanup": needs_cleanup,
        "structured_summary": structured_summary,
        "cleaned_transcript_path": str(cleaned_transcript_txt_path),
        "structured_summary_path": str(summary_json_path),
        "conversation": conversation_text,
        "conversation_path": str(conversation_path)
    }


def process_document_file(file_info: dict) -> dict:
    saved_path = file_info["saved_path"]
    processed_dir = Path(file_info["processed_dir"])

    extracted_text = extract_text_from_document(saved_path)
    needs_cleanup = transcript_needs_cleanup(extracted_text)
    cleaned_transcript = extracted_text

    if needs_cleanup:
        cleaned_transcript = clean_transcript_with_llm(
        raw_transcript=extracted_text,
        context=file_info.get("context") or ""
        )
    structured_summary = generate_structured_summary(
    transcript=cleaned_transcript,
    context=file_info.get("context") or ""
    )

    extracted_text_path = processed_dir / "document_text.txt"
    _save_text(extracted_text, str(extracted_text_path))
    cleaned_transcript_txt_path = processed_dir / "cleaned_transcript.txt"
    summary_json_path = processed_dir / "structured_summary.json"

    _save_text(cleaned_transcript, str(cleaned_transcript_txt_path))
    _save_structured_json(structured_summary, str(summary_json_path))

    return {
        "pipeline": "document",
        "transcript": extracted_text,
        "utterances": [],
        "document_text_path": str(extracted_text_path),
        "cleaned_transcript": cleaned_transcript,
        "needs_cleanup": needs_cleanup,
        "structured_summary": structured_summary,
        "cleaned_transcript_path": str(cleaned_transcript_txt_path),
        "structured_summary_path": str(summary_json_path)
    }


def process_uploaded_file(file_info: dict) -> dict:
    file_type = file_info["file_type"]

    if file_type == "audio":
        return process_audio_file(file_info)
    if file_type == "video":
        return process_video_file(file_info)
    if file_type == "document":
        return process_document_file(file_info)

    raise ValueError("Unsupported file type for processing")

def _save_structured_json(data: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

