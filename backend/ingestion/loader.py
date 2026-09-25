from pathlib import Path

def load_pdf(pdf_path: str) -> Path:
    """
    Validate and return the PDF path.
    """
    
    if not pdf_path:
        raise ValueError("Path is required")
    
    path = Path(pdf_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found at: {pdf_path}")
    
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")
    
    return path
