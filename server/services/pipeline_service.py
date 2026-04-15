import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from server.config import settings


@dataclass
class PipelineEvent:
    stage: str
    file: str
    progress: int
    total: int
    error: str | None = None
    results: dict | None = None


# In-memory job registry (local-only server, no persistence needed)
_jobs: dict[str, asyncio.Queue[PipelineEvent]] = {}


def create_job() -> tuple[str, asyncio.Queue[PipelineEvent]]:
    job_id = str(uuid.uuid4())
    queue: asyncio.Queue[PipelineEvent] = asyncio.Queue()
    _jobs[job_id] = queue
    return job_id, queue


def get_job_queue(job_id: str) -> asyncio.Queue[PipelineEvent] | None:
    return _jobs.get(job_id)


def remove_job(job_id: str) -> None:
    _jobs.pop(job_id, None)


async def _emit(queue: asyncio.Queue, stage: str, file: str, progress: int, total: int, **kwargs: Any) -> None:
    await queue.put(PipelineEvent(stage=stage, file=file, progress=progress, total=total, **kwargs))


def _create_provider(provider_name: str, model_name: str):
    """Create an inference provider (mirrors app.py logic)."""
    if provider_name == "openai":
        from openai import OpenAI
        from src.inference.openai_provider import OpenAIProvider
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return OpenAIProvider(client, model_name)
    elif provider_name == "gemini":
        from google import genai
        from src.inference.gemini_provider import GeminiProvider
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        return GeminiProvider(client, model_name)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


async def run_pipeline_for_files(
    filenames: list[str],
    model_name: str,
    provider_name: str,
    queue: asyncio.Queue[PipelineEvent],
) -> None:
    """Run the full pipeline for uploaded files with SSE progress reporting."""
    from functools import partial
    from src.utils.schema import load_schema, load_system_prompt
    from src.evidence.pubmed import build_evidence_context
    from src.severity.rules import apply_severity_validation
    from src.evidence.grading import enrich_evidence_metadata

    total = len(filenames)
    failures: list[dict] = []
    input_dir = str(settings.data_path)
    output_dir = str(settings.output_path)

    # Load schemas and prompts
    cr_schema = load_schema("chart_review", "v2")
    fb_schema = load_schema("cr_feedback", "v2")
    cr_prompt = load_system_prompt("chart_review")
    fb_prompt = load_system_prompt("feedback")

    # Set up output directories
    cr_subdir = os.path.join(output_dir, model_name, "chart_review")
    fb_subdir = os.path.join(output_dir, model_name, "cr_feedback")
    stats_subdir = os.path.join(output_dir, model_name, "usage")
    cache_dir = os.path.join(output_dir, model_name, "evidence_cache")
    for d in [cr_subdir, fb_subdir, stats_subdir, cache_dir]:
        os.makedirs(d, exist_ok=True)

    # Create provider
    provider = await asyncio.to_thread(_create_provider, provider_name, model_name)

    evidence_fn = partial(
        build_evidence_context,
        api_key=os.getenv("NCBI_API_KEY"),
        cache_dir=cache_dir,
    )

    for i, filename in enumerate(filenames, 1):
        base = filename.replace(".txt", "")
        filepath = os.path.join(input_dir, filename)

        try:
            # Read EMR text
            with open(filepath, "r", encoding="utf-8") as f:
                emr_text = f.read()

            # Stage 1: Evidence retrieval
            await _emit(queue, "retrieving_evidence", filename, i, total)
            evidence_text, retrieved_sources = await asyncio.to_thread(
                evidence_fn, emr_text
            )
            user_prompt_cr = emr_text
            if evidence_text:
                user_prompt_cr = f"{emr_text}\n{evidence_text}"

            # Stage 2: Chart review inference
            await _emit(queue, "running_inference_cr", filename, i, total)
            cr_result, cr_usage = await asyncio.to_thread(
                provider.run_inference, cr_prompt, user_prompt_cr, cr_schema
            )

            # Post-process: move sections under Plan
            if "Plan" in cr_result:
                plan = cr_result.setdefault("Plan", {})
                if isinstance(plan, dict):
                    for section in ("Anticipatory Preventative Care", "Follow Up Care"):
                        if section in cr_result and section not in plan:
                            plan[section] = cr_result.pop(section)

            # Stage 3: Severity validation
            await _emit(queue, "validating_severity", filename, i, total)
            cr_result = await asyncio.to_thread(
                apply_severity_validation, cr_result, None
            )

            # Citation validation
            if retrieved_sources:
                cr_result = await asyncio.to_thread(
                    enrich_evidence_metadata, cr_result, retrieved_sources
                )

            # Save chart review
            cr_path = os.path.join(cr_subdir, f"{base}_chart_review.json")
            with open(cr_path, "w", encoding="utf-8") as f:
                json.dump(cr_result, f, indent=2)

            # Stage 4: Feedback inference
            await _emit(queue, "running_inference_fb", filename, i, total)
            user_prompt_fb = f"{emr_text}\n# Chart Review for Feedback\n{json.dumps(cr_result)}"
            fb_result, fb_usage = await asyncio.to_thread(
                provider.run_inference, fb_prompt, user_prompt_fb, fb_schema
            )

            # Save feedback
            fb_path = os.path.join(fb_subdir, f"{base}_cr_feedback.json")
            with open(fb_path, "w", encoding="utf-8") as f:
                json.dump(fb_result, f, indent=2)

            # Stage 5: Drug pricing (per-file)
            await _emit(queue, "extracting_medications", filename, i, total)
            try:
                await asyncio.to_thread(
                    _run_drug_pricing_single, base, model_name, output_dir
                )
            except Exception:
                pass  # Drug pricing is optional; don't fail the pipeline

            # Stage 6: PDF generation
            await _emit(queue, "generating_pdf", filename, i, total)
            # PDF generation uses the full-directory functions, skip per-file

            await _emit(queue, "complete", filename, i, total)

        except Exception as e:
            failures.append({"file": filename, "error": str(e)})
            await _emit(queue, "failed", filename, i, total, error=str(e))

    # Generate PDFs as a batch after all files
    try:
        from src.rendering.chart_review_pdf import chart_review_json_to_pdf
        from src.rendering.feedback_pdf import cr_feedback_json_to_pdf
        from src.rendering.aggregate_pdf import aggregate_feedback
        await asyncio.to_thread(chart_review_json_to_pdf, model_name, output_dir)
        await asyncio.to_thread(cr_feedback_json_to_pdf, model_name, output_dir)
        await asyncio.to_thread(aggregate_feedback, model_name, output_dir)
    except Exception:
        pass  # PDF generation failure is non-fatal

    await _emit(
        queue, "all_complete", "", total, total,
        results={"processed": total - len(failures), "failures": failures},
    )


def _run_drug_pricing_single(base: str, model_name: str, output_dir: str) -> None:
    """Run drug pricing enrichment for existing chart review files."""
    import pandas as pd
    from src.enrichment.drug_pricing import extract_medications

    umls_api_key = os.getenv("UMLS_API_KEY")
    project_root = settings.project_root
    pricing_df1 = pd.read_csv(
        project_root / "drug_pricing" / "walmart_drug_pricing.csv",
        usecols=["source", "generic_drug_name", "30_day_cost"],
    )
    pricing_df2 = pd.read_csv(
        project_root / "drug_pricing" / "costplus_drug_pricing_cleaned.csv",
        usecols=["source", "generic_drug_name", "30_day_cost"],
    )
    extract_medications(
        model_name, output_dir,
        pricing_dfs=[pricing_df1, pricing_df2],
        model="en_core_sci_md",
        umls_api_key=umls_api_key,
    )
