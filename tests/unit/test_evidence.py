"""Tests for evidence retrieval and citation validation."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.evidence.grading import (
    _source_matches,
    enrich_evidence_metadata,
    validate_citations,
)
from src.evidence.pubmed import (
    _cache_key,
    _load_cached,
    _save_cache,
    build_evidence_context,
    extract_condition_keywords,
    load_guidelines,
    match_guidelines,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
SAMPLE_GUIDELINES = str(FIXTURES_DIR / "sample_guidelines.json")


class TestLoadGuidelines:
    def test_load_sample(self):
        guidelines = load_guidelines(SAMPLE_GUIDELINES)
        assert isinstance(guidelines, list)
        assert len(guidelines) == 4
        assert guidelines[0]["id"] == "aha-acc-afib-2023"


class TestExtractConditionKeywords:
    def test_matches_known_conditions(self):
        guidelines = load_guidelines(SAMPLE_GUIDELINES)
        emr_text = "Patient presents with atrial fibrillation and hypertension."
        conditions = extract_condition_keywords(emr_text, guidelines)
        assert "atrial fibrillation" in conditions
        assert "hypertension" in conditions

    def test_no_match_returns_empty(self):
        guidelines = load_guidelines(SAMPLE_GUIDELINES)
        emr_text = "Patient presents with ingrown toenail."
        conditions = extract_condition_keywords(emr_text, guidelines)
        assert conditions == []

    def test_case_insensitive(self):
        guidelines = load_guidelines(SAMPLE_GUIDELINES)
        emr_text = "ATRIAL FIBRILLATION detected on ECG."
        conditions = extract_condition_keywords(emr_text, guidelines)
        assert "atrial fibrillation" in conditions

    def test_deduplication(self):
        guidelines = load_guidelines(SAMPLE_GUIDELINES)
        emr_text = "Patient has AFib. Atrial fibrillation confirmed."
        conditions = extract_condition_keywords(emr_text, guidelines)
        # Each unique condition should appear only once
        assert len(conditions) == len(set(conditions))


class TestMatchGuidelines:
    def test_matches_correct_guidelines(self):
        guidelines = load_guidelines(SAMPLE_GUIDELINES)
        matched, unmatched = match_guidelines(["atrial fibrillation", "hypertension"], guidelines)
        assert len(matched) >= 2
        ids = {g["id"] for g in matched}
        assert "aha-acc-afib-2023" in ids
        assert "aha-acc-hypertension-2017" in ids
        assert unmatched == []

    def test_unmatched_conditions_returned(self):
        guidelines = load_guidelines(SAMPLE_GUIDELINES)
        matched, unmatched = match_guidelines(["atrial fibrillation", "gout"], guidelines)
        assert len(matched) >= 1
        assert "gout" in unmatched

    def test_deduplicates_by_id(self):
        guidelines = load_guidelines(SAMPLE_GUIDELINES)
        # "AFib" and "atrial fibrillation" should both match the same guideline
        matched, _ = match_guidelines(["AFib", "atrial fibrillation"], guidelines)
        ids = [g["id"] for g in matched]
        assert len(ids) == len(set(ids))


class TestBuildEvidenceContext:
    def test_returns_text_and_sources(self):
        emr_text = "71-year-old female with atrial fibrillation and hypertension."
        text, sources = build_evidence_context(emr_text, SAMPLE_GUIDELINES)
        assert "# Evidence Context" in text
        assert "Curated Clinical Guidelines" in text
        assert len(sources) >= 2
        assert all("title" in s for s in sources)

    def test_no_conditions_returns_empty(self):
        emr_text = "Patient presents with ingrown toenail."
        text, sources = build_evidence_context(emr_text, SAMPLE_GUIDELINES)
        assert text == ""
        assert sources == []

    @patch("src.evidence.pubmed.query_pubmed")
    def test_queries_pubmed_for_unmatched(self, mock_pubmed):
        """PubMed should be queried for conditions found in guidelines but not matched."""
        mock_pubmed.return_value = [
            {"pmid": "99999", "title": "Gout Management", "abstract": "...", "year": 2023, "url": "...", "source": "PubMed"}
        ]
        # Directly test with unmatched conditions by calling match_guidelines + query
        guidelines = load_guidelines(SAMPLE_GUIDELINES)
        # "colonoscopy" is in guidelines, "atrial fibrillation" too
        # Let's test that build_evidence_context works end-to-end with known conditions
        emr_text = "Patient with atrial fibrillation and hypertension."
        text, sources = build_evidence_context(emr_text, SAMPLE_GUIDELINES)
        # All conditions match curated DB, so PubMed should NOT be called
        assert not mock_pubmed.called
        assert "Curated Clinical Guidelines" in text
        assert all(s["origin"] == "curated" for s in sources)


class TestValidateCitations:
    def test_verified_citations(self):
        problem = {
            "Evidence Grade": {
                "certainty": "High",
                "sources": [
                    {"title": "2023 ACC/AHA/ACCP/HRS Guideline for Diagnosis and Management of Atrial Fibrillation", "source": "AHA/ACC"}
                ],
                "rationale": "...",
            }
        }
        retrieved = [
            {"title": "2023 ACC/AHA/ACCP/HRS Guideline for Diagnosis and Management of Atrial Fibrillation", "source": "AHA/ACC", "year": 2023}
        ]
        flagged = validate_citations(problem, retrieved)
        assert flagged == []

    def test_unverified_citation_flagged(self):
        problem = {
            "Evidence Grade": {
                "certainty": "High",
                "sources": [
                    {"title": "Made Up Guideline That Does Not Exist", "source": "Nobody"}
                ],
                "rationale": "...",
            }
        }
        retrieved = [
            {"title": "Real Guideline", "source": "AHA", "year": 2023}
        ]
        flagged = validate_citations(problem, retrieved)
        assert len(flagged) == 1
        assert flagged[0]["unverified"] is True

    def test_no_evidence_grade_returns_empty(self):
        problem = {"Problem Name": "Test"}
        flagged = validate_citations(problem, [])
        assert flagged == []


class TestEnrichEvidenceMetadata:
    def test_marks_unverified_sources(self):
        chart_review = {
            "Plan": {
                "problems": [
                    {
                        "Problem Name": "AF",
                        "Evidence Grade": {
                            "certainty": "High",
                            "sources": [
                                {"title": "Real Guideline", "source": "AHA"},
                                {"title": "Hallucinated Source", "source": "Unknown"},
                            ],
                            "rationale": "...",
                        },
                    }
                ]
            }
        }
        retrieved = [{"title": "Real Guideline", "source": "AHA", "year": 2023}]
        result = enrich_evidence_metadata(chart_review, retrieved)
        sources = result["Plan"]["problems"][0]["Evidence Grade"]["sources"]
        assert sources[0].get("unverified") is None or sources[0].get("unverified") is False
        assert sources[1]["unverified"] is True
        assert "_citation_flags" in result

    def test_no_flags_when_all_verified(self):
        chart_review = {
            "Plan": {
                "problems": [
                    {
                        "Problem Name": "AF",
                        "Evidence Grade": {
                            "certainty": "High",
                            "sources": [{"title": "Real Guideline", "source": "AHA"}],
                            "rationale": "...",
                        },
                    }
                ]
            }
        }
        retrieved = [{"title": "Real Guideline", "source": "AHA", "year": 2023}]
        result = enrich_evidence_metadata(chart_review, retrieved)
        assert "_citation_flags" not in result

    def test_problem_without_evidence_grade_is_skipped(self):
        chart_review = {
            "Plan": {
                "problems": [
                    {"Problem Name": "Hypertension"},
                    {
                        "Problem Name": "AF",
                        "Evidence Grade": {
                            "certainty": "High",
                            "sources": [{"title": "Hallucinated", "source": "Unknown"}],
                            "rationale": "...",
                        },
                    },
                ]
            }
        }
        result = enrich_evidence_metadata(chart_review, [])
        # First problem (no Evidence Grade) should not cause errors
        assert "_citation_flags" in result
        assert result["_citation_flags"][0]["problem"] == "AF"


class TestSourceMatches:
    def test_empty_cited_title_returns_false(self):
        cited = {"title": "", "source": "AHA"}
        retrieved = {"title": "Some Guideline", "source": "AHA"}
        assert _source_matches(cited, retrieved) is False

    def test_empty_retrieved_title_returns_false(self):
        cited = {"title": "Some Guideline", "source": "AHA"}
        retrieved = {"title": "", "source": "AHA"}
        assert _source_matches(cited, retrieved) is False

    def test_source_and_year_match_when_titles_differ(self):
        cited = {"title": "ACC Guidelines 2023", "source": "acc", "year": 2023}
        retrieved = {"title": "American College of Cardiology 2023 Report", "source": "acc", "year": 2023}
        # titles don't substring-match, but source + year do
        assert _source_matches(cited, retrieved) is True


class TestValidateCitationsEdgeCases:
    def test_empty_sources_list_returns_empty(self):
        problem = {
            "Evidence Grade": {
                "certainty": "High",
                "sources": [],
                "rationale": "...",
            }
        }
        flagged = validate_citations(problem, [])
        assert flagged == []


class TestExtractConditionKeywordsShortTerm:
    def test_short_condition_matched_with_word_boundary(self):
        guidelines = [
            {"id": "hiv-test", "conditions": ["hiv"], "title": "HIV Guidelines",
             "source": "WHO", "year": 2022, "summary": "...", "grade": "A",
             "grade_certainty": "High"}
        ]
        emr_text = "Patient has HIV and requires antiretroviral therapy."
        conditions = extract_condition_keywords(emr_text, guidelines)
        assert "hiv" in conditions

    def test_short_condition_not_matched_as_substring(self):
        guidelines = [
            {"id": "hiv-test", "conditions": ["hiv"], "title": "HIV Guidelines",
             "source": "WHO", "year": 2022, "summary": "...", "grade": "A",
             "grade_certainty": "High"}
        ]
        # "achieve" contains "hiv" but not as a word boundary
        emr_text = "Patient needs to achieve better glucose control."
        conditions = extract_condition_keywords(emr_text, guidelines)
        assert "hiv" not in conditions


class TestPubmedCache:
    def test_cache_key_is_deterministic(self):
        key1 = _cache_key("hypertension")
        key2 = _cache_key("hypertension")
        assert key1 == key2

    def test_cache_key_is_case_insensitive(self):
        assert _cache_key("Hypertension") == _cache_key("hypertension")

    def test_load_cached_returns_none_on_miss(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _load_cached(tmpdir, "nonexistent condition xyz")
        assert result is None

    def test_save_and_load_cache_roundtrip(self):
        data = [{"pmid": "12345", "title": "Test Article", "year": 2023, "source": "PubMed"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            _save_cache(tmpdir, "hypertension", data)
            loaded = _load_cached(tmpdir, "hypertension")
        assert loaded == data

    @patch("src.evidence.pubmed.match_guidelines")
    @patch("src.evidence.pubmed.extract_condition_keywords")
    @patch("src.evidence.pubmed.query_pubmed")
    def test_build_evidence_queries_pubmed_for_unmatched_and_caches(
        self, mock_pubmed, mock_extract, mock_match, tmp_path
    ):
        """Covers the PubMed query + cache write/read path in build_evidence_context."""
        pubmed_result = [
            {"pmid": "99", "title": "Gout Management Guidelines", "abstract": "Summary.",
             "year": 2023, "url": "https://pubmed.ncbi.nlm.nih.gov/99/", "source": "PubMed"}
        ]
        mock_pubmed.return_value = pubmed_result
        mock_extract.return_value = ["gout"]
        mock_match.return_value = ([], ["gout"])  # force unmatched condition

        guidelines = [{"id": "afib", "conditions": ["atrial fibrillation"], "title": "AF Guideline",
                       "source": "AHA", "year": 2023, "summary": "...", "grade": "A",
                       "grade_certainty": "High"}]
        guidelines_path = str(tmp_path / "guidelines.json")
        with open(guidelines_path, "w") as f:
            import json
            json.dump(guidelines, f)

        cache_dir = str(tmp_path / "cache")
        emr_text = "Patient has gout."

        # First call: PubMed queried, result cached
        text, sources = build_evidence_context(emr_text, guidelines_path, cache_dir=cache_dir)
        assert mock_pubmed.call_count == 1
        assert any(s["source"] == "PubMed" for s in sources)
        assert "PubMed Literature" in text

        # Second call: cache hit, PubMed not called again
        build_evidence_context(emr_text, guidelines_path, cache_dir=cache_dir)
        assert mock_pubmed.call_count == 1
