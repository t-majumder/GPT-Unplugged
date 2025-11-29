import streamlit as st
import os
import re
import base64
import json
import tempfile
import html
from datetime import datetime
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter,TokenTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from helper_functions.helpers import get_base64_of_background_image, get_context, format_message_content, process_latex
import yaml

#------------------------------------------------------------------------------
# Load environment variables
load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')
background_image_path = "images/Theme.jpg"
background_image = get_base64_of_background_image(background_image_path)
# Loading the Config file
with open("config/hyperparams.yaml", "r") as f:
    config=yaml.safe_load(f)
PDFS_DIRECTORY = config['pdfs_directory']
DB_PATH = config['db_path']
EMBEDDING_MODEL = config['embedding_model']
CHUNK_SIZE = config['text_splitting']['chunk_size']
CHUNK_OVERLAP = config['text_splitting']['chunk_overlap']
ADD_START_INDEX = config['text_splitting']['add_start_index']
SEARCH_TYPE = config['retrieval']['search_type']
TOP_K_RESULTS = config['retrieval']['top_k']
MIN_SIMILARITY = config['retrieval'].get('min_similarity', 0.0)
MAX_FILE_SIZE_MB = config['file_upload_limits']['max_file_size_mb']
MAX_FILE_SIZE_BYTES = config['file_upload_limits']['max_file_size_bytes']
MAX_HISTORY_MESSAGES = config['chat_history']['max_history_messages']  # Number of messages to include in context (5 exchanges)

#------------------------------------------------------------------------------
# Model Configuration
AVAILABLE_MODELS = {
    "Qwen3 32B": "qwen/qwen3-32b",
    "Kimi K2 Instruct": "moonshotai/kimi-k2-instruct",
    "GPT-OSS 120B": "openai/gpt-oss-120b",
    "Llama 3.3 70B": "llama-3.3-70b-versatile"
}

# Prompt Template
PROMPT_TEMPLATE = '''
You are Helpful assistant named ResearchGPT. You are given the following extracted parts of a long document, chat history, and a question. Provide a conversational answer based on the context provided and previous conversation.
Basically, you are An expert in scientific research papers. Use the context to answer the question as accurately as possible.
Your knowledge is like an university professor with expertise in research papers. Who explains everything clearly. And if you are asked to do any math you always provide the mathematical equations in latex format.
Yor solution Generation Format: 
Step1: Give all the necessary definitions needed. 
Step2: Explain the solution step by step in detail. If mathematical equations are there then try to derive them step by step. As you are a high level professor.
Always format mathematical equations in LaTeX format.
Step3: Finally provide the final TLDR; summarized form of the answer.

Chat History: {chat_history}
Context: {context}
Question: {question}
Answer: '''
#------------------------------------------------------------------------------

# Page Configuration
st.set_page_config(page_title="Research GPT",page_icon="🔬",layout="wide",initial_sidebar_state="expanded")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# MathJax Support for LaTeX Rendering
st.markdown("""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML" async></script>
    <script type="text/x-mathjax-config">
        MathJax.Hub.Config({
            tex2jax: {
                inlineMath: [['$','$'], ['\\(','\\)']],
                displayMath: [['$$','$$'], ['\\[','\\]']],
                processEscapes: true
            },
            CommonHTML: { linebreaks: { automatic: true } },
            "HTML-CSS": { scale: 100 }
        });
    </script>
""", unsafe_allow_html=True)

#------------------------------------------------------------------------------
# Model Initialization
llm_instances = {}
for model_name, model_id in AVAILABLE_MODELS.items():
    llm_instances[model_name] = ChatGroq(model=model_id, api_key=groq_api_key)

#------------------------------------------------------------------------------
class VectorDB:
    def __init__(self, pdfs_directory=PDFS_DIRECTORY, db_path=DB_PATH):
        self.pdfs_directory = pdfs_directory
        self.db_path = db_path
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.faiss_db = None

    def process_pdfs(self, additional_pdf_paths=None):
        """Process PDFs including optional uploaded PDFs"""
        documents = self.load_pdfs()

        # Add uploaded PDFs if provided
        if additional_pdf_paths:
            for pdf_path in additional_pdf_paths:
                if os.path.exists(pdf_path):
                    loader = PDFPlumberLoader(pdf_path)
                    uploaded_docs = loader.load()
                    documents.extend(uploaded_docs)

        text_chunks = self.create_chunks(documents)
        self.faiss_db = FAISS.from_documents(text_chunks, self.embeddings)
        os.makedirs(self.db_path, exist_ok=True)
        self.faiss_db.save_local(self.db_path)
        return self.faiss_db

    def load_pdfs(self):
        """Load PDFs from the pdfs directory"""
        documents = []
        if not os.path.exists(self.pdfs_directory):
            os.makedirs(self.pdfs_directory)
            return documents

        for filename in os.listdir(self.pdfs_directory):
            if filename.endswith(".pdf"):
                file_path = os.path.join(self.pdfs_directory, filename)
                loader = PDFPlumberLoader(file_path)
                doc = loader.load()
                documents.extend(doc)
        return documents

    def create_chunks(self, documents):
        text_splitter = TokenTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            add_start_index=ADD_START_INDEX,
            encoding_name="cl100k_base"
        )
        return text_splitter.split_documents(documents)

    def get_retriever(self):
        if not self.faiss_db:
            if os.path.exists(os.path.join(self.db_path, 'index.faiss')):
                self.faiss_db = FAISS.load_local(self.db_path, self.embeddings, allow_dangerous_deserialization=True)
            else:
                self.faiss_db = self.process_pdfs()
        return self.faiss_db.as_retriever(search_type=SEARCH_TYPE, search_kwargs={"k": TOP_K_RESULTS})

vector_db = VectorDB()
#------------------------------------------------------------------------------
# Helpers for Chat Interface
def retrieve_docs(query):
    retriever = vector_db.get_retriever()

    # We need similarity scores → use similarity_search_with_score()
    if hasattr(vector_db.faiss_db, "similarity_search_with_score"):
        docs_with_scores = vector_db.faiss_db.similarity_search_with_score(query, TOP_K_RESULTS)

        # Filter based on threshold
        filtered_docs = [doc for doc, score in docs_with_scores if score >= MIN_SIMILARITY]

        # If no document meets threshold → return empty list
        if not filtered_docs:
            return []

        return filtered_docs

    # fallback for non-FAISS retrievers
    if hasattr(retriever, 'get_relevant_documents'):
        return retriever.get_relevant_documents(query)

    if hasattr(retriever, 'retrieve'):
        return retriever.retrieve(query)

    if hasattr(retriever, 'invoke'):
        return retriever.invoke(query)

    raise RuntimeError("Retriever does not support common retrieval methods.")


def format_chat_history(chat_history):
    if not chat_history:
        return "No previous conversation."

    formatted = []
    for message in chat_history[-MAX_HISTORY_MESSAGES:]:  # Use global parameter
        role = "User" if message['role'] == 'user' else "Assistant"
        formatted.append(f"{role}: {message['content']}")
    return "\n".join(formatted)


def answer_query(documents, model, query, chat_history):
    context = get_context(documents)
    history_text = format_chat_history(chat_history)
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | model
    # Use model.invoke to keep previous behaviour; many LangChain-wrapped LLMs return .content
    out = chain.invoke({
        "question": query,
        "context": context,
        "chat_history": history_text
    })
    # Some LLM wrappers return the content directly, others wrap it; handle both
    if hasattr(out, 'content'):
        return out.content
    return out

#------------------------------------------------------------------------------
# STYLING
# Custom CSS with combined styles and math support (unchanged visuals)
GLASS_CONTAINER_BG = "rgba(255, 255, 255, 0.1)"
st.markdown(f"""
    <style>

    .stApp {{
        background-image: url("data:image/jpg;base64,{background_image}");
        background-size: cover;
    }}
    .main .block-container {{
        max-width: 2000px;   /* set your custom width */
        padding-left: 2rem;
        padding-right: 2rem;
    }}
    
    .glass-container {{
        background: {GLASS_CONTAINER_BG};
        backdrop-filter: blur(10px);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 20px;
        margin: 10px 0;
    }}
    .chat-message {{
        padding: 1.5rem;
        margin: 8px 0;
        border-radius: 12px;
        display: flex;
    }}

    /* Assistant bubble - full width */
    .assistant-message {{
        background: rgba(0, 0, 0, 0.5);
        width: 100%;
        justify-content: flex-start;
        margin-bottom: 100px;
    }}

    /* User bubble - small and right-aligned */
    .user-message {{
        background: rgba(0, 0, 0, 0.5);
        max-width: 40%;        /* make user bubble compact */
        margin-left: auto;     /* pushes it to the right */
        text-align: right;
        float: right;
    }}
    .math-container {{
        background-color: rgba(64, 65, 79, 0.7);
        border-radius: 8px;
        padding: 1.2rem;
        margin: 1rem 0;
        overflow-x: auto;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    .inline-math {{
        background-color: rgba(64, 65, 79, 0.5);
        border-radius: 4px;
        padding: 0.2rem 0.4rem;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }}
    .bullet-glass-container {{
        background-color: rgba(64, 65, 79, 0.7);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    .message-content {{
        color: #FFFFFF;
    }}
    .sidebar .block-container {{
        background: rgba(45, 45, 45, 0.7);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 10px;
    }}
    section[data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.3);
        width: 300px;
    }}
    .uploadedFile {{
        background-color: rgba(68, 70, 84, 0.7);
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        border: 1px solid rgba(86, 88, 105, 0.7);
    }}
    /* Enhanced markdown styling */
    .chat-message p {{
        margin: 0;
        padding: 0;
    }}
    .chat-message strong {{
        font-weight: bold;
        color: rgb(255, 153, 0);
    }}
    .chat-message em {{
        font-style: italic;
        color: #ADD8E6;
    }}
    .chat-message code {{
        background: rgba(0, 0, 0, 0.3);
        padding: 2px 4px;
        border-radius: 4px;
        font-family: monospace;
    }}
    .has-jax {{
        font-size: 100%;
    }}
    /* Compact button styling */
    .stButton > button {{
        padding: 0.35rem 0.75rem;
        font-size: 0.85rem;
        height: 2rem;
        line-height: 1.2;
    }}
    div[data-testid="stFileUploader"] {{
        padding: 0.5rem 0;
    }}
    div[data-testid="stFileUploader"] > div {{
        padding: 0.5rem;
    }}
    
    /* Chat input styling - Large square box with black interior and orange glow */
    .stChatInput {{
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
    }}
    
    .stChatInput > div {{
        background: transparent !important;
        padding: 0 !important;
    }}
    
    div[data-testid="stChatInput"] {{
        background: transparent !important;
        padding: 2rem 0 !important;
        margin: 0 !important;
        transform: translateY(0px) !important;  
        position: fixed !important;
        z-index: -999 !important;
        bottom: 0 !important;
    }}
    
    div[data-testid="stChatInput"] > div {{
        background: transparent !important;
        padding: 0 !important;
    }}
    
    div[data-testid="stChatInput"] > div > div {{
        background: transparent !important;
    }}
    
    div[data-testid="stChatInput"] form {{
        background: #000000 !important;
        border: 2px solid rgba(255, 140, 60, 0.6) !important;
        border-radius: 0px !important;
        padding: 0 !important;
        box-shadow: 0 0 20px rgba(255, 140, 60, 0.5), 
                    0 0 40px rgba(255, 140, 60, 0.3),
                    0 0 60px rgba(255, 140, 60, 0.2) !important;
        min-height: 180px !important;

    }}
    
    div[data-testid="stChatInput"] form > div {{
        background: #000000 !important;
        padding: 2rem 2rem !important;
        min-height: 100px !important;
        display: flex !important;
        align-items: center !important;
        
    }}
    
    div[data-testid="stChatInput"] textarea {{
        background: rgba(80, 80, 80, 0.4) !important;
        color: #FFFFFF !important;
        font-size: 1.2rem !important;
        min-height: 140px !important;
        max-height: 400px !important;
        padding: 1rem !important;
        border: none !important;
        outline: none !important;
        resize: none !important;
        line-height: 1.6 !important;
    }}
    
    div[data-testid="stChatInput"] textarea::placeholder {{
        color: rgba(255, 255, 255, 0.4) !important;
    }}
    
    div[data-testid="stChatInput"] button {{
        background: transparent !important;
        color: rgba(255, 140, 60, 0.6) !important;
        border: none !important;
        padding: 1rem !important;
        margin: 0 !important;
        font-size: 1.2rem !important;
    }}
    
    div[data-testid="stChatInput"] button:hover {{
        color: rgba(255, 140, 60, 1) !important;
        background: rgba(255, 140, 60, 0.1) !important;
    }}
    
    /* Remove any outer container backgrounds */
    .stChatInput, 
    .stChatInput * {{
        box-sizing: border-box !important;
    }}
    
    div[data-testid="stBottom"] {{
        background: transparent !important;
    }}
    
    div[data-testid="stBottom"] > div {{
        background: transparent !important;
    }}
    </style>
""", unsafe_allow_html=True)

#------------------------------------------------------------------------------
# SESSION STATE INITIALIZATION

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'vector_db_status' not in st.session_state:
    st.session_state.vector_db_status = False
if 'uploaded_pdf_paths' not in st.session_state:
    st.session_state.uploaded_pdf_paths = []

#------------------------------------------------------------------------------
# MAIN APP INTERFACE
# Display header
st.markdown(
    """
    # 🔬 Research GPT  
    **Upload any PDFs to get started!**  
    """
)

# ------------------------------------------------------------------------------
# SIDEBAR
with st.sidebar:
    st.image("images/Theam.jpg", use_container_width=True)

    # Model Selection
    st.markdown("<h3 style='color: #ECECF1;'>🤖 Select Model</h3>", unsafe_allow_html=True)
    llm_choice = st.selectbox("Choose Language Model", list(AVAILABLE_MODELS.keys()), help="Select the AI model for analysis")

    # Get selected LLM instance
    llm = llm_instances[llm_choice]

    st.markdown("---")

    # PDF Upload Section
    st.markdown("<h3 style='color: #ECECF1;'> Upload PDFs</h3>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        f"Upload PDFs (Max {MAX_FILE_SIZE_MB}MB each)",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload multiple PDFs to add to the vector database temporarily. Will be removed on page refresh."
    )

    if uploaded_files:
        st.session_state.uploaded_pdf_paths = []
        valid_files = []

        for uploaded_file in uploaded_files:
            # Check file size using global parameter
            if uploaded_file.size > MAX_FILE_SIZE_BYTES:
                st.error(f"ERROR: {uploaded_file.name} exceeds {MAX_FILE_SIZE_MB}MB limit!")
            else:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    st.session_state.uploaded_pdf_paths.append(tmp_file.name)
                    valid_files.append(uploaded_file.name)

    # Vectorize PDFs Button
    if st.button("🔄 Vectorize PDFs", use_container_width=True):
        with st.status("Processing PDFs...", expanded=True) as status:
            vector_db.process_pdfs(st.session_state.uploaded_pdf_paths if st.session_state.uploaded_pdf_paths else None)
            st.session_state.vector_db_status = True
            status.update(label="PDFs vectorized successfully!", state="complete")

    st.markdown("---")

    # Clear chat button
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    # Display chat statistics
    if st.session_state.chat_history:
        msg_count = len([m for m in st.session_state.chat_history if m['role'] == 'user'])
        st.markdown(f"<p style='color: #ECECF1; font-size: 0.9rem;'>💬 Messages: {msg_count}</p>", unsafe_allow_html=True)


#--------------------------------------------------------------
# # CHAT INTERFACE
for message in st.session_state.chat_history:
    with st.container():
        if message['role'] == 'assistant':
            # Keep the assistant content as-is (math delimiters preserved)
            processed_content = process_latex(message['content'])
            formatted_content = format_message_content(processed_content)
        else:
            # Keep user messages as is (escaped for safety)
            formatted_content = html.escape(message['content'])

        st.markdown(f"""
            <div class="chat-message {message['role']}-message">
                <div class="message-content">
                    {formatted_content}
                </div>
            </div>
        """, unsafe_allow_html=True)
        # Trigger MathJax typesetting after each assistant message
        st.markdown(
            """
            <script>
            if (window.MathJax) {
                MathJax.Hub.Queue(['Typeset', MathJax.Hub]);
            }
            </script>
            """,
            unsafe_allow_html=True
        )

#----------------------------------------------------------------
# QUERY INPUT & PROCESSING
user_query = st.chat_input("Ask any query...")

if user_query:
    if os.path.exists(os.path.join(vector_db.db_path, 'index.faiss')):
        st.session_state.chat_history.append({"role": "user", "content": user_query})

        with st.status("Generating response...", expanded=True) as status:
            try:
                retrieved_docs = retrieve_docs(user_query)

                # Generate response with chat history
                previous_history = st.session_state.chat_history[:-1]
                response = answer_query(
                    documents=retrieved_docs,
                    model=llm,
                    query=user_query,
                    chat_history=previous_history
                )
                st.session_state.chat_history.append({"role": "assistant", "content": response})

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                status.update(label="Error generating response", state="error")

        st.rerun()
    else:
        st.error("Please vectorize the PDFs first using the 'Vectorize PDFs' button in the sidebar.")
