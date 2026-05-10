import os
import google.generativeai as genai
import json
from dotenv import load_dotenv

def setup_gemini():
    load_dotenv(override=True)
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment.")
    genai.configure(api_key=api_key)

def upload_to_gemini(file_path, mime_type=None):
    setup_gemini()
    print(f"Uploading file to Gemini: {file_path}")
    gemini_file = genai.upload_file(file_path, mime_type=mime_type)
    return gemini_file

def _get_model():
    # Use standard flash model for multimodal input
    return genai.GenerativeModel('gemini-2.5-flash')

def wait_for_file_active(gemini_file):
    import time
    print(f"Checking state for file {gemini_file.name}...")
    while gemini_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(2)
        gemini_file = genai.get_file(gemini_file.name)
    if gemini_file.state.name == "FAILED":
        raise Exception("File processing failed on Gemini servers.")
    print("File is ready!")
    return gemini_file

def transcribe_file(gemini_file_name, context="", language="Default"):
    setup_gemini()
    model = _get_model()
    gemini_file = genai.get_file(gemini_file_name)
    gemini_file = wait_for_file_active(gemini_file)
    print(f"Starting generate_content for {gemini_file_name}")
    prompt = "Provide a verbatim transcript of the speech in this file. Output just the transcript text without any extra conversational filler."
    if context:
        prompt += f"\n\nContext provided by user: {context}"
    if language and language != "Default":
        prompt += f"\n\nCRITICAL: You MUST translate and generate the entire response in {language}."
    else:
        prompt += f"\n\nCRITICAL: You MUST generate the response in the exact language(s) natively spoken in the file (e.g., if the file contains Hinglish, generate in Hinglish)."
        
    response = model.generate_content([gemini_file, prompt])
    return response.text

def diarize_file(gemini_file_name, context="", language="Default"):
    setup_gemini()
    model = _get_model()
    gemini_file = genai.get_file(gemini_file_name)
    gemini_file = wait_for_file_active(gemini_file)
    print(f"Starting generate_content (diarize) for {gemini_file_name}")

    prompt = """You are an expert conversation analyst. Your task is to produce a speaker-diarized transcript.

CRITICAL RULES — follow in this exact priority order:

1. NAMED SPEAKERS (highest priority): If the user provides names in the context below, use those exact names as speaker labels.

2. ROLE/PERSONA DEDUCTION (mandatory if no names given): You MUST analyze the conversation content deeply and deduce meaningful role-based names. Examples:
   - A store conversation → "Sales Associate" and "Customer"
   - A medical call → "Doctor" and "Patient"
   - A job interview → "Interviewer" and "Candidate"
   - A support call → "Support Agent" and "User"
   - A podcast → "Host" and "Guest"
   - A negotiation → "Buyer" and "Seller"
   DO NOT skip this step. Always assign a meaningful role label.

3. GENERIC FALLBACK (absolute last resort ONLY): Use "Speaker 1", "Speaker 2" ONLY if the conversation gives ZERO contextual clues about roles, topic, or setting — this should be extremely rare.

FORMAT: Output each line as:
<SpeakerName>: <spoken text>

Do not include timestamps, headers, or any other text — only the diarized lines."""

    if context:
        prompt += f"\n\nUser-provided context (use this to identify speakers): {context}"

    if language and language != "Default":
        prompt += f"\n\nCRITICAL: Translate and generate the entire response in {language}."
    else:
        prompt += "\n\nCRITICAL: Generate the response in the exact language(s) spoken in the file."

    response = model.generate_content([gemini_file, prompt])
    return response.text


def summarize_content(gemini_file_name, context="", language="Default", summary_length="Detailed", summary_type="Paragraph", summary_prompt=""):
    setup_gemini()
    # Use pro for heavier reasoning if preferred, flash is usually fine
    model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
    gemini_file = genai.get_file(gemini_file_name)
    gemini_file = wait_for_file_active(gemini_file)
    print(f"Starting generate_content (summarize) for {gemini_file_name}")
    
    prompt = f"""
    Analyze the conversation or document in this file. Provide a response in valid JSON format with exactly these five keys:
    1. "summary": A {summary_length} overview of the entire content formatted as {summary_type}.
    2. "key_insights": A list of 3-5 strings containing the most important takeaways or decisions.
    3. "metrics": An object with 3 keys: "Engagement" (0-100), "Clarity" (0-100), "Sentiment" (0-100) representing overall scores.
    4. "emotion_keywords": An object with keys "positive", "negative", "neutral", each containing a list of keyword strings from the conversation.
    5. "speaker_analysis": A list of objects, one per unique speaker detected, each with:
       - "speaker": the speaker's name or role label
       - "sentiment": 0-100 sentiment score for that speaker's lines only
       - "engagement": 0-100 engagement score for that speaker
       - "clarity": 0-100 clarity score for that speaker
       - "emotion_keywords": object with "positive", "negative", "neutral" keyword lists specific to that speaker
       - "key_trait": a single short string describing this speaker's personality or behavior (e.g. "Helpful and proactive", "Hesitant but curious")

    The "speaker_analysis" array must contain an entry for every distinct speaker in the conversation.
    Ensure the JSON is perfectly valid with no trailing commas.
    """
    if context:
        prompt += f"\n\nContext provided by user: {context}"
        
    if summary_prompt:
        prompt += f"\n\nCRITICAL STYLE INSTRUCTION: The user has requested the summary to be generated in the following style/persona: '{summary_prompt}'. You MUST apply this style/persona to the 'summary' field."
        
    if language and language != "Default":
        prompt += f"\n\nCRITICAL: You MUST translate and generate the entire response in {language}."
    else:
        prompt += f"\n\nCRITICAL: You MUST generate the response in the exact language(s) natively spoken in the file (e.g., if the file contains Hinglish, generate in Hinglish)."
        
    response = model.generate_content([gemini_file, prompt])
    raw = response.text.strip()

    # ── Attempt 1: strip markdown code fences (```json ... ``` or ``` ... ```)
    if raw.startswith('```'):
        lines = raw.split('\n')
        # drop first line (```json or ```) and last line (```)
        inner_lines = lines[1:] if len(lines) > 1 else lines
        if inner_lines and inner_lines[-1].strip() == '```':
            inner_lines = inner_lines[:-1]
        raw = '\n'.join(inner_lines).strip()

    # ── Attempt 2: try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # ── Attempt 3: find outermost { ... } block via regex
    import re
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # ── Final fallback: return the raw text as summary with safe empty defaults
    return {
        "summary": raw,
        "key_insights": [],
        "metrics": {"Engagement": 0, "Clarity": 0, "Sentiment": 50},
        "emotion_keywords": {"positive": [], "negative": [], "neutral": []},
        "speaker_analysis": []
    }
