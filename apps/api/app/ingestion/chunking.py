"""Chunking per spec Section 6: RecursiveCharacterTextSplitter, 1,000 token
chunks, 150 token overlap. Length is measured in actual tokens (via tiktoken)
rather than characters, so chunk boundaries line up with what the embedding
model and downstream LLMs actually see.
"""

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE_TOKENS = 1000
CHUNK_OVERLAP_TOKENS = 150

_encoding = tiktoken.get_encoding("cl100k_base")


def _token_count(text: str) -> int:
    return len(_encoding.encode(text))


_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE_TOKENS,
    chunk_overlap=CHUNK_OVERLAP_TOKENS,
    length_function=_token_count,
)


def chunk_text(text: str) -> list[str]:
    chunks = _splitter.split_text(text)
    return [c for c in chunks if c.strip()]
