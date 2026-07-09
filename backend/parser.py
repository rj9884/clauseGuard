import fitz
from docx import Document
import re
import os

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
    """
    Splits document text into clauses (sentences) using a lightweight regex-based tokenizer.
    Avoids using spaCy to prevent dependency bloat and heavy memory footprint.
    """
    # Simple regex for sentence boundary detection:
    # Look for a period, exclamation, or question mark, followed by a space,
    # ensuring it's not preceded by common abbreviations.
    sentence_end = re.compile(
        r'(?<!\b(?:Inc|Co|Corp|Ltd|e\.g|i\.e|vs|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|No|Sec|Art|para))\.'
        r'(?=\s+[A-Z0-9]|\s*$)'
    )
    
    # Split paragraphs first, then segment sentences within paragraphs
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    
    clauses = []
    for paragraph in paragraphs:
        # Rebuild sentences by splitting on the regex
        matches = list(sentence_end.finditer(paragraph))
        start = 0
        current_sentences = []
        for match in matches:
            end = match.end()
            current_sentences.append(paragraph[start:end].strip())
            start = end
        if start < len(paragraph):
            current_sentences.append(paragraph[start:].strip())
            
        for sent in current_sentences:
            if len(sent) > 30:
                clauses.append(sent)
                
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
