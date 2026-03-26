import logging
import os
from typing import List
import pandas as pd
import json
import spacy
import scispacy
from scispacy.abbreviation import AbbreviationDetector
from scispacy.umls_linking import UmlsEntityLinker
from scispacy.linking import EntityLinker
from spacy.tokens import Span

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
)
logger.addHandler(handler)


def load_medication_pipeline(
    model: str = "en_core_sci_md",
    umls_api_key: str = None
) -> spacy.Language:
    """Load a SciSpacy pipeline configured for UMLS linking of medications only."""
    if not umls_api_key:
        raise ValueError("Must pass your UMLS_API_KEY to load the UmlsEntityLinker.")

    nlp = spacy.load(model)
    nlp.add_pipe("abbreviation_detector")
    nlp.add_pipe(
        "scispacy_linker",
        config={"resolve_abbreviations": True, "linker_name": "umls"}
    )
    return nlp


def flatten_text(data: dict) -> str:
    """Extract medication plan text from all problems in a chart review JSON.

    Supports both v2 (problems array) and v1 (fixed Problem N keys) formats.
    """
    pieces = []
    plan = data.get("Plan", {})

    # v2 format: problems is an array
    if "problems" in plan:
        for problem in plan["problems"]:
            med_plan = (problem.get("Treatment/Medication Plan")
                        or problem.get("Treatment Plan"))
            if med_plan:
                pieces.append(med_plan)
    else:
        # v1 fallback: iterate Plan dict values
        for problem in plan.values():
            if isinstance(problem, dict):
                med_plan = (problem.get("Treatment/Medication Plan")
                            or problem.get("Treatment Plan"))
                if med_plan:
                    pieces.append(med_plan)

    return "\n".join(pieces)


def extract_medications(
    model_name: str,
    output_dir: str,
    pricing_dfs: List[pd.DataFrame],
    model: str = "en_core_sci_md",
    umls_api_key: str = None
) -> pd.DataFrame:
    """Extract medication mentions via SciSpacy/UMLS and merge with pricing data.

    Parameters:
        model_name: Model identifier (for output path).
        output_dir: Base output directory.
        pricing_dfs: List of pricing DataFrames with columns
                     ['source', 'generic_drug_name', '30_day_cost'].
        model: SciSpacy model name.
        umls_api_key: UMLS API key for entity linker.

    Returns:
        DataFrame with medication pricing data.
    """
    nlp = load_medication_pipeline(model, umls_api_key)
    if "scispacy_linker" not in nlp.pipe_names:
        raise RuntimeError("NLP pipeline must include 'scispacy_linker'.")

    linker = nlp.get_pipe("scispacy_linker")
    print("Number of CUIs in KB:", len(linker.kb.cui_to_entity))
    meds: List[dict] = []

    DRUG_SEMANTIC_TYPES = {"T109", "T121", "T200"}

    drug_price_dir = os.path.join(output_dir, model_name, "chart_review/drug_pricing")
    os.makedirs(drug_price_dir, exist_ok=True)
    json_dir = os.path.join(output_dir, model_name, "chart_review")

    for json_file in os.listdir(json_dir):
        if json_file.endswith(".json"):
            json_path = os.path.join(json_dir, json_file)
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            text = flatten_text(data)
            print(f"Length of text: {len(text)}")
            print(f"First 250 characters: {text[:250]}")
            print("Document length:", len(text), "characters")
            print("NLP max allowed:", nlp.max_length, "characters")

            doc = nlp(text)
            logger.info(f"Identifying medications within: {json_file}...")
            for ent in doc.ents:
                logger.debug(f"Found entity: {ent.text}, UMLS entities: {ent._.kb_ents}")
                for cui, score in ent._.kb_ents:
                    try:
                        um_entity = linker.kb.cui_to_entity[cui]
                    except KeyError:
                        logger.debug(f"CUI {cui} not in KB; skipping.")
                        continue

                    if any(st in DRUG_SEMANTIC_TYPES for st in um_entity.types):
                        meds.append({
                            "mention": ent.text,
                            "cui": cui,
                            "generic_name": um_entity.canonical_name,
                            "link_score": score,
                        })
                        break

            if not meds:
                logger.info("No medication entities detected in input text.")
                continue

            meds_df = (
                pd.DataFrame(meds)
                .drop_duplicates(subset=["generic_name"])
                .assign(generic_lower=lambda df: df["generic_name"].str.lower())
            )

            logger.info("Looking up pricing data...")
            pricing_df = pd.concat(pricing_dfs, ignore_index=True)
            pricing_df = pricing_df.assign(
                generic_drug_name_lower=pricing_df["generic_drug_name"].str.strip().str.lower()
            )
            required_cols = {"source", "generic_drug_name", "30_day_cost"}
            if not required_cols.issubset(pricing_df.columns):
                raise ValueError(f"pricing_df must have columns {required_cols}")

            pricing_df = (
                pricing_df
                .copy()
                .assign(generic_drug_name_lower=lambda df: df["generic_drug_name"].str.lower())
            )

            result = meds_df.merge(
                pricing_df,
                left_on="generic_lower",
                right_on="generic_drug_name_lower",
                how="left"
            )

            missing = result.loc[result["source"].isna(), "generic_name"].unique()
            if len(missing):
                logger.warning(f"No pricing info for: {missing.tolist()}")
            result = result.dropna(subset=["source"])
            result = result.drop_duplicates(subset=["generic_name", "source"])
            result = result.drop(columns=["generic_lower", "generic_drug_name_lower", "link_score", "cui", "generic_drug_name"])
            result.columns = [col.replace("_", " ").title() for col in result.columns]
            json_data = result.to_json(orient='records')

            existing_pricing = data["Plan"].pop("Generic Drug Pricing", None)
            if existing_pricing is None:
                existing_pricing = []
            existing_pricing.extend(json.loads(json_data))
            data["Plan"]["Generic Drug Pricing"] = existing_pricing

            filename_base = json_file.replace(".json", "")
            json_file_path = os.path.join(drug_price_dir, filename_base + '_pricing.json')
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            logger.info(f"Saved drug pricing data to {json_file_path}")
