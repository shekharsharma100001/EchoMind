import numpy as np
import google.generativeai as genai
from utils.gemini_helper import setup_gemini

# In-memory store for currently active sessions.
# In a true scalable app, this would be a Vector DB like Chroma or Pinecone.
# Key: file_name | Value: { 'chunks': [...], 'embeddings': np.ndarray }
vector_store = {}

def chunk_text(text, chunk_size=1000):
    """Splits a large string into smaller chunks of character length."""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def create_embeddings(file_name, text_content):
    """Generates embeddings for the text and stores them in memory."""
    setup_gemini()
    
    chunks = chunk_text(text_content)
    if not chunks:
        return
    
    # We use Google's foundational embedding model mapping properly to standard key schemas
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=chunks,
        task_type="retrieval_document"
    )
    
    embeddings = np.array(result['embedding'])
    
    # Normalize embeddings for fast cosine similarity dot product
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    # Save to our in-memory store
    vector_store[file_name] = {
        'chunks': chunks,
        'embeddings': embeddings
    }
    return True

def query_rag(file_name, question, language="Default"):
    """Embeds the question, retrieves top chunks, and asks the LLM."""
    setup_gemini()
    
    store = vector_store.get(file_name)
    if not store:
        return "Sorry, I lost the context of this conversation. Please restart the analysis."
    
    # Embed the query
    q_result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=question,
        task_type="retrieval_query"
    )
    
    q_embed = np.array(q_result['embedding'])
    q_embed = q_embed / np.linalg.norm(q_embed)
    
    # Cosine Similarity (Dot Product on normalized vectors)
    similarities = np.dot(store['embeddings'], q_embed)
    
    # Get top 3 most relevant chunks
    top_k = 3
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    context_chunks = [store['chunks'][i] for i in top_indices]
    context_str = "\n---\n".join(context_chunks)
    
    # Construct Synthesis Prompt
    prompt = f"""
    You are an AI assistant answering questions based strictly on the provided conversation context.
    
    Context:
    {context_str}
    
    User Question: {question}
    
    Answer concisely based only on the context provided above.
    """
    
    if language and language != "Default":
        prompt += f"\nGenerate the response in {language} language."
    
    # Generate response
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    
    return response.text
