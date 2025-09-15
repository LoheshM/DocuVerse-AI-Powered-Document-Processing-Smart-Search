import os
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "document_processor"
COLLECTION_NAME = "documents"

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'

# File Storage Configuration
BASE_STORAGE_PATH = r"C:\Users\Lohesh\Documents\DataReveal\TextExtraction\documents"
TEMP_UPLOAD_DIR = "temp_uploads"

# Entity to Folder Mapping
ENTITIES = {
    "PRE-STUDY SITE VISIT FOLLOW-UP LETTER": "MVR_PSSV_FU_LETTER",
    "PRE-STUDY SITE VISIT CONFIRMATION LETTER": "MVR_PSSV_CONF_LETTER",
    "SITE INITIATION VISIT FOLLOW-UP LETTER": "MVR_SIV_FU_LETTER",
    "SITE INITIATION VISIT CONFIRMATION LETTER": "MVR_SIV_CONF_LETTER",
    "CLOSE OUT VISIT CONFIRMATION LETTER": "MVR_COV_CONF_LETTER",
    "CLOSE OUT VISIT FOLLOW-UP LETTER": "MVR_COV_FU_LETTER",
    "MONITORING VISIT FOLLOW-UP LETTER": "MVR_IMV_FU_LETTER",
    "MONITORING VISIT CONFIRMATION LETTER": "MVR_IMV_CONF_LETTER",
    "CLOSE OUT VISIT REPORT": "MVR_COV_REPORT",
    "MONITORING VISIT REPORT": "MVR_IMV_REPORT",
    "PRE-STUDY SITE VISIT REPORT": "MVR_PSSV_REPORT",
    "SITE INITIATION VISIT (SIV) REPORT": "MVR_SIV_REPORT",
    "SITE INITIATION VISIT REPORT": "MVR_SIV_REPORT"
}

LLM_PROMPT = """
Your task is to analyze OCR text from a clinical trial document, which may contain formatting errors and artifacts from the scanning process. You must identify and correct for common layout issues, such as multi-column headers where values and labels are misaligned in the text stream. Note that document structures vary: some may contain only tables, only text, or a mix of both. Your final output must be a single, valid JSON object with no extraneous text or explanations. This JSON object must contain exactly these keys: metadata, formatted_content, formatted_tables, entity.


METADATA RULES:
- Extract all fields listed below. If you cannot find the information for a specific field in the document, you MUST include the key and use the string "N/A" as its value.
- Fields to extract: Sponsor, Protocol Number, CRA Name, Site Number, Visit Type, Visit Start Date, Visit End Date, Investigator Name, Date of Letter, Date of Previous Visit, Number of Days.
- You may also add other relevant metadata fields if they are clearly stated in the document.
- Infer the 'Site Number' from the prefix of the subject IDs (e.g., "03409" from "03409-001").
- Calculate the 'Number of Days' for the visit duration.
- Convert ALL values to STRINGS.
- Format all dates as "dd-mm-yyyy".
- Analyze the document to correctly associate labels with their values, even when the OCR splits them. For example, OCR text like "(ELEVATE) STML-ELA- \n Protocol Number \n 0222" should be correctly interpreted as "Protocol Number": "(ELEVATE) STML-ELA-0222".


FORMATTED_CONTENT:
- Provide clean, human-readable text from the document's non-tabular sections.
- Reconstruct the document's flow, merging text from all pages.
- Remove OCR artifacts, formatting issues, and repetitive page headers or footers.
- Use paragraphs and bullet points for readability.
- If the document contains no prose or text outside of tables, this field can be an empty string.
- CRITICAL: Do NOT include the detailed, row-by-row content of tables in this section. That data belongs exclusively in the 'formatted_tables' section.


FORMATTED_TABLES:
- Extract all tabular data into a structured JSON array of objects, where each object represents a single row.
- Consolidate tables that span multiple pages into a single data structure.
- For the main follow-up issues table, parse the complex multi-line "Issue" column into the following separate keys within each row's object: 'ID', 'DueDate', 'Category', 'TriggeredBy', 'Issue', 'Description', and 'Action'.
- If no tables are found, return an empty array [].


ENTITY:
- Classify the document using exactly one of the following options:
  PRE-STUDY SITE VISIT FOLLOW-UP LETTER, PRE-STUDY SITE VISIT CONFIRMATION LETTER, SITE INITIATION VISIT FOLLOW-UP LETTER, SITE INITIATION VISIT CONFIRMATION LETTER, CLOSE OUT VISIT CONFIRMATION LETTER, CLOSE OUT VISIT FOLLOW-UP LETTER, MONITORING VISIT FOLLOW-UP LETTER, MONITORING VISIT CONFIRMATION LETTER, CLOSE OUT VISIT REPORT, MONITORING VISIT REPORT, PRE-STUDY SITE VISIT REPORT, SITE INITIATION VISIT (SIV) REPORT, SITE INITIATION VISIT REPORT


DOCUMENT TEXT:
{ocr_text}


RETURN ONLY VALID JSON, NO OTHER TEXT:
"""

INTENT_PROMPT = """
You are an expert at parsing user queries for a document search system.
From the user's query, extract two things:
1.  "filters": A JSON object of metadata fields to filter documents. The keys must be the exact field names from this list: ["Sponsor", "Protocol Number", "CRA Name", "Site Number", "Visit Type", "Investigator Name", "Date of Letter", "entity"].
2.  "semantic_query": A concise string that represents the core question to be answered from the document's content.

User Query: "{query}"

Return ONLY a valid JSON object with "filters" and "semantic_query" keys. If no filters are found, return an empty "filters" object.
"""

RAG_PROMPT = """
You are a helpful AI assistant. Answer the user's question based ONLY on the provided context below.
If the context does not contain the answer, state that you cannot find the information in the provided documents.
Cite the source document filename(s) in your answer.

User Question: "{query}"

Context:
---
{context}
---
"""