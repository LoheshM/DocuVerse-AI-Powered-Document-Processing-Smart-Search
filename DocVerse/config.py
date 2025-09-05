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

# LLM Prompt
# LLM_PROMPT = """
# You are a document understanding system.

# You will be given raw OCR output extracted from a document. The OCR data may include:
# - Paragraphs, headings, and scattered content across multiple pages.
# - Tables that may be well-structured or fragmented due to OCR quality.
# - Fields that may appear randomly in the document (not necessarily inside tables).

# Your tasks:

# 1. **Extract all meaningful fields** from the document and return them under a `"metadata"` key. These include, but are not limited to:
#    - Sponsor
#    - Protocol Number
#    - CRA Name
#    - Site Number
#    - Visit Type
#    - Visit Start Date
#    - Visit End Date
#    - Investigator Name
#    - Date of Letter
#    - Previous Visit Date
#    - Number of Days
#    - Any additional fields that seem relevant

#    ⚠️ Fields may appear anywhere in the content. Extract them thoughtfully.

# 2. **Reconstruct and format the full content** of the document in a clean, readable way. Merge content from all pages, removing noise and redundancies. Return this as `"formatted_content"`.

# 3. **Extract any tables**, format them clearly using Markdown-style or structured JSON, and return under `"formatted_tables"`.

# 4. **Classify the document** by matching its content with one of the following entity types and return the matched entity string exactly under the `"entity"` key:

#    - PRE-STUDY SITE VISIT FOLLOW-UP LETTER
#    - PRE-STUDY SITE VISIT CONFIRMATION LETTER
#    - SITE INITIATION VISIT FOLLOW-UP LETTER
#    - SITE INITIATION VISIT CONFIRMATION LETTER
#    - CLOSE OUT VISIT CONFIRMATION LETTER
#    - CLOSE OUT VISIT FOLLOW-UP LETTER
#    - MONITORING VISIT FOLLOW-UP LETTER
#    - MONITORING VISIT CONFIRMATION LETTER
#    - CLOSE OUT VISIT REPORT
#    - MONITORING VISIT REPORT
#    - PRE-STUDY SITE VISIT REPORT
#    - SITE INITIATION VISIT (SIV) REPORT
#    - SITE INITIATION VISIT REPORT

# """
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