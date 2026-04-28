
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter


loader = DirectoryLoader('./kb', glob="*.md", loader_cls=TextLoader)
docs = loader.load()

