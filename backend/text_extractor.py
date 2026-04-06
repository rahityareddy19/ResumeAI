"""
Text Extraction Module
Handles extracting text content from PDF, DOCX, and TXT files.
"""

import os
import pdfplumber
from docx import Document


def extract_from_pdf(filepath: str) -> str:
    """Extract text from a PDF file using pdfplumber."""
    text_parts = []
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}")
    return "\n".join(text_parts)


def extract_from_docx(filepath: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    text_parts = []
    try:
        doc = Document(filepath)
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {e}")
    return "\n".join(text_parts)


def extract_from_txt(filepath: str) -> str:
    """Extract text from a plain text file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise ValueError(f"Failed to read text file: {e}")


def extract_text(filepath: str) -> str:
    """
    Auto-detect file format and extract text.
    Supports: .pdf, .docx, .txt
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()

    extractors = {
        ".pdf": extract_from_pdf,
        ".docx": extract_from_docx,
        ".txt": extract_from_txt,
    }

    extractor = extractors.get(ext)
    if extractor is None:
        raise ValueError(f"Unsupported file format: {ext}. Supported: .pdf, .docx, .txt")

    text = extractor(filepath)
    if not text.strip():
        raise ValueError(f"No text could be extracted from: {os.path.basename(filepath)}")

    return text
