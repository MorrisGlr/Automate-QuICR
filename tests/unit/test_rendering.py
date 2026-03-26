"""Test rendering modules produce valid output from v2 fixtures.

These tests require weasyprint to be installed. They are skipped if unavailable.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"

try:
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False

weasyprint_required = pytest.mark.skipif(
    not HAS_WEASYPRINT, reason="weasyprint not installed"
)


@weasyprint_required
def test_chart_review_pdf_renders_v2_data():
    from src.rendering.chart_review_pdf import chart_review_json_to_pdf

    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up directory structure expected by the renderer
        model = "test_model"
        dp_dir = os.path.join(tmpdir, model, "chart_review", "drug_pricing")
        os.makedirs(dp_dir)
        pdf_dir = os.path.join(tmpdir, model, "chart_review", "pdf")

        # Copy v2 fixture as a drug-pricing enriched file
        with open(FIXTURES_DIR / "v2_chart_review.json", "r") as f:
            data = json.load(f)
        # Add minimal drug pricing if not present
        if "Generic Drug Pricing" not in data.get("Plan", {}):
            data["Plan"]["Generic Drug Pricing"] = []
        with open(os.path.join(dp_dir, "test_chart_review_pricing.json"), "w") as f:
            json.dump(data, f)

        chart_review_json_to_pdf(model, tmpdir)

        # Verify PDF was created
        pdf_files = list(Path(pdf_dir).glob("*.pdf"))
        assert len(pdf_files) == 1
        assert pdf_files[0].stat().st_size > 0


@weasyprint_required
def test_feedback_pdf_renders_v2_data():
    from src.rendering.feedback_pdf import cr_feedback_json_to_pdf

    with tempfile.TemporaryDirectory() as tmpdir:
        model = "test_model"
        fb_dir = os.path.join(tmpdir, model, "cr_feedback")
        os.makedirs(fb_dir)

        with open(FIXTURES_DIR / "v2_feedback.json", "r") as f:
            data = json.load(f)
        with open(os.path.join(fb_dir, "test_cr_feedback.json"), "w") as f:
            json.dump(data, f)

        cr_feedback_json_to_pdf(model, tmpdir)

        pdf_dir = os.path.join(tmpdir, model, "cr_feedback", "pdf")
        pdf_files = list(Path(pdf_dir).glob("*.pdf"))
        assert len(pdf_files) == 1
        assert pdf_files[0].stat().st_size > 0


@weasyprint_required
def test_aggregate_pdf_renders_v2_data():
    from src.rendering.aggregate_pdf import aggregate_feedback

    with tempfile.TemporaryDirectory() as tmpdir:
        model = "test_model"
        fb_dir = os.path.join(tmpdir, model, "cr_feedback")
        os.makedirs(fb_dir)

        with open(FIXTURES_DIR / "v2_feedback.json", "r") as f:
            data = json.load(f)
        with open(os.path.join(fb_dir, "test_cr_feedback.json"), "w") as f:
            json.dump(data, f)

        aggregate_feedback(model, tmpdir)

        pdf_path = os.path.join(fb_dir, "aggregated_feedback.pdf")
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 0

        html_path = os.path.join(fb_dir, "aggregated_feedback.html")
        assert os.path.exists(html_path)
