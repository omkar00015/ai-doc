"""
Smart text chunker for document comparison.
Splits documents into semantic chunks (paragraphs/sections) while preserving
section boundaries and context for meaningful comparison.
"""

import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def chunk_text(text: str, max_chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    """
    Split document text into semantic chunks for embedding and comparison.

    Strategy:
    1. First try to split on section headers / double newlines (semantic boundaries)
    2. If chunks are too large, split further on single newlines / sentence boundaries
    3. Each chunk gets an index and metadata for alignment

    Args:
        text: Full document text
        max_chunk_size: Maximum characters per chunk
        overlap: Character overlap between adjacent chunks for context continuity

    Returns:
        List of dicts: [{"index": int, "text": str, "start_char": int, "end_char": int}]
    """
    if not text or not text.strip():
        return []

    # Normalize whitespace but preserve paragraph structure
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\t', ' ', text)
    text = re.sub(r' +', ' ', text)

    # Step 1: Split on section-level boundaries (double newlines, headers, horizontal rules)
    section_pattern = r'\n\s*\n'
    raw_sections = re.split(section_pattern, text)

    # Filter empty sections
    raw_sections = [s.strip() for s in raw_sections if s.strip()]

    if not raw_sections:
        return []

    # Step 2: Further split large sections into smaller chunks
    chunks = []
    char_offset = 0

    for section in raw_sections:
        if len(section) <= max_chunk_size:
            chunks.append({
                "index": len(chunks),
                "text": section,
                "start_char": char_offset,
                "end_char": char_offset + len(section),
            })
            char_offset += len(section) + 2  # +2 for the double newline separator
        else:
            # Split large sections on sentence boundaries
            sub_chunks = _split_on_sentences(section, max_chunk_size, overlap)
            for sub in sub_chunks:
                chunks.append({
                    "index": len(chunks),
                    "text": sub,
                    "start_char": char_offset,
                    "end_char": char_offset + len(sub),
                })
                char_offset += len(sub)
            char_offset += 2

    logger.info(f"Chunked text into {len(chunks)} chunks (avg {sum(len(c['text']) for c in chunks) // max(len(chunks), 1)} chars)")
    return chunks


def _split_on_sentences(text: str, max_size: int, overlap: int) -> List[str]:
    """Split a large text block on sentence boundaries."""
    # Split on sentence-ending punctuation followed by space
    sentences = re.split(r'(?<=[.!?;])\s+', text)

    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_size:
            current = f"{current} {sentence}".strip() if current else sentence
        else:
            if current:
                chunks.append(current)
            # Start new chunk, optionally with overlap from end of previous
            if overlap > 0 and chunks:
                overlap_text = chunks[-1][-overlap:]
                current = f"{overlap_text} {sentence}".strip()
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


def chunk_text_by_lines(text: str, lines_per_chunk: int = 10) -> List[Dict]:
    """
    Alternative chunking by line count - useful for structured documents
    like bank statements where each line is a record.

    Args:
        text: Full document text
        lines_per_chunk: Number of lines per chunk

    Returns:
        List of chunk dicts
    """
    lines = text.strip().split('\n')
    lines = [l.strip() for l in lines if l.strip()]

    chunks = []
    for i in range(0, len(lines), lines_per_chunk):
        batch = lines[i:i + lines_per_chunk]
        chunk_text_str = '\n'.join(batch)
        chunks.append({
            "index": len(chunks),
            "text": chunk_text_str,
            "start_line": i,
            "end_line": min(i + lines_per_chunk, len(lines)),
        })

    return chunks
