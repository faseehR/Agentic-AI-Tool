import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import CharacterTextSplitter

def build_vector_store():
    
    loader = DirectoryLoader('./', glob="*.md", loader_cls=TextLoader)
    docs = loader.load()
    
    
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(docs)
    
    
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore

def retrieve_kb_context(query, vectorstore):
    
    docs = vectorstore.similarity_search(query, k=2)
    context = "\n".join([d.page_content for d in docs])
    sources = list(set([d.metadata['source'] for d in docs]))
    return context, sources