
# DocuVerse: AI-Powered Document Processing, Classification & Conversational Search

**DocuVerse** is an advanced AI-powered document processing and management system designed to automate the entire lifecycle of document ingestion, extraction, classification, and structured knowledge generation. By leveraging cutting-edge tools like PaddleOCR, GPT-based LLMs, and a Hybrid Retrieval-Augmented Generation (RAG) architecture, DocuVerse provides efficient and accurate document management and querying.

## Table of Contents

1. Overview
2. System Architecture
3. Modules

   * 1. Document Upload & Ingestion Module
   * 2. OCR Module — PaddleOCR
   * 3. LLM Integration Module
   * 4. Document Classification & Storage Module
   * 5. Advanced Question and Answering Module with Hybrid Search & RAG Architecture
4. AI-Powered Workflow
5. How to Run
6. Dependencies
7. Future Enhancements


## Overview
DocuVerse automates the processing, classification, and querying of documents, transforming unstructured data into structured knowledge. By using state-of-the-art OCR and Large Language Models (LLMs), it extracts and formats key document information, making it easy for users to query and retrieve relevant insights.

### Key Features:
- **Document Upload & Ingestion**: Accepts multiple document types (PDF, images) for processing.
- **OCR with PaddleOCR**: Extracts raw text from documents.
- **LLM Integration**: Extracts key metadata, structures content, classifies documents, and formats tables.
- **Document Classification**: Automatically classifies documents into predefined categories and stores them.
- **Conversational Search**: Provides a sophisticated search interface that uses Hybrid Retrieval-Augmented Generation (RAG) to answer user queries based on document content.

---

## System Architecture
The system architecture of DocuVerse is modular, scalable, and consists of five key components:
1. **Document Upload & Ingestion Module**: Manages the upload process.
2. **OCR Module**: Extracts text from documents.
3. **LLM Integration Module**: Processes extracted text for analysis and content generation.
4. **Document Classification & Storage**: Organizes and stores documents based on classifications.
5. **Hybrid Search & Q&A**: A robust question-answering module using semantic and metadata search.

Each of these components can be scaled independently, allowing for easy updates or modifications.

---

## Modules

### 1. Document Upload & Ingestion Module

#### Purpose:
This module facilitates the upload of document files (PDFs and images) and prepares them for OCR processing.

#### Functionality:
- Accepts document uploads through an API or CLI interface.
- Temporarily stores the documents before passing them for OCR processing.
  
#### Input:
- PDF or image files (supports batch uploads).

#### Output:
- Raw document passed to the OCR module for text extraction.

---

### 2. OCR Module — PaddleOCR

#### Purpose:
The OCR module uses **PaddleOCR** to extract the raw text and layout information from uploaded documents.

#### Tool:
- **PaddleOCR** (Python library)

#### Functionality:
- Extracts text from each page of the document.
- Merges the text into a single string or keeps it page-wise for detailed processing.
- Optionally extracts layout and bounding box information for later use in document rendering.

#### Output:
- Raw extracted text from the document.

---

### 3. LLM Integration Module

#### Purpose:
Once the raw text is extracted by OCR, this module sends the data to the LLM for further processing to extract metadata, reformat content, and classify the document.

#### Functionality:
- **Extract Metadata**: Key fields like "Sponsor," "Protocol Number," and "CRA Name."
- **Generate Formatted Content**: Converts the document text into clean and readable prose.
- **Format Tables**: Converts tabular data into structured JSON format.
- **Classify Documents**: Classifies the document into predefined categories (e.g., "Site Initiation Visit Follow-Up Letter").

#### Output:
```json
{
  "metadata": {
    "Sponsor": "ABC Pharma",
    "Protocol Number": "XYZ-001",
    "CRA Name": "Jane Smith"
  },
  "formatted_content": "Dear Dr. John Doe, ...",
  "formatted_tables": [
    {
      "Table Title": "Visit Summary",
      "Content": [
        { "Day": "1", "Task": "Site Tour" },
        { "Day": "2", "Task": "Protocol Review" }
      ]
    }
  ],
  "entity": "SITE INITIATION VISIT FOLLOW-UP LETTER"
}
````

---

### 4. Document Classification & Storage Module

#### Purpose:

This module ensures that the classified document is stored correctly and organized based on its classification type.

#### Functionality:

* **Entity Mapping**: Resolves document type to a folder name using a predefined dictionary (e.g., "SITE INITIATION VISIT" → "SIV").
* **File Storage**: Saves the original file in an organized folder structure and stores metadata and formatted content in a MongoDB database.

#### Output:

* Document metadata and content saved in MongoDB:

```json
{
  "filename": "SIV_FollowUp_Letter_001.pdf",
  "entity": "SITE INITIATION VISIT FOLLOW-UP LETTER",
  "folder_name": "MVR_SIV_FU_LETTER",
  "metadata": { ... },
  "formatted_content": "...",
  "formatted_tables": [...],
  "upload_date": "2025-09-02T12:34:56Z"
}
```

---

### 5. Advanced Question and Answering Module with Hybrid Search & RAG Architecture

#### Purpose:

This module enables users to ask questions about documents and receive precise, contextually relevant answers through a **Hybrid Retrieval-Augmented Generation (RAG)** architecture.

#### Workflow:

1. **Query Preprocessing & Intent Recognition**: Uses an LLM (e.g., GPT-4) to understand the user’s query, correct typos, and extract key entities (e.g., protocol number, CRA name).
2. **Dual-Pronged Retrieval Strategy**:

   * **Metadata Search**: Uses fuzzy matching on the MongoDB metadata to find documents even with slight errors in the query.
   * **Semantic Content Search**: Converts the query into vector embeddings and searches for the most relevant document content in a vector store.
3. **Context Augmentation & Final Prompting**: Combines results from both searches and forms a comprehensive, context-aware prompt for the LLM.
4. **LLM-Powered Response**: The LLM synthesizes the results into a human-like answer.

#### Output Example:

```text
"In the Site Initiation Visit Follow-Up Letter for protocol PR-567 (filename: SIV_FollowUp_Letter_001.pdf), which was handled by CRA John Smith, the visit summary included a 'Site Tour' on Day 1 and a 'Protocol Review' on Day 2."
```

---

## AI-Powered Workflow

### Efficient Use of AI:

DocuVerse harnesses advanced AI in several key areas:

* **OCR**: PaddleOCR is used to extract text with high accuracy, even from noisy document images.
* **LLM Integration**: GPT-4 or similar models are employed to process and understand document content, extracting relevant metadata and restructuring text for human readability.
* **Hybrid Search & RAG**: The innovative combination of structured metadata search and semantic content search (via vector embeddings) allows for highly efficient and contextually accurate responses to user queries.

The system is designed to handle slight variations in user input and produce relevant, structured information in real-time.

---

## How to Run

To get **DocuVerse** up and running, follow these steps to start both the backend and frontend services.

### 1. Clone the Repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/your-repository/DocuVerse.git
cd DocuVerse
```

### 2. Install Dependencies

Install the required Python dependencies for both backend and frontend:

```bash
pip install -r requirements.txt
```

### 3. Run the Backend (API)

Start the backend service, which handles document processing and data storage. Execute the following command:

```bash
python main.py
```

This will initialize the backend server, which listens for document uploads, OCR processing, and AI-driven document querying.

### 4. Run the Frontend (Streamlit UI)

Once the backend is running, you can start the frontend, which provides a user-friendly interface for interacting with the system. Use Streamlit to run the UI:

```bash
streamlit run app.py
```

This will open the Streamlit web interface in your browser, where you can upload documents and query the system using the conversational interface.

### 5. Upload Documents

In the Streamlit interface, you'll be able to upload one or more documents (PDFs or images). The backend will process these documents


, extracting text via PaddleOCR and passing the data through the LLM for further structuring and classification.

### 6. Query the Documents

Once documents are processed and stored, you can use the conversational interface to ask questions about the documents. The system will use the Hybrid Retrieval-Augmented Generation (RAG) architecture to search both structured metadata and content to provide contextually relevant answers.

---

## Dependencies

* Python 3.7+
* PaddleOCR
* OpenAI GPT (for LLM integration)
* Streamlit (for frontend UI)
* MongoDB (for document storage)

---

## Future Enhancements

* **Support for More Document Types**: Extend the system to handle additional document formats, such as Word and Excel.
* **AI Model Fine-Tuning**: Fine-tune the LLM to handle more specific document categories and improve context understanding.
* **Real-Time Collaboration**: Implement features for multiple users to collaborate on document processing and querying in real-time.

---
