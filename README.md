# CyberRAG: Cyber Advisory Search Engine 🛡️

CyberRAG is a Retrieval-Augmented Generation (RAG) application designed to provide intelligent answers to cyber threat intelligence questions. It ingests cybersecurity advisories (PDFs), indexes them using vector embeddings, and uses a Large Language Model (LLM) to generate comprehensive, citation-backed briefings for security analysts.

## 🚀 Features

-   **Semantic Search:** Finds relevant documents based on meaning, not just keywords, using Weaviate and Ollama embeddings.
-   **AI-Powered Answers:** Generates professional threat briefings using Google Gemini (Flash 2.5).
-   **Citation Tracking:** Every claim in the generated answer is cited with the source document.
-   **Dark Mode UI:** A professional, "Spotlight Search" style interface built with Streamlit.
-   **Progress Tracking:** Real-time visibility into the search and generation pipeline.
-   **PDF Ingestion:** Automated pipeline to parse, chunk, and index PDF advisories.

## 🛠️ Architecture

1.  **Ingestion:** PDFs are parsed using `pypdf`, chunked, and embedded using `Ollama` (model: `embeddinggemma`).
2.  **Storage:** Embeddings and text chunks are stored in a local `Weaviate` vector database.
3.  **Retrieval:** User queries are embedded and matched against the database using vector similarity search.
4.  **Generation:** Retrieved context is sent to `Google Gemini`, which acts as a Senior Threat Intelligence Analyst to answer the user's question.

## Architecture
<img width="875" height="643" alt="Architecture" src="https://github.com/user-attachments/assets/3b8d7d5c-549e-4d1c-b9e3-fcc165bac8b0" />

## 📋 Prerequisites

Before running the project, ensure you have the following installed:

1.  **Python 3.12+**
2.  **Docker** (for running Weaviate)
3.  **Ollama** (for local embeddings)
    -   Install Ollama from [ollama.com](https://ollama.com).
    -   Pull the embedding model: `ollama pull embeddinggemma`

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd CyberRAG
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Start Weaviate:**
    You need a running Weaviate instance. If you have a `docker-compose.yml` file (typical for Weaviate), run:
    ```bash
    docker-compose up -d
    ```
    *Note: Ensure Weaviate is accessible at `localhost:8080` (GRPC on 50051).*

## ⚙️ Configuration

Create a `.env` file in the root directory with the following variables:

```env
# LLM & Embedding
OLLAMA_HOST=http://localhost:11434
EMBEDDING_MODEL=embeddinggemma
SUMMARIZE_MODEL=gemini-2.5-flash
GEMMA_API_KEY=your_google_gemini_api_key_here

# Vector Database (Weaviate)
WEAVIATE_HOST=localhost
WEAVIATE_API_KEY=supersecret_api_key_123
WEAVIATE_COLLECTION=Advisory
TOP_K_DEFAULT=25
```

> **Note:** You can get a Google Gemini API key from [Google AI Studio](https://aistudio.google.com/).

## 🏃 Usage

### 1. Ingest Data
Place your PDF files in the `data/cisa_pdfs/` directory. Then run the ingestion script to parse and index them:

```bash
python ingestion_process.py
```
*This will read PDFs, generate embeddings, and populate the Weaviate database.*

### 2. Run the Application
Start the Streamlit web interface:

```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501`.

## 📂 Project Structure

```
CyberRAG/
├── app.py                  # Main Streamlit application entry point
├── ingestion_process.py    # Script to ingest PDFs into Weaviate
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
├── data/
│   └── cisa_pdfs/          # Directory for input PDF files
├── logs/                   # Application logs
└── src/                    # Source code modules
    ├── answerer.py         # LLM generation logic (Google Gemini)
    ├── config.py           # Configuration management
    ├── embedder.py         # Embedding generation (Ollama)
    ├── logger.py           # Logging and progress tracking
    └── search.py           # Weaviate search logic
```

## 🛡️ License

This project is licensed under the Apache License 2.0.  
See the LICENSE file for details.
© 2025 Mohan Kumar Manivannan
