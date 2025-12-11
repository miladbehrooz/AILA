import re

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    SentenceTransformersTokenTextSplitter,
)

from backend.embeddings import EmbeddingModelSingleton

embedding_model = EmbeddingModelSingleton()


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Split arbitrary text into fixed-size segments with optional overlap.

    Args:
        text (str): Source text to segment.
        chunk_size (int, optional): Target character length per chunk. Defaults to 500.
        chunk_overlap (int, optional): Number of overlapping tokens between chunks.

    Returns:
        list[str]: Ordered list of text chunks.
    """
    character_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n"],
        chunk_size=chunk_size,
        chunk_overlap=0,
    )
    text_split_by_characters = character_splitter.split_text(text)

    chunks_by_tokens = []

    if embedding_model.provider.startswith("huggingface"):
        token_splitter = SentenceTransformersTokenTextSplitter(
            chunk_overlap=chunk_overlap,
            tokens_per_chunk=embedding_model.max_input_length,
            model_name=embedding_model.model_name,
        )

        for section in text_split_by_characters:
            chunks_by_tokens.extend(token_splitter.split_text(section))

    else:

        chunks_by_tokens = text_split_by_characters

    return chunks_by_tokens


def chunk_article(text: str, min_length: int, max_length: int) -> list[str]:
    """Split long-form articles by sentences while enforcing length limits.

    Args:
        text (str): Article text to chunk.
        min_length (int): Minimum number of characters per chunk.
        max_length (int): Maximum number of characters per chunk.

    Returns:
        list[str]: Chunks that respect the configured length boundaries.
    """
    sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s", text)

    extracts = []
    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence + " "
        else:
            if len(current_chunk) >= min_length:
                extracts.append(current_chunk.strip())
            current_chunk = sentence + " "

    if len(current_chunk) >= min_length:
        extracts.append(current_chunk.strip())

    return extracts
