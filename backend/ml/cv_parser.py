import fitz
from docx import Document
from PIL import Image
import pytesseract
import io

def extract_text_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

def extract_text_from_image(file_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(file_bytes))
    text = pytesseract.image_to_string(image, lang="eng")
    return text.strip()

def detect_skills(text: str, skill_vocab: dict) -> list:
    text_lower = text.lower()
    matched = []
    for skill in skill_vocab.keys():
        if f" {skill} " in f" {text_lower} ":
            matched.append(skill)
    return sorted(matched)

def parse_cv(file_bytes: bytes, filename: str, skill_vocab: dict) -> dict:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        text = extract_text_from_pdf(file_bytes)
    elif ext == "docx":
        text = extract_text_from_docx(file_bytes)
    elif ext in ("jpg", "jpeg", "png"):
        text = extract_text_from_image(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")
        
    skills = detect_skills(text, skill_vocab)
    
    return {
        "extracted_text": text,
        "detected_skills": skills,
        "word_count": len(text.split()),
        "file_type": ext
    }
