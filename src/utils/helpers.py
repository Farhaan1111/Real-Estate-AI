"""Utility functions for Real Estate AI"""

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Basic cleaning
    text = text.strip()
    text = ' '.join(text.split())  # Remove extra whitespace
    
    return text

def chunk_text(text: str, max_length: int = 500) -> List[str]:
    """Split text into chunks"""
    if len(text) <= max_length:
        return [text]
    
    # Simple chunking by sentences (you can enhance this)
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk + sentence) <= max_length:
            current_chunk += sentence + ". "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks