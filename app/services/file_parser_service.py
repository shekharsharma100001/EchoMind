
from pathlib import Path

from pypdf import PdfReader
from docx import Document


def extract_text_from_txt(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8", errors="ignore")


def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts).strip()


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs).strip()


def extract_text_from_document(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()

    if suffix == ".txt":
        return extract_text_from_txt(file_path)
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    if suffix in {".doc", ".docx"}:
        return extract_text_from_docx(file_path)

    raise ValueError(f"Unsupported document type: {suffix}")



def build_upload_response(file_info: dict) -> dict:
    return {
        "message": "File uploaded successfully",
        "file_id": file_info["file_id"],
        "filename": file_info["original_filename"],
        "file_type": file_info["file_type"],
        "saved_path": file_info["saved_path"],
    }