import fitz
from docx import Document
import spacy
import re
import os

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(file_path: str) -> str:
    text = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text.append(page.get_text())
    return "\n".join(text)

def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    text = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(text)

def clean_text(text: str) -> str:
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def segment_into_clauses(text: str) -> list[str]:
    doc = nlp(text)
    clauses = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 30]
    return clauses

def process_document(file_path: str) -> list[str]:
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        raw_text = extract_text_from_pdf(file_path)
    elif ext == ".docx":
        raw_text = extract_text_from_docx(file_path)
    else:
        return []
        
    cleaned_text = clean_text(raw_text)
    clauses = segment_into_clauses(cleaned_text)
    
    return clauses
