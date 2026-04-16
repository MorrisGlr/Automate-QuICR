# Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
# Licensed under the Apache License, Version 2.0.
"""Post-hoc citation validation for LLM-generated evidence grades.

Cross-references LLM-cited sources against actually-retrieved evidence
to flag potential hallucinated citations. Does not override the LLM's
GRADE certainty judgment — only flags unverified sources.
"""


def _normalize(text: str) -> str:
    """Normalize text for fuzzy comparison."""
    return " ".join(text.lower().split())


def _source_matches(cited: dict, retrieved: dict) -> bool:
    """Check if a cited source matches a retrieved source.

    Uses fuzzy title matching (substring containment) and optionally
    year matching for confirmation.
    """
    cited_title = _normalize(cited.get("title", ""))
    retrieved_title = _normalize(retrieved.get("title", ""))

    if not cited_title or not retrieved_title:
        return False

    # Check title overlap (either direction for substring match)
    title_match = cited_title in retrieved_title or retrieved_title in cited_title

    # Also check source organization if titles are short
    if not title_match:
        cited_source = _normalize(cited.get("source", ""))
        retrieved_source = _normalize(retrieved.get("source", ""))
        if cited_source and retrieved_source:
            source_match = cited_source in retrieved_source or retrieved_source in cited_source
            # If source matches and years match, consider it a match
            if source_match and cited.get("year") and retrieved.get("year"):
                if cited["year"] == retrieved["year"]:
                    return True

    return title_match


def validate_citations(
    problem: dict,
    retrieved_sources: list[dict],
) -> list[dict]:
    """Cross-reference a problem's cited sources against retrieved evidence.

    Args:
        problem: A single problem dict from chart review output,
                 expected to contain an "Evidence Grade" key with "sources" array.
        retrieved_sources: List of sources that were actually retrieved
                          and injected into the LLM context.

    Returns:
        List of flagged citations (dicts with "title", "source", "unverified": True).
        Empty list if all citations are verified or no citations exist.
    """
    evidence_grade = problem.get("Evidence Grade")
    if not evidence_grade:
        return []

    cited_sources = evidence_grade.get("sources", [])
    if not cited_sources:
        return []

    flagged = []
    for cited in cited_sources:
        verified = any(
            _source_matches(cited, retrieved)
            for retrieved in retrieved_sources
        )
        if not verified:
            flagged.append({
                "title": cited.get("title", ""),
                "source": cited.get("source", ""),
                "unverified": True,
            })

    return flagged


def enrich_evidence_metadata(
    chart_review: dict,
    retrieved_sources: list[dict],
) -> dict:
    """Add citation validation metadata to a chart review output.

    Walks all problems and flags any citations not found in the
    retrieved evidence. Adds an "unverified" field to flagged sources
    and appends a "_citation_flags" metadata key to the output.

    Args:
        chart_review: Full chart review JSON output dict.
        retrieved_sources: List of sources from build_evidence_context().

    Returns:
        The chart_review dict with citation flags added (mutated in place).
    """
    plan = chart_review.get("Plan", {})
    problems = plan.get("problems", [])

    all_flags = []
    for problem in problems:
        evidence_grade = problem.get("Evidence Grade")
        if not evidence_grade:
            continue

        cited_sources = evidence_grade.get("sources", [])
        flagged = validate_citations(problem, retrieved_sources)
        flagged_titles = {f["title"].lower() for f in flagged}

        # Mark unverified sources in-place
        for cited in cited_sources:
            if cited.get("title", "").lower() in flagged_titles:
                cited["unverified"] = True

        if flagged:
            all_flags.append({
                "problem": problem.get("Problem Name", ""),
                "flagged_citations": flagged,
            })

    if all_flags:
        chart_review["_citation_flags"] = all_flags

    return chart_review
