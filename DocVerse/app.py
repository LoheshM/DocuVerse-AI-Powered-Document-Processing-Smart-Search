import streamlit as st
import requests
import json
import os
from datetime import datetime
import pandas as pd

# API configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Document Processing System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .stButton button {
        width: 100%;
    }
    .json-container {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        max-height: 400px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def upload_files(files):
    """Upload files to the API"""
    try:
        files_data = [("files", (file.name, file, file.type)) for file in files]
        response = requests.post(f"{API_BASE_URL}/upload/", files=files_data)
        return response.json()
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}

def search_documents(field, value, exact_match):
    """Search documents using the API"""
    try:
        params = {"field": field, "value": value, "exact": exact_match}
        response = requests.get(f"{API_BASE_URL}/search/", params=params)
        return response.json()
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}

def check_api_health():
    """Check if API is available"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def display_llm_response(response_data):
    """Display LLM response in a user-friendly format"""
    if not response_data:
        return
    
    st.subheader("📊 LLM Processing Results")
    
    # Metadata section
    with st.expander("📋 Extracted Metadata", expanded=True):
        if response_data.get("metadata"):
            metadata_df = pd.DataFrame.from_dict(response_data["metadata"], orient='index', columns=['Value'])
            st.dataframe(metadata_df, use_container_width=True)
        else:
            st.info("No metadata extracted")
    
    # Formatted content section
    with st.expander("📝 Formatted Content", expanded=False):
        formatted_content = response_data.get("formatted_content", "")
        if formatted_content:
            st.text_area("Content", formatted_content, height=200, disabled=True)
        else:
            st.info("No formatted content available")
    
    # Tables section
    with st.expander("📊 Extracted Tables", expanded=False):
        tables = response_data.get("formatted_tables", [])
        if tables:
            for i, table in enumerate(tables):
                st.write(f"**Table {i+1}: {table.get('Table Title', 'Untitled')}**")
                if table.get("Content"):
                    try:
                        table_df = pd.DataFrame(table["Content"])
                        st.dataframe(table_df, use_container_width=True)
                    except:
                        st.json(table)
                st.divider()
        else:
            st.info("No tables extracted")
    
    # Entity classification
    with st.expander("🏷️ Document Classification", expanded=False):
        entity = response_data.get("entity", "UNKNOWN")
        st.info(f"**Document Type:** {entity}")
    
    # Raw JSON response
    with st.expander("🔧 Raw JSON Response", expanded=False):
        st.markdown('<div class="json-container">', unsafe_allow_html=True)
        st.json(response_data)
        st.markdown('</div>', unsafe_allow_html=True)

# Main app
def main():
    st.markdown('<h1 class="main-header">Document Processing System</h1>', unsafe_allow_html=True)
    
    # Check API connection
    if not check_api_health():
        st.error("⚠️ API server is not available. Please make sure the backend server is running on localhost:8000")
        st.stop()
    
    # Sidebar
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("Go to", ["Upload Documents", "Search Documents", "About"])
    
    if app_mode == "Upload Documents":
        render_upload_page()
    elif app_mode == "Search Documents":
        render_search_page()
    elif app_mode == "About":
        render_about_page()

def render_upload_page():
    st.header("Upload Documents")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose PDF or image files", 
        type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.info(f"Selected {len(uploaded_files)} file(s) for processing")
        
        # Display file details
        with st.expander("File Details"):
            file_data = []
            for file in uploaded_files:
                file_data.append({
                    "Name": file.name,
                    "Type": file.type,
                    "Size": f"{len(file.getvalue()) / 1024:.2f} KB"
                })
            st.table(file_data)
        
        # Process button
        if st.button("Process Documents", type="primary"):
            with st.spinner("Processing documents..."):
                result = upload_files(uploaded_files)
                
                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success(f"Processed {len(result.get('results', []))} documents")
                    
                    # Display results
                    for i, res in enumerate(result.get('results', [])):
                        if res['status'] == 'success':
                            st.markdown(f"""
                            <div class="success-box">
                                <strong>✅ {res['filename']}</strong><br>
                                Entity: {res['entity']}<br>
                                Processed at: {res['processing_time']}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Display LLM response details
                            display_llm_response(res.get('llm_response', {}))
                            
                        else:
                            st.markdown(f"""
                            <div class="error-box">
                                <strong>❌ {res['filename']}</strong><br>
                                Error: {res['error']}
                            </div>
                            """, unsafe_allow_html=True)

def render_search_page():
    st.header("Search Documents")
    
    # Search form
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_field = st.selectbox(
            "Search Field",
            options=["Sponsor", "Protocol Number", "CRA Name", "Site Number", 
                    "Visit Type", "Investigator Name", "Date of Letter"]
        )
    
    with col2:
        search_value = st.text_input("Search Value")
    
    exact_match = st.checkbox("Exact match", value=True)
    
    if st.button("Search", type="primary") and search_value:
        with st.spinner("Searching..."):
            result = search_documents(search_field, search_value, exact_match)
            
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                search_results = result.get('results', [])
                st.success(f"Found {len(search_results)} matching documents")
                
                if search_results:
                    # Display results in a table
                    df_data = []
                    # for res in search_results:
                    #     df_data.append({
                    #         "Filename": res['filename'],
                    #         "Entity": res['entity'],
                    #         "Folder": res['folder_name']
                    #     })
                    
                    # df = pd.DataFrame(df_data)
                    # st.write(df)
                    for i, res in enumerate(search_results):
                        st.code(f"""
                    Filename: {res['filename']}
                    Entity: {res['entity']}
                    Folder: {res['folder_name']}
                    """, language="text")

                    
                    # Show detailed view with LLM response
                    for i, res in enumerate(search_results):
                        with st.expander(f"Details: {res['filename']}"):
                            st.subheader("Metadata")
                            st.json(res.get('metadata', {}))
                            
                            # Display LLM response if available
                            if 'formatted_content' in res or 'formatted_tables' in res:
                                display_llm_response({
                                    "metadata": res.get('metadata', {}),
                                    "formatted_content": res.get('formatted_content', ''),
                                    "formatted_tables": res.get('formatted_tables', []),
                                    "entity": res.get('entity', '')
                                })
                else:
                    st.info("No documents found matching your criteria")

def render_about_page():
    st.header("About Document Processing System")
    
    st.markdown("""
    This application processes clinical trial documents using AI-powered extraction and classification.
    
    ### Features:
    - **Document Upload**: Upload PDF or image files for processing
    - **OCR Extraction**: Extract text from documents using PaddleOCR
    - **AI Processing**: Use OpenAI GPT to extract metadata, format content, and classify documents
    - **Intelligent Storage**: Automatically organize documents based on classification
    - **Metadata Search**: Search documents by any metadata field
    
    ### Supported Document Types:
    The system can classify these document types:
    - Pre-study site visit documents
    - Site initiation visit documents
    - Monitoring visit documents
    - Close out visit documents
    - Various reports and letters
    
    ### How it works:
    1. Upload your documents
    2. The system extracts text using OCR
    3. AI processes the text to extract metadata and classify the document
    4. Documents are automatically organized in the appropriate folder
    5. You can search for documents using any extracted metadata field
    """)
    
    st.info("""
    **Note**: This is a demonstration system. For production use, ensure proper 
    data security measures are implemented, especially when handling sensitive documents.
    """)

if __name__ == "__main__":
    main()