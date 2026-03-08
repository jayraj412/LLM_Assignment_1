import os
import pandas as pd
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Load environment variables (API Key)
load_dotenv()

# Initialize OpenAI Embeddings model
# Requires OPENAI_API_KEY to be set in the environment or .env
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Path to the synthetic data and where to store the vector DB
DATA_PATH = "synthetic_underwriting_claims.csv"
CHROMA_PATH = "chroma_db"

def load_data(file_path):
    """Loads claims from CSV and formats them into LangChain Document objects."""
    print(f"Loading data from {file_path}...")
    df = pd.read_csv(file_path)
    
    documents = []
    for _, row in df.iterrows():
        # Construct a rich text chunk so the LLM has all context
        page_content = (
            f"Claim ID: {row['Claim_ID']}\n"
            f"Industry: {row['Industry']}\n"
            f"Policy Type: {row['Policy_Type']}\n"
            f"Incident Description: {row['Incident_Description']}\n"
            f"Accepted Parts: {row['Accepted_Parts']}\n"
            f"Rejected Parts: {row['Rejected_Parts']}\n"
            f"Expert Decision: {row['Expert_Decision']}\n"
            f"Underwriter Reasoning: {row['Underwriter_Reasoning']}"
        )
        
        # Attach metadata for filtering if needed later
        metadata = {
            "claim_id": row['Claim_ID'],
            "policy_type": row['Policy_Type'],
            "industry": row['Industry']
        }
        
        doc = Document(page_content=page_content, metadata=metadata)
        documents.append(doc)
        
    print(f"Loaded {len(documents)} claims.")
    return documents

def build_vector_db():
    """Embeds documents and stores them in a local ChromaDB instance."""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Source data file '{DATA_PATH}' not found. Please ensure the synthetic generation script ran successfully.")
        
    docs = load_data(DATA_PATH)
    
    print(f"Building/Updating Chroma database at '{CHROMA_PATH}'...")
    # This will create or update the chroma_db folder locally
    Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    print("Database indexing complete.")

if __name__ == "__main__":
    try:
        if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "paste_your_key_here":
            print("ERROR: Please set a valid OPENAI_API_KEY in your .env file before building the index.")
        else:
            build_vector_db()
    except Exception as e:
        print(f"An error occurred: {e}")
