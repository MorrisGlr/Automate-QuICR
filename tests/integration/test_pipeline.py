"""Integration tests for the pipeline CLI."""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

try:
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False

weasyprint_required = pytest.mark.skipif(
    not HAS_WEASYPRINT, reason="weasyprint not installed"
)


def test_cli_help():
    """CLI --help exits 0 and shows usage."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "app.py"), "--help"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0
    assert "--step" in result.stdout


def test_cli_invalid_step():
    """CLI rejects invalid step names."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "app.py"), "--step", "invalid"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode != 0


@weasyprint_required
def test_cli_pdf_aggregate():
    """CLI pdf-aggregate step runs successfully with existing data."""
    result = subprocess.run(
        [
            sys.executable, str(PROJECT_ROOT / "app.py"),
            "--step", "pdf-aggregate",
            "--model", "o4-mini-2025-04-16",
        ],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "Aggregated" in result.stdout
