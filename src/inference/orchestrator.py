import glob
import json
import os
import time
from collections.abc import Callable

import pandas as pd

from src.inference.base import InferenceProvider


def run_pipeline_step(
    provider: InferenceProvider,
    model_name: str,
    system_prompt: str,
    input_dir: str,
    json_schema: dict,
    output_dir: str,
    overwrite: bool = False,
    evidence_context_fn: Callable[[str], tuple[str, list[dict]]] | None = None,
    severity_validator: Callable[[dict, dict | None], dict] | None = None,
    citation_validator: Callable[[dict, list[dict]], dict] | None = None,
) -> None:
    """Orchestrate inference across all input files in a directory.

    Args:
        provider: An InferenceProvider instance (OpenAI or Gemini).
        model_name: Model identifier for output path namespacing.
        system_prompt: System prompt text.
        input_dir: Directory containing *.txt EMR input files.
        json_schema: JSON schema dict (must have 'name' key).
        output_dir: Base output directory.
        overwrite: If True, regenerate existing outputs.
        evidence_context_fn: Optional callable that takes EMR text and returns
            (evidence_text, retrieved_sources) for in-context RAG.
        severity_validator: Optional callable that takes (chart_review, feedback)
            and returns chart_review with validated severities.
        citation_validator: Optional callable that takes (chart_review, retrieved_sources)
            and returns chart_review with citation flags.
    """
    stats_list = []
    schema_name = json_schema["name"]

    output_subdir = os.path.join(output_dir, model_name, schema_name)
    os.makedirs(output_subdir, exist_ok=True)
    stats_subdir = os.path.join(output_dir, model_name, "usage")
    os.makedirs(stats_subdir, exist_ok=True)

    for path in sorted(glob.glob(os.path.join(input_dir, "*.txt"))):
        filename = os.path.basename(path)
        base_filename = filename.replace(".txt", "")
        output_filename = f"{base_filename}_{schema_name}.json"
        output_filepath = os.path.join(output_subdir, output_filename)

        if not overwrite and os.path.exists(output_filepath):
            print(f"Generated text for {filename} already exists. Skipping...")
            continue

        with open(path, "r", encoding="utf-8") as f:
            user_prompt = f.read()

        # Evidence retrieval (in-context RAG) for chart review
        retrieved_sources = []
        if schema_name == "chart_review" and evidence_context_fn is not None:
            print(f"Retrieving evidence context for {filename}...")
            evidence_text, retrieved_sources = evidence_context_fn(user_prompt)
            if evidence_text:
                user_prompt = f"{user_prompt}\n{evidence_text}"
                print(f"Appended evidence context ({len(retrieved_sources)} sources)")

        # For feedback schema, append the corresponding chart review JSON
        if schema_name == "cr_feedback":
            print(f"JSON schema name: {schema_name}")
            cr_subdir = os.path.join(output_dir, model_name, "chart_review")
            chart_review_filename = f"{base_filename}_chart_review.json"
            chart_review_filepath = os.path.join(cr_subdir, chart_review_filename)
            if os.path.exists(chart_review_filepath):
                with open(chart_review_filepath, "r", encoding="utf-8") as f:
                    chart_review_json = json.load(f)
                user_prompt = f"{user_prompt}\n# Chart Review for Feedback\n{json.dumps(chart_review_json)}"
                print(f"Using chart review JSON for {filename} from {chart_review_filename}")

        print(
            f"Generating text for {filename} using {model_name} "
            f"with {schema_name} JSON structured output..."
        )

        try:
            result, usage_dict = provider.run_inference(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_schema=json_schema,
            )
        except Exception as e:
            print(f"Error during inference for {filename}: {e}")
            continue

        print(f"Text generation complete for {filename} in {usage_dict.get('time_to_generate', '?')} seconds.")

        # Post-processing: move sections under Plan if they ended up at top level
        if "Plan" in result:
            plan = result.setdefault("Plan", {})
            if not isinstance(plan, dict):
                print(f"Warning: 'Plan' is not a dict in {filename}, skipping post-processing")
            else:
                for section in ("Anticipatory Preventative Care", "Follow Up Care"):
                    if section in result and section not in plan:
                        print(f"Conforming generated JSON: moving {section} to Plan")
                        plan[section] = result.pop(section)

        # Post-hoc severity validation
        if severity_validator is not None and schema_name == "chart_review":
            # Load corresponding feedback if it exists (for skill assessment floors)
            feedback_data = None
            fb_subdir = os.path.join(output_dir, model_name, "cr_feedback")
            fb_filename = f"{base_filename}_cr_feedback.json"
            fb_filepath = os.path.join(fb_subdir, fb_filename)
            if os.path.exists(fb_filepath):
                with open(fb_filepath, "r", encoding="utf-8") as f:
                    feedback_data = json.load(f)
            result = severity_validator(result, feedback_data)
            adj = result.get("_severity_adjustments", [])
            if adj:
                print(f"Severity adjustments for {filename}: {len(adj)} problem(s) escalated")

        # Post-hoc citation validation
        if citation_validator is not None and retrieved_sources and schema_name == "chart_review":
            result = citation_validator(result, retrieved_sources)
            flags = result.get("_citation_flags", [])
            if flags:
                print(f"Citation flags for {filename}: {sum(len(f['flagged_citations']) for f in flags)} unverified")

        # Write output
        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        # Build stats
        usage_dict["input_filename"] = filename
        usage_dict["output_filename"] = output_filename
        usage_dict["model_name"] = model_name
        usage_dict["json_schema"] = schema_name
        print(
            f"Usage stats: (input_tokens: {usage_dict.get('input_tokens')}, "
            f"output_tokens: {usage_dict.get('output_tokens')}, "
            f"total_tokens: {usage_dict.get('total_tokens')})\n"
        )
        stats_list.append(usage_dict)

    # Save stats CSV
    if stats_list:
        stats_df = pd.DataFrame(stats_list)
        file_name_date_time = time.strftime("%Y%m%d-%H%M%S")
        stats_filename = f"inference_stats_{schema_name}_{file_name_date_time}.csv"
        stats_filepath = os.path.join(stats_subdir, stats_filename)
        stats_df.to_csv(stats_filepath, index=False)
