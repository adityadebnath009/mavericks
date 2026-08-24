import os
import requests
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGULATORY_DIR = PROJECT_ROOT / "data" / "regulatory"

# Corrected official PDF documents for the RAG system
PDF_DOWNLOADS = {
    "fao_safety_at_sea_manual.pdf": "http://www.fao.org/3/ca5772en/ca5772en.pdf", # Corrected URL code
    "fao_small_vessel_inspection.pdf": "https://www.fao.org/3/i0625e/i0625e.pdf"
}

def download_pdfs():
    """Download official maritime safety and inspection guidelines in PDF format for RAG ingestion."""
    REGULATORY_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Initiating PDF collection for Grounded RAG agent...")
    print("==================================================")
    
    for filename, url in PDF_DOWNLOADS.items():
        dest_path = REGULATORY_DIR / filename
        print(f"Downloading: {filename}")
        print(f"Source URL:  {url}")
        
        try:
            # Set a standard user-agent header to avoid scraping blocks
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"Successfully saved to: {dest_path.relative_to(PROJECT_ROOT)}")
            print(f"File size: {dest_path.stat().st_size / 1024 / 1024:.2f} MB\n")
            
        except Exception as e:
            print(f"Error downloading {filename}: {e}\n")
            
    print("==================================================")
    print("PDF collection complete.")

if __name__ == "__main__":
    download_pdfs()
