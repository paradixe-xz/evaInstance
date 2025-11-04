"""
Document processing service for Knowledge Base
Handles text extraction from various file formats and chunking
"""
import os
import hashlib
import mimetypes
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

# Text processing
import re
from datetime import datetime

# File format handlers
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing documents and extracting text"""
    
    # Supported file types
    SUPPORTED_TYPES = {
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'md': 'text/markdown',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'json': 'application/json'
    }
    
    # Chunking parameters
    DEFAULT_CHUNK_SIZE = 1000  # characters
    DEFAULT_CHUNK_OVERLAP = 200  # characters
    MIN_CHUNK_SIZE = 100  # minimum chunk size
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """Initialize document processor"""
        self.chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or self.DEFAULT_CHUNK_OVERLAP
        
    def get_file_type(self, filename: str) -> Optional[str]:
        """Determine file type from filename"""
        extension = Path(filename).suffix.lower().lstrip('.')
        return extension if extension in self.SUPPORTED_TYPES else None
    
    def is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported"""
        return self.get_file_type(filename) is not None
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            raise
    
    def extract_text_from_pdf(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from PDF file"""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 is required for PDF processing. Install with: pip install PyPDF2")
        
        text = ""
        metadata = {"pages": 0, "page_texts": []}
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    text += page_text + "\n\n"
                    metadata["page_texts"].append({
                        "page": page_num,
                        "text": page_text,
                        "char_start": len(text) - len(page_text) - 2,
                        "char_end": len(text) - 2
                    })
                    
                # Extract PDF metadata
                if pdf_reader.metadata:
                    metadata.update({
                        "title": pdf_reader.metadata.get("/Title", ""),
                        "author": pdf_reader.metadata.get("/Author", ""),
                        "subject": pdf_reader.metadata.get("/Subject", ""),
                        "creator": pdf_reader.metadata.get("/Creator", "")
                    })
                    
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise
            
        return text.strip(), metadata
    
    def extract_text_from_docx(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from DOCX file"""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx is required for DOCX processing. Install with: pip install python-docx")
        
        try:
            doc = DocxDocument(file_path)
            text = ""
            metadata = {"paragraphs": 0}
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n\n"
                    metadata["paragraphs"] += 1
            
            # Extract document properties
            if doc.core_properties:
                metadata.update({
                    "title": doc.core_properties.title or "",
                    "author": doc.core_properties.author or "",
                    "subject": doc.core_properties.subject or "",
                    "created": doc.core_properties.created.isoformat() if doc.core_properties.created else None,
                    "modified": doc.core_properties.modified.isoformat() if doc.core_properties.modified else None
                })
                
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {e}")
            raise
            
        return text.strip(), metadata
    
    def extract_text_from_txt(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            metadata = {
                "lines": len(text.split('\n')),
                "encoding": "utf-8"
            }
            
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    text = file.read()
                metadata = {
                    "lines": len(text.split('\n')),
                    "encoding": "latin-1"
                }
            except Exception as e:
                logger.error(f"Error extracting text from TXT {file_path}: {e}")
                raise
        except Exception as e:
            logger.error(f"Error extracting text from TXT {file_path}: {e}")
            raise
            
        return text.strip(), metadata
    
    def extract_text_from_markdown(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from Markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            # Extract title from first heading
            title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
            title = title_match.group(1) if title_match else ""
            
            # Count headings
            headings = re.findall(r'^#+\s+(.+)$', text, re.MULTILINE)
            
            metadata = {
                "title": title,
                "headings_count": len(headings),
                "headings": headings[:10],  # First 10 headings
                "lines": len(text.split('\n'))
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from Markdown {file_path}: {e}")
            raise
            
        return text.strip(), metadata
    
    def extract_text_from_json(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from JSON file"""
        import json
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Convert JSON to readable text
            text = json.dumps(data, indent=2, ensure_ascii=False)
            
            metadata = {
                "json_keys": list(data.keys()) if isinstance(data, dict) else [],
                "json_type": type(data).__name__,
                "size": len(str(data))
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from JSON {file_path}: {e}")
            raise
            
        return text.strip(), metadata
    
    def extract_text(self, file_path: str, file_type: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text from file based on type"""
        extractors = {
            'pdf': self.extract_text_from_pdf,
            'docx': self.extract_text_from_docx,
            'txt': self.extract_text_from_txt,
            'md': self.extract_text_from_markdown,
            'json': self.extract_text_from_json
        }
        
        if file_type not in extractors:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return extractors[file_type](file_path)
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def create_chunks(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Split text into chunks with overlap"""
        if not text or len(text) < self.MIN_CHUNK_SIZE:
            return []
        
        chunks = []
        text = self.clean_text(text)
        
        # Split by sentences first to avoid breaking mid-sentence
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Create chunk
                chunk_data = {
                    "content": current_chunk.strip(),
                    "chunk_index": chunk_index,
                    "start_char": current_start,
                    "end_char": current_start + len(current_chunk),
                    "token_count": self.estimate_token_count(current_chunk),
                    "metadata": metadata or {}
                }
                chunks.append(chunk_data)
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
                current_start = current_start + len(current_chunk) - len(overlap_text) - len(sentence) - 1
                chunk_index += 1
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add final chunk if it has content
        if current_chunk.strip() and len(current_chunk.strip()) >= self.MIN_CHUNK_SIZE:
            chunk_data = {
                "content": current_chunk.strip(),
                "chunk_index": chunk_index,
                "start_char": current_start,
                "end_char": current_start + len(current_chunk),
                "token_count": self.estimate_token_count(current_chunk),
                "metadata": metadata or {}
            }
            chunks.append(chunk_data)
        
        return chunks
    
    def estimate_token_count(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Simple estimation: ~4 characters per token for Spanish/English
        return max(1, len(text) // 4)
    
    def process_document(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Process a document and return extracted data"""
        try:
            # Determine file type
            file_type = self.get_file_type(filename)
            if not file_type:
                raise ValueError(f"Unsupported file type for {filename}")
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_hash = self.calculate_file_hash(file_path)
            
            # Extract text
            text, metadata = self.extract_text(file_path, file_type)
            
            if not text:
                raise ValueError("No text could be extracted from the document")
            
            # Create chunks
            chunks = self.create_chunks(text, metadata)
            
            # Calculate total tokens
            total_tokens = sum(chunk["token_count"] for chunk in chunks)
            
            # Extract title if not in metadata
            title = metadata.get("title", "")
            if not title:
                # Use first line or filename as title
                first_line = text.split('\n')[0][:100]
                title = first_line if len(first_line) > 10 else Path(filename).stem
            
            return {
                "success": True,
                "file_type": file_type,
                "file_size": file_size,
                "content_hash": file_hash,
                "title": title,
                "text": text,
                "chunks": chunks,
                "total_chunks": len(chunks),
                "total_tokens": total_tokens,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_type": self.get_file_type(filename),
                "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
            }