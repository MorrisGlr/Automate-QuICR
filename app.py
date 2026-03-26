#!/usr/bin/env python3
"""QuICR pipeline CLI.

Usage:
    python app.py --step <step> [--model <model>] [--provider <provider>] [options]

Steps:
    inference-cr       Run chart review inference
    inference-fb       Run feedback inference
    drug-pricing       Run medication NER + drug pricing enrichment
    pdf-cr             Generate chart review PDFs
    pdf-fb             Generate feedback PDFs
    pdf-aggregate      Generate aggregated feedback PDF
    all                Run full pipeline
"""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from src.utils.schema import load_schema, load_system_prompt

PROJECT_ROOT = Path(__file__).resolve().parent

STEPS = [
    "inference-cr",
    "inference-fb",
    "drug-pricing",
    "pdf-cr",
    "pdf-fb",
    "pdf-aggregate",
    "all",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="QuICR pipeline")
    parser.add_argument(
        "--step", required=True, choices=STEPS,
        help="Pipeline step to run",
    )
    parser.add_argument("--model", default="o4-mini-2025-04-16", help="Model name")
    parser.add_argument(
        "--provider", default="openai", choices=["openai", "gemini"],
        help="Inference provider (default: openai)",
    )
    parser.add_argument("--input-dir", default="data", help="Input data directory")
    parser.add_argument("--output-dir", default="generated_output", help="Output directory")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    parser.add_argument("--system-prompt", default=None, help="Path to system prompt file")
    parser.add_argument("--schema", default=None, help="Path to JSON schema file")
    return parser


def _create_provider(args):
    """Lazily create the appropriate inference provider."""
    if args.provider == "openai":
        from openai import OpenAI
        from src.inference.openai_provider import OpenAIProvider
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return OpenAIProvider(client, args.model)
    elif args.provider == "gemini":
        from google import genai
        from src.inference.gemini_provider import GeminiProvider
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        return GeminiProvider(client, args.model)
    else:
        raise ValueError(f"Unknown provider: {args.provider}")


def _load_schema(args, schema_name: str) -> dict:
    """Load JSON schema from explicit path or auto-detect by name."""
    if args.schema:
        with open(args.schema, "r", encoding="utf-8") as f:
            return json.load(f)
    return load_schema(schema_name, "v2")


def _load_prompt(args, step_name: str) -> str:
    """Load system prompt from explicit path or auto-detect by step."""
    return load_system_prompt(step_name, path=args.system_prompt)


def run_step(step: str, args) -> None:
    """Execute a single pipeline step."""
    input_dir = str(PROJECT_ROOT / args.input_dir)
    output_dir = str(PROJECT_ROOT / args.output_dir)

    if step == "inference-cr":
        from src.inference.orchestrator import run_pipeline_step
        provider = _create_provider(args)
        system_prompt = _load_prompt(args, "chart_review")
        json_schema = _load_schema(args, "chart_review")
        run_pipeline_step(
            provider=provider,
            model_name=args.model,
            system_prompt=system_prompt,
            input_dir=input_dir,
            json_schema=json_schema,
            output_dir=output_dir,
            overwrite=args.overwrite,
        )

    elif step == "inference-fb":
        from src.inference.orchestrator import run_pipeline_step
        provider = _create_provider(args)
        system_prompt = _load_prompt(args, "feedback")
        json_schema = _load_schema(args, "cr_feedback")
        run_pipeline_step(
            provider=provider,
            model_name=args.model,
            system_prompt=system_prompt,
            input_dir=input_dir,
            json_schema=json_schema,
            output_dir=output_dir,
            overwrite=args.overwrite,
        )

    elif step == "drug-pricing":
        import pandas as pd
        from src.enrichment.drug_pricing import extract_medications

        umls_api_key = os.getenv("UMLS_API_KEY")
        pricing_df1 = pd.read_csv(
            PROJECT_ROOT / "drug_pricing" / "walmart_drug_pricing.csv",
            usecols=["source", "generic_drug_name", "30_day_cost"],
        )
        pricing_df2 = pd.read_csv(
            PROJECT_ROOT / "drug_pricing" / "costplus_drug_pricing_cleaned.csv",
            usecols=["source", "generic_drug_name", "30_day_cost"],
        )
        extract_medications(
            args.model, output_dir,
            pricing_dfs=[pricing_df1, pricing_df2],
            model="en_core_sci_md",
            umls_api_key=umls_api_key,
        )

    elif step == "pdf-cr":
        from src.rendering.chart_review_pdf import chart_review_json_to_pdf
        chart_review_json_to_pdf(args.model, output_dir)

    elif step == "pdf-fb":
        from src.rendering.feedback_pdf import cr_feedback_json_to_pdf
        cr_feedback_json_to_pdf(args.model, output_dir)

    elif step == "pdf-aggregate":
        from src.rendering.aggregate_pdf import aggregate_feedback
        aggregate_feedback(args.model, output_dir)

    else:
        raise ValueError(f"Unknown step: {step}")


def main():
    parser = build_parser()
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")

    if args.step == "all":
        all_steps = [
            "inference-cr", "inference-fb", "drug-pricing",
            "pdf-cr", "pdf-fb", "pdf-aggregate",
        ]
        for step in all_steps:
            print(f"\n{'='*60}")
            print(f"Running step: {step}")
            print(f"{'='*60}\n")
            run_step(step, args)
    else:
        run_step(args.step, args)


if __name__ == "__main__":
    main()
