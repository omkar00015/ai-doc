"""
Document Comparison Engine.

Takes two parsed documents, chunks them, embeds them using AI,
and produces a detailed comparison report showing:
- MATCH: Sections that are semantically identical (similarity > 0.85)
- MODIFIED: Sections with similar meaning but different wording (0.50-0.85)
- MISSING_IN_B: Sections present in Doc A but absent from Doc B
- MISSING_IN_A: Sections present in Doc B but absent from Doc A

Designed for CA audit workflows - comparing financial documents,
policy drafts, bank statements, or compliance reports.
"""

import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

from utils.text_chunker import chunk_text
from utils.embedding_service import compute_similarity, get_embedding_method

logger = logging.getLogger(__name__)

# Similarity thresholds for classification
THRESHOLD_MATCH = 0.85
THRESHOLD_MODIFIED = 0.50


def compare_documents(
    text_a: str,
    text_b: str,
    name_a: str = "Document A",
    name_b: str = "Document B",
    max_chunk_size: int = 500,
) -> Dict[str, Any]:
    """
    Full document comparison pipeline.

    Args:
        text_a: Full text of first document
        text_b: Full text of second document
        name_a: Display name for first document
        name_b: Display name for second document
        max_chunk_size: Maximum characters per chunk

    Returns:
        Comparison result dict with summary, alignments, and details
    """
    logger.info(f"Starting comparison: '{name_a}' vs '{name_b}'")
    start_time = datetime.now()

    # Step 1: Chunk both documents
    chunks_a = chunk_text(text_a, max_chunk_size=max_chunk_size)
    chunks_b = chunk_text(text_b, max_chunk_size=max_chunk_size)

    if not chunks_a and not chunks_b:
        return _empty_result(name_a, name_b, "Both documents are empty")

    if not chunks_a:
        return _all_missing_result(name_a, name_b, chunks_b, "a")

    if not chunks_b:
        return _all_missing_result(name_a, name_b, chunks_a, "b")

    logger.info(f"Doc A: {len(chunks_a)} chunks | Doc B: {len(chunks_b)} chunks")

    # Step 2: Compute similarity matrix
    texts_a = [c["text"] for c in chunks_a]
    texts_b = [c["text"] for c in chunks_b]

    sim_matrix = compute_similarity(texts_a, texts_b)

    if sim_matrix.size == 0:
        return _empty_result(name_a, name_b, "Failed to compute similarity")

    # Step 3: Align chunks using the similarity matrix
    alignments = _align_chunks(chunks_a, chunks_b, sim_matrix)

    # Step 4: Classify and build report
    result = _build_report(alignments, chunks_a, chunks_b, sim_matrix, name_a, name_b)

    elapsed = (datetime.now() - start_time).total_seconds()
    result["processing_time_seconds"] = round(elapsed, 2)
    result["embedding_method"] = get_embedding_method()

    logger.info(
        f"Comparison complete in {elapsed:.1f}s - "
        f"{result['summary']['match_count']} matches, "
        f"{result['summary']['modified_count']} modified, "
        f"{result['summary']['missing_in_b_count']} missing in B, "
        f"{result['summary']['missing_in_a_count']} missing in A"
    )

    return result


def _align_chunks(
    chunks_a: List[Dict],
    chunks_b: List[Dict],
    sim_matrix,
) -> List[Dict]:
    """
    Align chunks from Doc A to Doc B using greedy best-match.

    For each chunk in A, find the best matching chunk in B.
    Then identify unmatched chunks in B (missing in A).
    """
    import numpy as np

    n_a, n_b = sim_matrix.shape
    alignments = []
    matched_b_indices = set()

    # For each chunk in A, find best match in B
    for i in range(n_a):
        best_j = int(np.argmax(sim_matrix[i]))
        best_score = float(sim_matrix[i, best_j])

        if best_score >= THRESHOLD_MATCH:
            status = "match"
        elif best_score >= THRESHOLD_MODIFIED:
            status = "modified"
        else:
            status = "missing_in_b"

        alignment = {
            "chunk_a_index": i,
            "chunk_a_text": chunks_a[i]["text"],
            "similarity": round(best_score, 4),
            "status": status,
        }

        if status != "missing_in_b":
            alignment["chunk_b_index"] = best_j
            alignment["chunk_b_text"] = chunks_b[best_j]["text"]
            matched_b_indices.add(best_j)
        else:
            alignment["chunk_b_index"] = None
            alignment["chunk_b_text"] = None

        alignments.append(alignment)

    # Find chunks in B that were never matched (missing in A)
    for j in range(n_b):
        if j not in matched_b_indices:
            # Check if this chunk has any reasonable match in A
            best_i = int(np.argmax(sim_matrix[:, j]))
            best_score = float(sim_matrix[best_i, j])

            alignments.append({
                "chunk_a_index": None,
                "chunk_a_text": None,
                "chunk_b_index": j,
                "chunk_b_text": chunks_b[j]["text"],
                "similarity": round(best_score, 4),
                "status": "missing_in_a",
            })

    return alignments


def _build_report(
    alignments: List[Dict],
    chunks_a: List[Dict],
    chunks_b: List[Dict],
    sim_matrix,
    name_a: str,
    name_b: str,
) -> Dict[str, Any]:
    """Build the final comparison report from alignments."""
    import numpy as np

    matches = [a for a in alignments if a["status"] == "match"]
    modified = [a for a in alignments if a["status"] == "modified"]
    missing_in_b = [a for a in alignments if a["status"] == "missing_in_b"]
    missing_in_a = [a for a in alignments if a["status"] == "missing_in_a"]

    total_chunks = len(chunks_a) + len(chunks_b)
    matched_chunks = len(matches) * 2  # each match accounts for one chunk in each doc

    # Overall similarity score (average of best matches from A→B perspective)
    if len(chunks_a) > 0:
        best_scores_a = [float(np.max(sim_matrix[i])) for i in range(sim_matrix.shape[0])]
        avg_similarity = sum(best_scores_a) / len(best_scores_a)
    else:
        avg_similarity = 0.0

    return {
        "success": True,
        "document_a": name_a,
        "document_b": name_b,
        "summary": {
            "overall_similarity": round(avg_similarity, 4),
            "overall_similarity_pct": round(avg_similarity * 100, 1),
            "total_chunks_a": len(chunks_a),
            "total_chunks_b": len(chunks_b),
            "match_count": len(matches),
            "modified_count": len(modified),
            "missing_in_b_count": len(missing_in_b),
            "missing_in_a_count": len(missing_in_a),
            "coverage_pct": round(
                (len(matches) + len(modified)) / max(len(chunks_a), 1) * 100, 1
            ),
        },
        "alignments": alignments,
        "matches": matches,
        "modified": modified,
        "missing_in_b": missing_in_b,
        "missing_in_a": missing_in_a,
        "timestamp": datetime.now().isoformat(),
    }


def _empty_result(name_a: str, name_b: str, reason: str) -> Dict[str, Any]:
    """Return empty comparison result."""
    return {
        "success": False,
        "document_a": name_a,
        "document_b": name_b,
        "error": reason,
        "summary": {
            "overall_similarity": 0,
            "overall_similarity_pct": 0,
            "total_chunks_a": 0,
            "total_chunks_b": 0,
            "match_count": 0,
            "modified_count": 0,
            "missing_in_b_count": 0,
            "missing_in_a_count": 0,
            "coverage_pct": 0,
        },
        "alignments": [],
        "matches": [],
        "modified": [],
        "missing_in_b": [],
        "missing_in_a": [],
        "timestamp": datetime.now().isoformat(),
    }


def _all_missing_result(
    name_a: str, name_b: str, chunks: List[Dict], missing_in: str
) -> Dict[str, Any]:
    """Result when one document is empty - everything is 'missing'."""
    alignments = []
    for c in chunks:
        if missing_in == "b":
            alignments.append({
                "chunk_a_index": c["index"],
                "chunk_a_text": c["text"],
                "chunk_b_index": None,
                "chunk_b_text": None,
                "similarity": 0.0,
                "status": "missing_in_b",
            })
        else:
            alignments.append({
                "chunk_a_index": None,
                "chunk_a_text": None,
                "chunk_b_index": c["index"],
                "chunk_b_text": c["text"],
                "similarity": 0.0,
                "status": "missing_in_a",
            })

    return {
        "success": True,
        "document_a": name_a,
        "document_b": name_b,
        "summary": {
            "overall_similarity": 0,
            "overall_similarity_pct": 0,
            "total_chunks_a": len(chunks) if missing_in == "b" else 0,
            "total_chunks_b": 0 if missing_in == "b" else len(chunks),
            "match_count": 0,
            "modified_count": 0,
            "missing_in_b_count": len(chunks) if missing_in == "b" else 0,
            "missing_in_a_count": 0 if missing_in == "b" else len(chunks),
            "coverage_pct": 0,
        },
        "alignments": alignments,
        "matches": [],
        "modified": [],
        "missing_in_b": alignments if missing_in == "b" else [],
        "missing_in_a": alignments if missing_in == "a" else [],
        "timestamp": datetime.now().isoformat(),
    }
