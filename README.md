# ClauseGuard - AI-Powered Contract Risk Analyzer

ClauseGuard is a hybrid AI-powered system designed to analyze, classify, and compare legal contracts. By leveraging a local sentence embedding model for semantic diffing and the Gemini API for natural language risk assessment, the application helps identify compliance flags, calculate clause-level risk scores, and generate negotiation talking points.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture and Data Flow](#system-architecture-and-data-flow)
- [Core Components](#core-components)
- [Technical Stack](#technical-stack)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Deployment and Setup](#deployment-and-setup)

---

## Overview

ClauseGuard segments legal agreements (PDF and DOCX) into distinct clauses, detects the contract type, scores each clause based on risk categories (Financial, Legal, Compliance, Enforceability, and Termination), suggests mitigation alternatives, and highlights negotiation talking points. It also offers semantic document comparison to align and analyze risk changes between original and revised contracts.

---

## System Architecture and Data Flow

```
Upload (PDF or DOCX)
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ parser.py                                              │
│ PyMuPDF or python-docx -> Text Cleaning                │
│ Regex Sentence Segmentation                            │
│ Output: List of parsed clauses                         │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ classifier.py                                          │
│ Gemini 2.0 Flash (Category Detection on snippet)       │
│ Output: Contract Type and Confidence Score             │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ analyzer.py                                            │
│ Gemini 2.0 Flash (Batch Processing, size = 4)          │
│ Outputs: risk_score, risk_level, risk_category,        │
│          safer_alternative, negotiation_point          │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ comparator.py (For Contract Comparison)                │
│ Local Model: sentence-transformers/all-MiniLM-L6-v2    │
│ Cosine Similarity Mapping + Gemini Risk Explanations   │
│ Outputs: delta_score, matched change sets              │
└────────────────────────────────────────────────────────┘
        │
        ▼
JSON Response -> React Frontend Client
```

---

## Core Components

### 1. Document Parsing and Segmentation
* **Extraction:** The backend handles PDF text extraction using PyMuPDF and DOCX extraction using python-docx.
* **Cleaning:** A preprocessing pass collapses redundant white spaces and normalizes newlines.
* **Segmentation:** Clauses are extracted using a rule-based regex tokenizer designed for contract clause boundaries. Abbreviations (such as Co., Ltd., Corp., Inc., e.g., and i.e.) are filtered to prevent false splits. Only segments exceeding 30 characters are processed.
* **Batch Capping:** Analysis is capped at the top 20 clauses to optimize rate-limiting thresholds.

### 2. Contract Type Classification
* **Model:** The classification engine queries Gemini 2.0 Flash with a structured schema returning the classified category and confidence score.
* **Candidate Labels:** NDA, Employment Agreement, SaaS / Software License, Vendor Agreement, Partnership Agreement, Commercial Lease, Consulting Agreement, Share Purchase Agreement, and General Commercial Contract.
* **Fallback Mode:** In case of API limits or connectivity issues, a regex-based keyword matching algorithm acts as a local fallback.

### 3. Risk Analysis Engine
* **Concurrent Execution:** Clauses are processed in parallel batches of 4 using asyncio.
* **Analysis Metadata:** Each clause is graded on a risk score (0-100), risk level (Low, Medium, High, Critical), risk category, explanation, safer alternative rewrite, and counterparty negotiation point.
* **Summarization:** A separate API call summarizes the contract into exactly five plain-English bullet points.

### 4. Hybrid Semantic Comparison
* **Local Embedding Matching:** The comparison engine generates embeddings for the original and revised clause lists using a local `all-MiniLM-L6-v2` transformer model. It calculates a pairwise cosine similarity matrix.
* **Clause Diffing:** Match pairs are grouped by similarity:
  * **Unchanged:** Similarity >= 0.98
  * **Modified:** 0.55 <= Similarity < 0.98
  * **Added:** New clauses with similarity < 0.55
  * **Deleted:** Old clauses with similarity < 0.55
* **LLM Explanation:** For modified clauses, Gemini 2.0 Flash is invoked asynchronously to describe the exact business risk impact of the change.

---

## Technical Stack

### Backend
* **FastAPI and Uvicorn:** High-performance asynchronous routing and server execution.
* **PyMuPDF (fitz):** PDF document parsing.
* **python-docx:** DOCX document parsing.
* **google-genai:** Asynchronous interactions with Gemini 2.0 Flash.
* **sentence-transformers:** Local embeddings and similarity calculations.
* **Pydantic v2:** Input and output schema validation.

### Frontend
* **React and TypeScript:** Single-page application UI development.
* **Vite:** Asset compilation and hot-reloading dev server.
* **Tailwind CSS:** Utility-first interface styling.
* **Recharts:** Data visualization for risk analytics.
* **jsPDF:** Client-side document generation.

---

## API Reference

### `POST /upload`
* **Request:** `multipart/form-data` containing the file parameter (PDF or DOCX).
* **Response:** Returns JSON object containing the document metadata, contract classification details, overall risk scores, five-bullet summary, and the list of analyzed clauses.

### `POST /compare`
* **Request:** `multipart/form-data` containing file1 (original version) and file2 (negotiated version).
* **Response:** Returns JSON object containing the overall risk delta score, a change summary message, and the list of categorized semantic modifications.

### `GET /health`
* **Response:** `{"status": "healthy"}`

---

## Project Structure

```
clauseGuard/
├── backend/
│   ├── main.py           # FastAPI server interface and CORS configuration
│   ├── parser.py         # Text cleaning and regex clause segmentation
│   ├── classifier.py     # Gemini-based contract category classifier
│   ├── analyzer.py       # Gemini-based risk scoring and summarizing
│   ├── comparator.py     # Local SentenceTransformer embedding match + Gemini explanations
│   ├── .dockerignore
│   └── Dockerfile
├── frontend/
│   ├── src/              # React TSX pages and components
│   ├── .dockerignore
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── SETUP.md
```

---

## Deployment and Setup

### Prerequisites
* Docker and Docker Compose
* Google Gemini API Key

### Deploy with Docker
1. Clone the repository and navigate to the project root.
2. Copy `.env.example` to `.env` and fill in your `GEMINI_API_KEY`.
3. Build and launch the containers:
   ```bash
   docker compose up --build -d
   ```
4. Access the web client at `http://localhost:5173` and the API documentation at `http://localhost:8000/docs`.

---

## License

This project is licensed under the MIT License. See LICENSE for details.
