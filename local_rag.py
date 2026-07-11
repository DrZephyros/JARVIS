import os
import logging
import faiss
import numpy as np
import google.generativeai as genai
from pypdf import PdfReader
import docx2txt

logger = logging.getLogger("jarvis.local_rag")

def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start+chunk_size])
        start += chunk_size - overlap
    return chunks

class LocalFolderAnalyzer:
    def __init__(self, folder_path, gemini_api_key):
        self.folder_path = folder_path
        genai.configure(api_key=gemini_api_key)
        self.index = None
        self.texts = []
        self.model = genai.GenerativeModel("gemini-3.5-flash")

    def build_index(self):
        logger.info(f"Building local index for folder: {self.folder_path}")
        documents = []
        for file in os.listdir(self.folder_path):
            file_path = os.path.join(self.folder_path, file)
            if not os.path.isfile(file_path):
                continue
                
            ext = os.path.splitext(file)[1].lower()
            text = ""
            try:
                if ext == '.txt':
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                elif ext == '.pdf':
                    reader = PdfReader(file_path)
                    text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
                elif ext == '.docx':
                    text = docx2txt.process(file_path)
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
                
            if text.strip():
                documents.append(text)
                
        if not documents:
            logger.warning("No valid documents found to index.")
            return False
            
        # Chunking
        for doc in documents:
            self.texts.extend(chunk_text(doc))
            
        if not self.texts:
            return False
            
        try:
            # Embeddings
            embeddings_result = genai.embed_content(
                model="models/text-embedding-004",
                content=self.texts,
                task_type="retrieval_document"
            )
            embeddings = np.array(embeddings_result['embedding'], dtype='float32')
            
            # FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings)
            
            logger.info("Index built successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to create embeddings or FAISS index: {e}")
            return False

    def query(self, question):
        if self.index is None:
            return "Sir, I have not indexed this folder yet."
            
        try:
            # Embed question
            response = genai.embed_content(
                model="models/text-embedding-004",
                content=question,
                task_type="retrieval_query"
            )
            q_emb = np.array([response['embedding']], dtype='float32')
            
            # Search
            k = 5
            distances, indices = self.index.search(q_emb, k)
            
            context = "\n\n".join([self.texts[i] for i in indices[0] if i < len(self.texts)])
            
            prompt = f"Answer the following question using ONLY the provided context.\n\nContext:\n{context}\n\nQuestion: {question}"
            
            chat_response = self.model.generate_content(prompt)
            return chat_response.text.strip()
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return "I encountered an error while searching the folder, Sir."
