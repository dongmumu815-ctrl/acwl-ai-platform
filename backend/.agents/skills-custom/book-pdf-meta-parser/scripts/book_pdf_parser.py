import requests
import json
import argparse
import sys

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


def parse_pdf_metadata(pdf_url: str):
    """Extract metadata from PDF without poppler dependency"""
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        pdf_bytes = response.content
    except Exception as e:
        return {"error": f"Failed to download PDF: {str(e)}"}

    # Try pdfplumber first (better for text extraction)
    if pdfplumber:
        try:
            import io
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                metadata = pdf.metadata or {}
                
                # Extract text from first 3 pages
                text_content = ""
                for i, page in enumerate(pdf.pages[:3]):
                    try:
                        text_content += page.extract_text() or ""
                    except Exception:
                        pass
                
                result = {
                    "status": "success",
                    "metadata": {
                        "title": metadata.get("Title", ""),
                        "author": metadata.get("Author", ""),
                        "subject": metadata.get("Subject", ""),
                        "creator": metadata.get("Creator", ""),
                        "producer": metadata.get("Producer", ""),
                        "pages": len(pdf.pages)
                    },
                    "extracted_text": text_content[:500]  # First 500 chars
                }
                return result
        except Exception as e:
            return {"error": f"pdfplumber extraction failed: {str(e)}"}

    # Fallback to PyPDF2
    if PdfReader:
        try:
            import io
            reader = PdfReader(io.BytesIO(pdf_bytes))
            metadata = reader.metadata or {}
            
            # Extract text from first 3 pages
            text_content = ""
            for page in reader.pages[:3]:
                try:
                    text_content += page.extract_text() or ""
                except Exception:
                    pass
            
            result = {
                "status": "success",
                "metadata": {
                    "title": metadata.get("/Title", ""),
                    "author": metadata.get("/Author", ""),
                    "subject": metadata.get("/Subject", ""),
                    "creator": metadata.get("/Creator", ""),
                    "producer": metadata.get("/Producer", ""),
                    "pages": len(reader.pages)
                },
                "extracted_text": text_content[:500]
            }
            return result
        except Exception as e:
            return {"error": f"PyPDF2 extraction failed: {str(e)}"}

    return {"error": "No PDF library available. Install pdfplumber or PyPDF2."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Book PDF metadata parser")
    parser.add_argument("url", nargs="?", help="PDF URL")
    parser.add_argument("--url", dest="url_opt", help="PDF URL")
    args = parser.parse_args()

    url = args.url_opt or args.url
    if not url:
        print(json.dumps({"error": "Missing PDF URL"}, ensure_ascii=False))
        sys.exit(1)
    else:
        result = parse_pdf_metadata(url)
        print(json.dumps(result, ensure_ascii=False))
