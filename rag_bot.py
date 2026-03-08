import os
import argparse
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

PROMPT_TEMPLATE = """
You are an expert insurance underwriter assistant. 
Your goal is to answer questions about claims coverage, specifically regarding what parts of an incident should be accepted or rejected based on historical precedent.

Answer the question based strictly on the following context consisting of past claims and underwriter decisions. 
If the answer cannot be confidently derived from the provided context, state that you don't have enough historical precedent to make a ruling.

Do not make up coverage rules. Base your reasoning directly on the 'Underwriter Reasoning' and 'Accepted/Rejected Parts' found in the context.

Context (Past Claims):
{context}

---
Question: {query}
"""

def get_rag_chain():
    # 1. Connect to the existing vector database
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    db = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    
    # 2. Setup the Retriever (fetch top 4 most similar past claims)
    retriever = db.as_retriever(search_kwargs={"k": 4})
    
    # 3. Setup the Prompt and the LLM
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) # Using 4o-mini for speed and cost efficiency
    
    # 4. Construct the LangChain execution chain
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "query": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain

def run_query(query_text):
    if not os.path.exists("chroma_db"):
        print("Error: Vector database not found. Please run 'build_index.py' first.")
        return

    print(f"\n--- Question ---\n{query_text}\n")
    print("--- Underwriter's Assessment ---")
    
    chain = get_rag_chain()
    # Stream the output for a better UX, or just use invoke
    response = chain.invoke(query_text)
    print(response)
    print("\n-------------------------------\n")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "paste_your_key_here":
        print("ERROR: Please set a valid OPENAI_API_KEY in your .env file.")
        exit(1)
        
    parser = argparse.ArgumentParser(description="Query the Insurance Underwriting Knowledge Base")
    parser.add_argument("query", type=str, nargs="?", help="The policy/claim question you want to ask.")
    args = parser.parse_args()

    if args.query:
        run_query(args.query)
    else:
        print("Interactive mode started. Type 'exit' or 'quit' to stop.")
        while True:
            user_input = input("\nEnter your claim question: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            if user_input.strip():
                run_query(user_input)
