#!/usr/bin/env python3
# Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
# Licensed under the Apache License, Version 2.0.
"""Migrate v1 QuICR JSON outputs (fixed "Problem N" keys) to v2 format (problems arrays).

Usage:
    python scripts/migrate_v1_to_v2.py [--in-place] [--validate] [--dir <path>]

Default behaviour writes migrated files with a _v2 suffix alongside the originals.
Use --in-place to overwrite originals instead.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Keys under Plan that are NOT problems
PLAN_NON_PROBLEM_KEYS = {
    "Anticipatory Preventative Care",
    "Preventative Care",
    "Follow Up Care",
    "Generic Drug Pricing",
}


def is_chart_review(data: dict) -> bool:
    return "Plan" in data and "Feedback Details" not in data


def is_feedback(data: dict) -> bool:
    return "Feedback Details" in data


def migrate_chart_review(data: dict) -> dict:
    """Convert a v1 chart review JSON (fixed Problem keys) to v2 (problems array)."""
    plan = data.get("Plan", {})
    problems = []

    for key, value in plan.items():
        if key in PLAN_NON_PROBLEM_KEYS:
            continue
        if not isinstance(value, dict):
            continue
        # Skip the orphan "Problem " key (trailing space, no number)
        if key.strip() == "Problem":
            continue

        problem = {}

        # Determine problem name
        if "Problem Name" in value:
            problem["Problem Name"] = value["Problem Name"]
        else:
            # Older formats use the condition name as the key (e.g. "Atrial Fibrillation")
            problem["Problem Name"] = key

        problem["Status"] = value.get("Status", "")

        # Handle the typo variant of the diagnostic plan field
        diag = (value.get("Decision Making and Diagnostic Plan")
                or value.get("Decision Making and Diagnositic Plan")
                or "")
        problem["Decision Making and Diagnostic Plan"] = diag

        # Handle treatment plan field name variants
        treat = (value.get("Treatment/Medication Plan")
                 or value.get("Treatment Plan")
                 or "")
        problem["Treatment/Medication Plan"] = treat

        problem["Contingency Planning"] = value.get("Contingency Planning", "")
        problem["Considerations for Documentation Improvement"] = value.get(
            "Considerations for Documentation Improvement", "")
        problem["Considerations for Cost Effective Care Improvement"] = value.get(
            "Considerations for Cost Effective Care Improvement", "")

        problems.append(problem)

    # Build new Plan
    new_plan = {"problems": problems}

    # Handle Anticipatory Preventative Care (may be at top level, under Plan, or use shorter name)
    apc = (plan.get("Anticipatory Preventative Care")
           or data.get("Anticipatory Preventative Care")
           or plan.get("Preventative Care")
           or {})
    new_plan["Anticipatory Preventative Care"] = apc

    # Handle Follow Up Care (may be at top level or under Plan)
    fuc = plan.get("Follow Up Care") or data.get("Follow Up Care") or {}
    new_plan["Follow Up Care"] = fuc

    # Preserve Generic Drug Pricing if present
    pricing = plan.get("Generic Drug Pricing")
    if pricing is not None:
        new_plan["Generic Drug Pricing"] = pricing

    # Build new top-level structure
    result = {}
    for key in data:
        if key == "Plan":
            result["Plan"] = new_plan
        elif key in ("Anticipatory Preventative Care", "Follow Up Care"):
            continue  # already moved under Plan
        else:
            result[key] = data[key]

    # Ensure Plan is present even if original didn't have it
    if "Plan" not in result:
        result["Plan"] = new_plan

    return result


def migrate_feedback(data: dict) -> dict:
    """Convert a v1 feedback JSON (fixed Problem keys) to v2 (problems array)."""
    details = data.get("Feedback Details", {})
    problems = []
    new_details = {}

    for key, value in details.items():
        if key.startswith("Problem") and isinstance(value, dict):
            problems.append(value)
        else:
            new_details[key] = value

    # Insert problems array after Assessment Section if present
    ordered_details = {}
    if "Assessment Section" in new_details:
        ordered_details["Assessment Section"] = new_details.pop("Assessment Section")
    ordered_details["problems"] = problems
    ordered_details.update(new_details)

    return {
        "Feedback Summary": data.get("Feedback Summary", ""),
        "Feedback Details": ordered_details,
    }


def migrate_file(filepath: Path, in_place: bool = False, validate: bool = False) -> bool:
    """Migrate a single JSON file. Returns True if migration was performed."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"  SKIP {filepath}: cannot read ({e})")
        return False

    if not content.strip():
        print(f"  SKIP {filepath}: empty file")
        return False

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  SKIP {filepath}: invalid JSON ({e})")
        return False

    if not isinstance(data, dict):
        print(f"  SKIP {filepath}: top-level is not an object")
        return False

    # Already migrated?
    if is_chart_review(data) and "problems" in data.get("Plan", {}):
        print(f"  SKIP {filepath}: already v2 format")
        return False
    if is_feedback(data) and "problems" in data.get("Feedback Details", {}):
        print(f"  SKIP {filepath}: already v2 format")
        return False

    # Determine type and migrate
    if is_chart_review(data):
        migrated = migrate_chart_review(data)
        n_problems = len(migrated["Plan"]["problems"])
        print(f"  OK   {filepath}: chart review, {n_problems} problems")
    elif is_feedback(data):
        migrated = migrate_feedback(data)
        n_problems = len(migrated["Feedback Details"]["problems"])
        print(f"  OK   {filepath}: feedback, {n_problems} problems")
    else:
        print(f"  SKIP {filepath}: unrecognized format (no Plan or Feedback Details)")
        return False

    if validate:
        _validate_migrated(migrated, filepath)

    # Write output
    if in_place:
        out_path = filepath
    else:
        out_path = filepath.with_stem(filepath.stem + "_v2")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(migrated, f, indent=2)

    return True


def _validate_migrated(data: dict, filepath: Path):
    """Basic structural validation of migrated data."""
    if is_chart_review(data):
        plan = data.get("Plan", {})
        problems = plan.get("problems", [])
        if not problems:
            print(f"  WARN {filepath}: no problems after migration")
        for i, p in enumerate(problems):
            if not p.get("Problem Name"):
                print(f"  WARN {filepath}: problem {i} missing Problem Name")
            if "Decision Making and Diagnositic Plan" in p:
                print(f"  WARN {filepath}: problem {i} still has typo field name")
    elif is_feedback(data):
        details = data.get("Feedback Details", {})
        problems = details.get("problems", [])
        if not problems:
            print(f"  WARN {filepath}: no problems after migration")
        for i, p in enumerate(problems):
            if not p.get("Problem Name"):
                print(f"  WARN {filepath}: problem {i} missing Problem Name")


def main():
    parser = argparse.ArgumentParser(description="Migrate QuICR v1 JSONs to v2 array format")
    parser.add_argument("--in-place", action="store_true",
                        help="Overwrite original files instead of writing _v2 suffix")
    parser.add_argument("--validate", action="store_true",
                        help="Run structural validation after migration")
    parser.add_argument("--dir", default="generated_output",
                        help="Root directory to scan (default: generated_output)")
    args = parser.parse_args()

    root = Path(args.dir)
    if not root.is_dir():
        print(f"Error: {root} is not a directory")
        sys.exit(1)

    print(f"Scanning {root} for v1 JSON files...")
    migrated = 0
    skipped = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip usage directories (CSV files only)
        if "usage" in dirpath:
            continue
        for fname in sorted(filenames):
            if not fname.endswith(".json"):
                continue
            # Skip already-migrated _v2 files
            if fname.endswith("_v2.json"):
                continue
            filepath = Path(dirpath) / fname
            if migrate_file(filepath, in_place=args.in_place, validate=args.validate):
                migrated += 1
            else:
                skipped += 1

    print(f"\nDone. Migrated: {migrated}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
