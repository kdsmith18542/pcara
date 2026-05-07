try:
    import chromadb
except ImportError:
    print("ChromaDB not available, RAG features will be limited")
    chromadb = None
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import os
from typing import Optional, List
from models import Repository
from dotenv import load_dotenv

load_dotenv()

class RAGService:
    def __init__(self):
        # Initialize ChromaDB client
        if chromadb:
            try:
                self.chroma_client = chromadb.HttpClient(host="chromadb", port=8000)
            except Exception as e:
                print(f"Failed to connect to ChromaDB: {e}")
                self.chroma_client = None
        else:
            self.chroma_client = None
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize Gemini API
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        # Get or create collections
        if self.chroma_client:
            try:
                self.public_docs_collection = self.chroma_client.get_or_create_collection(
                    name="public_docs",
                    metadata={"description": "Public documentation and knowledge base"}
                )
                
                self.code_collection = self.chroma_client.get_or_create_collection(
                    name="code_analysis",
                    metadata={"description": "Code analysis results and insights"}
                )
            except Exception as e:
                print(f"Failed to create ChromaDB collections: {e}")
                self.public_docs_collection = None
                self.code_collection = None
        else:
            self.public_docs_collection = None
            self.code_collection = None
    
    async def query(
        self,
        query: str,
        repository: Optional[Repository] = None,
        user_id: int = None
    ) -> str:
        """Process a RAG query and return a response"""
        
        # Generate embedding for the query
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # Search relevant documents
        relevant_docs = []
        
        if self.public_docs_collection:
            try:
                # Search public documentation
                public_results = self.public_docs_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=5
                )
                if public_results['documents']:
                    relevant_docs.extend(public_results['documents'][0])
            except Exception as e:
                print(f"Error searching public docs: {e}")
        
        # If repository is specified, search code-specific knowledge
        if repository and self.code_collection:
            try:
                code_results = self.code_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=3,
                    where={"repository_id": repository.id}
                )
                if code_results['documents']:
                    relevant_docs.extend(code_results['documents'][0])
            except Exception as e:
                print(f"Error searching code collection: {e}")
        
        # Construct prompt with context
        context = "\n\n".join(relevant_docs)
        prompt = f"""
Based on the following context, please answer the user's question about code analysis and refactoring:

Context:
{context}

User Question: {query}

Please provide a helpful and accurate response based on the context provided. If the context doesn't contain enough information to answer the question, please say so.
"""
        
        try:
            # Generate response using Gemini
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Sorry, I encountered an error while processing your query: {str(e)}"
    
    def add_document(
        self,
        content: str,
        metadata: dict,
        collection_name: str = "public_docs"
    ):
        """Add a document to the knowledge base"""
        
        # Generate embedding
        embedding = self.embedding_model.encode([content]).tolist()[0]
        
        # Get collection
        collection = self.chroma_client.get_or_create_collection(name=collection_name)
        
        # Add document
        collection.add(
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
            ids=[f"{collection_name}_{len(collection.get()['ids'])}"]
        )
    
    def add_code_analysis_result(
        self,
        repository_id: int,
        analysis_result: dict,
        file_path: str,
        language: str
    ):
        """Add code analysis results to the knowledge base"""
        
        # Create searchable content from analysis results
        content = f"""
File: {file_path}
Language: {language}
Analysis Results: {analysis_result}
"""
        
        metadata = {
            "repository_id": repository_id,
            "file_path": file_path,
            "language": language,
            "type": "code_analysis"
        }
        
        self.add_document(content, metadata, "code_analysis")