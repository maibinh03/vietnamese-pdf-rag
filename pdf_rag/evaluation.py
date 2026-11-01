"""Run a reproducible offline TF-IDF retrieval baseline on the sample corpus."""

import argparse
import json
import math
import platform
import re
import statistics
import sys
import time
import unicodedata
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from pdf_rag.ingestion import chunk_pages, extract_pages

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = ROOT / "data" / "evaluation" / "questions.json"
SAMPLES_PATH = ROOT / "data" / "samples"
TOKEN_PATTERN = re.compile(r"[\wÀ-ỹ]+", re.UNICODE)
OFFLINE_RELEVANCE_THRESHOLD = 0.2


def tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFD", text.casefold())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return [
        token.replace("đ", "d")
        for token in TOKEN_PATTERN.findall(normalized.replace("đ", "d"))
    ]


def load_corpus() -> list[dict]:
    chunks: list[dict] = []
    for path in sorted(SAMPLES_PATH.glob("*.txt")):
        pages = extract_pages(path.name, path.read_bytes())
        for chunk in chunk_pages(pages, 400, 80):
            chunks.append(
                {
                    "filename": path.name,
                    "text": chunk.text,
                    "tokens": Counter(tokens(chunk.text)),
                }
            )
    return chunks


def retrieve(query: str, corpus: list[dict], top_k: int = 5) -> list[dict]:
    query_counts = Counter(tokens(query))
    if not query_counts:
        return []
    document_frequency = Counter(
        token for chunk in corpus for token in chunk["tokens"]
    )
    query_vector = {
        token: count * math.log(1 + len(corpus) / (1 + document_frequency[token]))
        for token, count in query_counts.items()
    }
    query_norm = math.sqrt(sum(value * value for value in query_vector.values()))
    scored = []
    for chunk in corpus:
        weights = {
            token: count * math.log(1 + len(corpus) / (1 + document_frequency[token]))
            for token, count in chunk["tokens"].items()
        }
        norm = math.sqrt(sum(value * value for value in weights.values()))
        dot = sum(query_vector.get(token, 0) * value for token, value in weights.items())
        score = dot / (query_norm * norm) if norm and query_norm else 0.0
        scored.append((score, chunk))
    return [
        {**chunk, "score": score}
        for score, chunk in sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]
    ]


def run_evaluation() -> dict:
    corpus = load_corpus()
    cases = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    latencies: list[float] = []
    hits = 0
    answerable_count = 0
    answerable_evidence = 0
    unanswerable_correct = 0
    by_category: dict[str, dict[str, int]] = {}
    for case in cases:
        started = time.perf_counter()
        results = retrieve(case["question"], corpus)
        latencies.append((time.perf_counter() - started) * 1000)
        expected = set(case["relevant_documents"])
        is_unanswerable = case["category"] == "unanswerable"
        found = any(item["filename"] in expected for item in results)
        if not is_unanswerable:
            answerable_count += 1
            hits += int(found)
            answerable_evidence += int(
                any(item["filename"] in expected and item["score"] >= OFFLINE_RELEVANCE_THRESHOLD for item in results)
            )
        else:
            unanswerable_correct += int(
                not results or results[0]["score"] < OFFLINE_RELEVANCE_THRESHOLD
            )
        category = by_category.setdefault(case["category"], {"total": 0, "hit_at_5": 0})
        category["total"] += 1
        category["hit_at_5"] += int(found)
    sorted_latency = sorted(latencies)
    p95_index = max(0, math.ceil(0.95 * len(sorted_latency)) - 1)
    return {
        "evaluation": "offline TF-IDF retrieval baseline; not the production E5/Qdrant/LLM path",
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "runtime": {"python": sys.version.split()[0], "platform": platform.platform()},
        "question_count": len(cases),
        "corpus_chunk_count": len(corpus),
        "offline_relevance_threshold": OFFLINE_RELEVANCE_THRESHOLD,
        "answerable_recall_at_5": round(hits / answerable_count, 4) if answerable_count else 0,
        "answerable_evidence_coverage_at_threshold": round(
            answerable_evidence / answerable_count, 4
        ) if answerable_count else 0,
        "unanswerable_rejection_rate": round(
            unanswerable_correct / (len(cases) - answerable_count), 4
        ) if len(cases) > answerable_count else None,
        "retrieval_latency_ms": {
            "median": round(statistics.median(latencies), 3),
            "p95": round(sorted_latency[p95_index], 3),
        },
        "latency_scope": "Per-question TF-IDF scoring over in-memory chunks; excludes corpus loading, API, embedding model and vector database.",
        "generation_accuracy": None,
        "grounding_rate": None,
        "generation_note": "Not measured: offline baseline does not call an LLM.",
        "categories": by_category,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "evaluation.json")
    args = parser.parse_args()
    report = run_evaluation()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
