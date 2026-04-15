"""PubMed RAG retrieval and curated guideline matching for evidence-based chart review.

Provides in-context evidence for LLM inference by:
1. Extracting condition keywords from EMR text
2. Matching against a curated guidelines database
3. Querying PubMed E-utilities for unmatched conditions
4. Formatting evidence as context to append to the user prompt
"""

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_GUIDELINES_PATH = str(PROJECT_ROOT / "data" / "guidelines" / "guidelines.json")

# NCBI E-utilities base URLs
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def load_guidelines(guidelines_path: str = DEFAULT_GUIDELINES_PATH) -> list[dict]:
    """Load the curated guidelines database."""
    with open(guidelines_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_condition_keywords(emr_text: str, guidelines: list[dict]) -> list[str]:
    """Extract condition keywords from EMR text by matching against known conditions.

    Uses the conditions lists from the guidelines database for keyword matching,
    plus a set of common clinical terms as fallback.

    Args:
        emr_text: Raw EMR text content.
        guidelines: Loaded guidelines database.

    Returns:
        Deduplicated list of matched condition keywords.
    """
    text_lower = emr_text.lower()

    # Build condition → keyword mapping from guidelines
    all_conditions = set()
    for entry in guidelines:
        for condition in entry.get("conditions", []):
            all_conditions.add(condition.lower())

    matched = []
    for condition in sorted(all_conditions, key=len, reverse=True):
        # Use word boundary matching for short terms, substring for longer ones
        if len(condition) <= 3:
            pattern = r"\b" + re.escape(condition) + r"\b"
            if re.search(pattern, text_lower):
                matched.append(condition)
        else:
            if condition in text_lower:
                matched.append(condition)

    return list(dict.fromkeys(matched))  # deduplicate preserving order


def match_guidelines(conditions: list[str], guidelines: list[dict]) -> tuple[list[dict], list[str]]:
    """Match extracted conditions against the curated guidelines database.

    Args:
        conditions: List of condition keywords found in the EMR.
        guidelines: Loaded guidelines database.

    Returns:
        Tuple of (matched_guidelines, unmatched_conditions).
        matched_guidelines is deduplicated by guideline id.
    """
    matched = {}
    matched_conditions = set()

    for condition in conditions:
        cond_lower = condition.lower()
        for entry in guidelines:
            entry_conditions = [c.lower() for c in entry.get("conditions", [])]
            if cond_lower in entry_conditions:
                if entry["id"] not in matched:
                    matched[entry["id"]] = entry
                matched_conditions.add(cond_lower)

    unmatched = [c for c in conditions if c.lower() not in matched_conditions]
    return list(matched.values()), unmatched


def query_pubmed(
    condition: str,
    max_results: int = 3,
    api_key: str | None = None,
) -> list[dict]:
    """Query PubMed E-utilities for clinical practice guidelines on a condition.

    Args:
        condition: Clinical condition to search for.
        max_results: Maximum number of results to return.
        api_key: Optional NCBI API key (increases rate limit from 3 to 10 req/sec).

    Returns:
        List of dicts with keys: pmid, title, abstract, year.
    """
    # Rate limiting
    delay = 0.1 if api_key else 0.34
    time.sleep(delay)

    # Step 1: esearch to get PMIDs
    search_term = (
        f'("{condition}"[MeSH Terms] OR "{condition}"[Title/Abstract]) '
        f'AND ("Practice Guideline"[Publication Type] OR "Guideline"[Publication Type]) '
        f'AND ("last 5 years"[PDat])'
    )
    params = {
        "db": "pubmed",
        "term": search_term,
        "retmax": str(max_results),
        "retmode": "xml",
        "sort": "relevance",
    }
    if api_key:
        params["api_key"] = api_key

    try:
        url = f"{ESEARCH_URL}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            search_xml = resp.read()
    except (urllib.error.URLError, TimeoutError):
        return []

    root = ET.fromstring(search_xml)
    pmids = [id_elem.text for id_elem in root.findall(".//Id") if id_elem.text]
    if not pmids:
        return []

    # Step 2: efetch to get article details
    time.sleep(delay)
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }
    if api_key:
        fetch_params["api_key"] = api_key

    try:
        url = f"{EFETCH_URL}?{urllib.parse.urlencode(fetch_params)}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            fetch_xml = resp.read()
    except (urllib.error.URLError, TimeoutError):
        return []

    root = ET.fromstring(fetch_xml)
    results = []
    for article in root.findall(".//PubmedArticle"):
        pmid_elem = article.find(".//PMID")
        title_elem = article.find(".//ArticleTitle")
        abstract_parts = article.findall(".//AbstractText")
        year_elem = article.find(".//PubDate/Year")

        pmid = pmid_elem.text if pmid_elem is not None else ""
        title = title_elem.text if title_elem is not None else ""
        year = int(year_elem.text) if year_elem is not None and year_elem.text else 0
        abstract = " ".join(
            part.text for part in abstract_parts if part.text
        )[:500]  # Truncate for context window efficiency

        if title:
            results.append({
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "year": year,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "source": "PubMed",
            })

    return results


def _cache_key(condition: str) -> str:
    """Generate a cache filename for a condition query."""
    return hashlib.md5(condition.lower().encode()).hexdigest()


def _load_cached(cache_dir: str, condition: str) -> list[dict] | None:
    """Load cached PubMed results for a condition, if available."""
    path = os.path.join(cache_dir, f"{_cache_key(condition)}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_cache(cache_dir: str, condition: str, results: list[dict]) -> None:
    """Save PubMed results to cache."""
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{_cache_key(condition)}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def build_evidence_context(
    emr_text: str,
    guidelines_path: str = DEFAULT_GUIDELINES_PATH,
    api_key: str | None = None,
    cache_dir: str | None = None,
) -> tuple[str, list[dict]]:
    """Build evidence context for LLM inference from EMR text.

    Extracts conditions, matches curated guidelines, queries PubMed for gaps,
    and formats everything as a text section to append to the user prompt.

    Args:
        emr_text: Raw EMR text content.
        guidelines_path: Path to curated guidelines JSON.
        api_key: Optional NCBI API key.
        cache_dir: Optional directory for caching PubMed results.

    Returns:
        Tuple of (evidence_context_text, all_retrieved_sources).
        evidence_context_text is formatted for prompt injection.
        all_retrieved_sources is the full list for post-hoc citation validation.
    """
    guidelines = load_guidelines(guidelines_path)
    conditions = extract_condition_keywords(emr_text, guidelines)

    if not conditions:
        return "", []

    matched_guidelines, unmatched = match_guidelines(conditions, guidelines)

    # Query PubMed for unmatched conditions
    pubmed_results = []
    for condition in unmatched:
        cached = _load_cached(cache_dir, condition) if cache_dir else None
        if cached is not None:
            pubmed_results.extend(cached)
        else:
            results = query_pubmed(condition, max_results=3, api_key=api_key)
            pubmed_results.extend(results)
            if cache_dir:
                _save_cache(cache_dir, condition, results)

    # Build all_sources for validation
    all_sources = []
    for g in matched_guidelines:
        all_sources.append({
            "title": g["title"],
            "source": g["source"],
            "year": g["year"],
            "url": g.get("url", ""),
            "origin": "curated",
        })
    for p in pubmed_results:
        all_sources.append({
            "title": p["title"],
            "source": p["source"],
            "year": p["year"],
            "url": p.get("url", ""),
            "origin": "pubmed",
        })

    # Format evidence context text
    lines = ["# Evidence Context"]

    if matched_guidelines:
        lines.append("\n## Curated Clinical Guidelines")
        for g in matched_guidelines:
            grade_str = f" (Grade {g['grade']})" if g.get("grade") else ""
            lines.append(
                f"- [{g['source']} {g['year']}] {g['title']}{grade_str}: {g['summary']}"
            )

    if pubmed_results:
        lines.append("\n## PubMed Literature")
        for p in pubmed_results:
            year_str = f" ({p['year']})" if p.get("year") else ""
            abstract_str = f": {p['abstract']}" if p.get("abstract") else ""
            lines.append(
                f"- [PMID:{p['pmid']}] {p['title']}{year_str}{abstract_str}"
            )

    evidence_text = "\n".join(lines)
    return evidence_text, all_sources
