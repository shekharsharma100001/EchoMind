import json
import re
from openai import OpenAI
from app.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_SUMMARY_MODEL,
    OPENROUTER_RAG_MODEL
)


def get_openrouter_client() -> OpenAI:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is missing")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )


def safe_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def transcript_needs_cleanup(transcript: str) -> bool:
    if not transcript or len(transcript.strip()) < 40:
        return False

    text = transcript.strip()

    # too many repeated filler/noise markers
    noise_patterns = [
        r"\b(um|uh|hmm|mmm)\b",
        r"\[.*?noise.*?\]",
        r"\[.*?inaudible.*?\]",
        r"\bunclear\b",
        r"\bunknown\b",
    ]

    noise_hits = sum(len(re.findall(pattern, text, flags=re.IGNORECASE)) for pattern in noise_patterns)

    # many very short broken words
    words = text.split()
    short_tokens = sum(1 for w in words if len(w) <= 2)

    # low punctuation can signal messy transcript
    punctuation_hits = len(re.findall(r"[.!?]", text))

    if noise_hits >= 3:
        return True

    if len(words) > 40 and short_tokens / max(len(words), 1) > 0.35:
        return True

    if len(words) > 60 and punctuation_hits < 2:
        return True

    return False


def clean_transcript_with_llm(raw_transcript: str, context: str = "") -> str:
    client = get_openrouter_client()
    safe_context = safe_text(context)

    prompt = f"""
You are cleaning a speech-to-text transcript generated from audio.

Your job:
1. Correct obvious ASR mistakes only when highly likely.
2. Use the optional context if provided.
3. Preserve the original meaning and full content.
4. Do not shorten the transcript.
5. Do not omit any important information.
6. Do not add information not present in the transcript.
7. Make the transcript readable and properly punctuated.
8. Keep the conversation in transcript form.
9. If speaker labels already exist, preserve them.
10. If some words are still uncertain, keep the most reasonable wording without inventing new facts.

Optional context:
{safe_context if safe_context else "No extra context provided."}

Transcript:
{raw_transcript}
""".strip()

    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are an expert transcript cleanup assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=4000,
    )

    content = response.choices[0].message.content
    return safe_text(content)


def generate_structured_summary(transcript: str, context: str = "") -> dict:
    client = get_openrouter_client()
    safe_context = safe_text(context)

    prompt = f"""
Create a structured summary for the following transcript.





Optional context:
{safe_context if safe_context else "No extra context provided."}

Transcript:
{transcript}
""".strip()

    response = client.chat.completions.create(
    model=OPENROUTER_SUMMARY_MODEL,
    messages=[
        {
            "role": "system",
            "content": "You are an expert summarization assistant."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    temperature=0.2,
    max_tokens=600,
    extra_body={"reasoning": {"enabled": True}}
    )

    content = safe_text(response.choices[0].message.content)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "title": "Conversation Summary",
            "summary": content,
            "key_points": [],
            "action_items": [],
            "sentiment_overview": "",
        }
    


def answer_question_with_rag_context(question: str, retrieved_chunks: list[dict]) -> str:
    client = get_openrouter_client()

    safe_question = safe_text(question)

    if not safe_question:
        return "Question is empty."

    if not retrieved_chunks:
        return "I could not find relevant information in the processed file."

    context_parts = []
    for chunk in retrieved_chunks:
        chunk_id = chunk.get("chunk_id", "unknown")
        text = safe_text(chunk.get("text", ""))
        if text:
            context_parts.append(f"[Chunk {chunk_id}]\n{text}")

    combined_context = "\n\n".join(context_parts)

    prompt = f"""
Answer the user's question using only the provided context.

Rules:
1. Answer only from the context below.
2. Do not use outside knowledge.
3. If the answer is not present in the context, say: "The answer is not available in the provided file."
4. Keep the answer clear and concise.
5. If useful, mention the relevant point directly.

Context:
{combined_context}

Question:
{safe_question}
""".strip()

    response = client.chat.completions.create(
        model=OPENROUTER_RAG_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a grounded question-answering assistant. Answer only from the supplied context."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=500,
    )

    content = response.choices[0].message.content if response.choices else ""
    return safe_text(content) or "The answer is not available in the provided file."