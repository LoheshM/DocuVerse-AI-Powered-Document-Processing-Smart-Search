import streamlit as st
import requests
import json
import os
from datetime import datetime
import pandas as pd

# API configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(page_title="Document Chatbot", page_icon="🤖", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #1f77b4; text-align: center; }
    .stChatMessage { background-color: #f0f2f6; border-radius: 10px; padding: 15px; }
</style>
""", unsafe_allow_html=True)

# Helper functions
def post_chat_message(query: str):
    """Send a message to the chatbot API."""
    try:
        response = requests.post(f"{API_BASE_URL}/chat/", json={"query": query})
        if response.status_code == 200:
            return response.json()
        else:
            return {"answer": f"Error: Received status code {response.status_code}", "sources": []}
    except Exception as e:
        return {"answer": f"Connection error: {str(e)}", "sources": []}

def check_api_health():
    """Check if API is available."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        return response.status_code == 200
    except:
        return False

# Main app
def main():
    st.markdown('<h1 class="main-header">Document Intelligence Chatbot 🤖</h1>', unsafe_allow_html=True)

    if not check_api_health():
        st.error("⚠️ API server is not available. Please start the backend server.")
        st.stop()
    
    # Sidebar for upload (can be moved from your old code)
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("Go to", ["Chat with Documents", "Upload Documents"])

    if app_mode == "Chat with Documents":
        render_chat_page()
    elif app_mode == "Upload Documents":
        render_upload_page() # You can copy this function from your old app.py
    elif app_mode == "About":
        render_about_page()

def render_chat_page():
    st.header("Ask me anything about your documents!")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What is your question?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner("Thinking..."):
                response = post_chat_message(prompt)
                full_response = response.get("answer", "No answer found.")
                sources = response.get("sources", [])
                
                message_placeholder.markdown(full_response)
                
                if sources:
                    with st.expander("📚 View Sources"):
                        for source in sources:
                            st.success(f"**File:** {source['filename']} (Score: {source['score']:.2f})")
                            st.json(source['metadata'])


        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
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