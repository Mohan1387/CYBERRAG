"""
Ingestion Process Script

This script handles the ingestion of PDF documents into a Weaviate vector database.
It performs the following steps:
1. Connects to a local Weaviate instance.
2. Ensures the 'Advisory' collection exists with the correct schema.
3. Iterates through PDF files in the 'data/cisa_pdfs' directory.
4. Extracts text and metadata (IOCs) from each PDF.
5. Chunks the text and generates embeddings using Ollama.
6. Inserts the chunks and metadata into Weaviate.
7. Renames processed files to avoid re-ingestion.
"""

import pypdf
import os
import re
from itertools import accumulate
import hashlib
import unicodedata
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Property, DataType, Configure
import ollama

from src.config import EMBEDDING_MODEL, OLLAMA_HOST
from src.config import WEAVIATE_HOST, WEAVIATE_API_KEY, WEAVIATE_COLLECTION

# ==========================================
# Configuration & Connection
# ==========================================

# Weaviate Connection Settings
HOST = WEAVIATE_HOST
API_KEY = WEAVIATE_API_KEY

# Initialize Weaviate Client
client = weaviate.connect_to_custom(
    http_host=HOST, http_port=9090, http_secure=False,
    grpc_host=HOST, grpc_port=50051, grpc_secure=False,
    auth_credentials=Auth.api_key(API_KEY),
)

print("Weaviate Connected:", client.is_ready())

# ==========================================
# Schema Definition
# ==========================================

# Define Weaviate collection name
collection_name = WEAVIATE_COLLECTION

# Check if collection exists, create if not
if collection_name not in client.collections.list_all():
    print(f"Creating collection: {collection_name}")
    client.collections.create(
        name=collection_name,
        properties=[
            # Core doc fields
            Property(name="text",     data_type=DataType.TEXT, description="The chunk of text from the document"),
            Property(name="doc_name", data_type=DataType.TEXT, description="Original filename"),
            Property(name="doc_id",   data_type=DataType.TEXT, description="SHA256 hash of the document content"),
            # Aggregated IOC list (optional, keep if you like having a flat view)
            Property(name="iocs",     data_type=DataType.TEXT_ARRAY, description="All extracted IOCs flattened"),
            # Per-type IOC fields (matching IOC_PATTERNS keys)
            Property(name="cves",     data_type=DataType.TEXT_ARRAY),
            Property(name="tids",     data_type=DataType.TEXT_ARRAY),
            Property(name="ipv4",     data_type=DataType.TEXT_ARRAY),
            Property(name="ipv6",     data_type=DataType.TEXT_ARRAY),
            Property(name="hashes",   data_type=DataType.TEXT_ARRAY),
            Property(name="emails",   data_type=DataType.TEXT_ARRAY),
            Property(name="urls",     data_type=DataType.TEXT_ARRAY),
            Property(name="domains",  data_type=DataType.TEXT_ARRAY),
            Property(name="paths",    data_type=DataType.TEXT_ARRAY),
            Property(name="ports",    data_type=DataType.TEXT_ARRAY),
        ],
        # Using external embeddings (Ollama), so disable built-in vectorizer
        vectorizer_config=None,
    )

# Get the collection object for operations
documents = client.collections.get(collection_name)


# Ollama API to generate embeddings
OLLAMA_API_URL = OLLAMA_HOST
EMBEDDING_MODEL = EMBEDDING_MODEL

ollama_client = ollama.Client(host=OLLAMA_API_URL)

# Path to pdf files
directory_path = r'data/cisa_pdfs'
# Get a list of all filenames in that directory
filenames = os.listdir(directory_path)


def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file and return it along with the file name."""
    reader = pypdf.PdfReader(pdf_file)
    text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
    
    # Get the file name without path
    pdf_name = os.path.basename(pdf_file)
    
    return pdf_name, text


def chunk_text_by_sentence_and_paragraph(text, max_chunk_size=1024):
    """
    Split text into chunks based on sentences and double newlines,
    keeping each chunk under max_chunk_size tokens/words approx.
    """

    # First, split by double newlines to separate paragraphs
    paragraphs = re.split(r'\n\s*\n', text.strip())
    chunks = []

    for para in paragraphs:
        # Split paragraph into sentences
        sentences = re.split(r'(?<=[.!?])\s+', para.strip())
        current_chunk = []

        for sentence in sentences:
            if len(" ".join(current_chunk + [sentence]).split()) <= max_chunk_size:
                current_chunk.append(sentence)
            else:
                # Finalize current chunk and start new one
                chunks.append(" ".join(current_chunk).strip())
                current_chunk = [sentence]

        # Add remaining sentence(s)
        if current_chunk:
            chunks.append(" ".join(current_chunk).strip())

    return [c for c in chunks if c]


# ==========================================
# IOC Extraction Logic
# ==========================================

# Simple IOC extraction (IPv4, CVE, ATT&CK, hashes, domains, urls, emails)
import re
from typing import Dict, List

def deobfuscate(text: str) -> str:
    """
    Deobfuscate common IOC patterns (e.g., hxxp -> http, [.] -> .).
    Useful for extracting IOCs from security advisories that obfuscate them.
    """
    t = text
    t = re.sub(r"hxxp(s?)://", r"http\1://", t, flags=re.I)
    t = t.replace("[.]", ".").replace("(.)", ".").replace("{.}", ".")
    return t

# Regex patterns for various Indicators of Compromise (IOCs)
IOC_PATTERNS = {
    "cves": re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I),
    "tids": re.compile(r"\bT\d{4}(?:\.\d{1,3})?\b", re.I),
    "ipv4": re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
    "ipv6": re.compile(r"\b(?:[A-F0-9]{0,4}:){2,7}[A-F0-9]{0,4}\b", re.I),
    "hashes": re.compile(r"\b[a-f0-9]{32}\b|\b[a-f0-9]{40}\b|\b[a-f0-9]{64}\b", re.I),
    "emails": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "urls": re.compile(r"\bhttps?://[^\s<>\]]+\b", re.I),
    "domains": re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b"),
    "paths": re.compile(r"(?:[A-Za-z]:\\(?:[^\\\r\n]+\\)*[^\\\r\n]+)|(?:/(?:[^/\s]+/)*[^/\s]+)"),
    "ports": re.compile(r"\bport\s?(\d{1,5})\b", re.I),
}

def extract_iocs(raw_text: str) -> Dict[str, List[str]]:
    """
    Extract IOC metadata from text using regex patterns.
    Returns a dictionary of normalized lists per IOC type.
    """
    text = deobfuscate(raw_text)
    md = {}
    for key, rx in IOC_PATTERNS.items():
        if key == "ports":
            vals = [m.group(1) for m in rx.finditer(text)]
        else:
            vals = rx.findall(text)
            if isinstance(vals, list) and vals and isinstance(vals[0], tuple):
                vals = [v[0] for v in vals]
        
        # Normalize and deduplicate
        if key in ("cves", "tids", "hashes", "emails", "urls", "domains", "paths"):
            vals = list({v.strip() for v in vals})
        elif key in ("ipv4", "ipv6"):
            vals = list({v.strip().lower() for v in vals})
        elif key == "ports":
            vals = list({str(int(v)) for v in vals if 0 < int(v) <= 65535})
        md[key] = sorted(vals)
    
    # Ensure ipv4 and ipv6 are lists (redundant check but safe)
    md["ipv4"] = list(set(md["ipv4"]))
    md["ipv6"] = list(set(md["ipv6"]))
    return md

def extract_iocs_from_text(q: str) -> Dict[str, list]:
    """Quick IOC grab for queries (same patterns)."""
    return extract_iocs(q)


# List of prefixes to remove
prefixes = ["/attack.mitre.org", "https://attack.mitre.org"]

def remove_prefix_matches(values, prefix_list):
    return [
        v for v in values
        if not any(v.startswith(pref) for pref in prefix_list)
    ]


def get_ollama_embedding(text, client):

    embedding = client.embeddings(
                                    model=EMBEDDING_MODEL,
                                    prompt=text
                                   )
    return embedding['embedding'] if embedding else None


# ==========================================
# Main Ingestion Loop
# ==========================================

filecount = 0
for i, filename in enumerate(filenames):

    # Get the name part (e.g., 'data') and extension (e.g., '.pdf')
    name_part, extension_part = os.path.splitext(filename)
    
    # Skip hidden files or already processed files
    if filename.startswith('.') or name_part.endswith('_processed'):
        print(f'Skipping hidden/processed item: {filename}')
        continue
    else:    
        # Construct the full path to the file
        full_path = os.path.join(directory_path, filename)
    
        # 1. Extract Text
        pdf_name, extracted_text = extract_text_from_pdf(full_path)
        
        # 2. Generate Document ID (Hash)
        doc_id = hashlib.sha256(extracted_text.encode('utf-8')).hexdigest()
        
        # 3. Extract IOCs
        extracted_iocs = extract_iocs_from_text(extracted_text)
        # Flatten all IOCs into a single list for the 'iocs' field
        iocslst = sum(extracted_iocs.values(), []) 
    
        # 4. Chunk Text
        chunks = chunk_text_by_sentence_and_paragraph(extracted_text, max_chunk_size=512)
    
        # 5. Embed and Insert Chunks
        for chunk in chunks:
            # Generate embedding for the chunk
            vector = get_ollama_embedding(chunk, ollama_client)
     
            # Insert into Weaviate
            documents.data.insert(
                        properties={
                            "text": chunk, # Store the chunk text, not the full document text
                            "doc_name": pdf_name,
                            "doc_id": doc_id,
                            "iocs": iocslst,
                            # Store all IOCs for the document in every chunk (metadata)
                            "cves": extracted_iocs.get("cves", []),
                            "tids": extracted_iocs.get("tids", []),
                            "ipv4": extracted_iocs.get("ipv4", []),
                            "ipv6": extracted_iocs.get("ipv6", []),
                            "hashes": extracted_iocs.get("hashes", []),
                            "emails": extracted_iocs.get("emails", []),
                            "urls": extracted_iocs.get("urls", []),
                            "domains": extracted_iocs.get("domains", []),
                            "paths": extracted_iocs.get("paths", []),
                            "ports": extracted_iocs.get("ports", []),
                        },
                        vector=vector)
        filecount += 1
        print(f"Processed file {pdf_name}, Total files processed: {filecount}")

        # 6. Rename File to mark as processed
        try:
            new_filename = f"{name_part}_processed{extension_part}"
            new_full_path = os.path.join(directory_path, new_filename)
            os.rename(full_path, new_full_path)
            print(f'  Renamed to: {new_filename}\n')
        except Exception as e:
            print(f'  Error renaming {filename}: {e}\n')

client.close()





































    