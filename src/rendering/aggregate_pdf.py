# Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
# Licensed under the Apache License, Version 2.0.
import os
import json
from jinja2 import Environment, BaseLoader
from weasyprint import HTML, CSS

css = CSS(string="""
@page {
  size: Letter;
  margin: 1in;
}
body {
  font-family: "SF Pro Text", sans-serif;
  margin: 0;
  line-height: 1.4;
}
h1 { font-family: Helvetica, sans-serif; font-size: 20pt; color: #558a86; margin:0.5em 0 0.2em; }
h2 { font-family: Helvetica, sans-serif; font-size: 16pt; color: #558a86; margin:1em 0 0.3em; }
h3 { font-weight: bold; font-size: 11pt; margin:0; padding:0; }
p  { font-size: 10pt; margin: 0.2em 0; }

.status-bar {
  background: #dddddd;
  border-radius: 4px;
  overflow: hidden;
  height: 0.8em;
  margin: 0.4em 0 0.8em;
}
.status-fill {
  height: 100%;
}
.section { margin-bottom: 1em; }

.severity-badge {
  display: inline-block;
  padding: 0.1em 0.45em;
  border-radius: 4px;
  font-size: 9pt;
  font-weight: bold;
  color: white;
  margin-left: 0.4em;
  vertical-align: middle;
}
.severity-critical { background-color: #e57373; }
.severity-high     { background-color: #f77e5e; }
.severity-moderate { background-color: #ffd54f; color: #333; }

.summary-box {
  background-color: #f5f5f5;
  border-radius: 6px;
  padding: 0.6em 1em;
  margin-bottom: 1.5em;
}
.summary-box h2 { margin-top: 0; }
.summary-row {
  display: inline-block;
  margin-right: 1.5em;
  font-size: 10pt;
}
""")

ASSESSMENT_RANK = {
    "Critical Gap": 1,
    "Needs Improvement": 2,
    "Meets Expectations": 3,
    "Excellent": 4,
}

SEVERITY_RANK = {"Critical": 4, "High": 3, "Moderate": 2, "Low": 1}

RATINGS = {
    name: {"percent": (rank * 25), "color": color}
    for name, (rank, color) in {
        "Critical Gap":      (1, "#e57373"),
        "Needs Improvement": (2, "#ffd54f"),
        "Meets Expectations":(3, "#81d4fa"),
        "Excellent":         (4, "#81c784"),
    }.items()
}

AGGREGATE_TEMPLATE = Environment(loader=BaseLoader()).from_string(r"""
<!DOCTYPE html>
<html><body>
  <h1>Aggregated Feedback Report</h1>

  {% if severity_dist %}
  <div class="summary-box">
    <h2>Severity Distribution</h2>
    {% for level, count in severity_dist.items() %}
      <span class="summary-row">
        {% if level != "Low" %}<span class="severity-badge severity-{{ level|lower }}">{{ level }}</span>{% else %}<strong>{{ level }}</strong>{% endif %}
        {{ count }}
      </span>
    {% endfor %}
  </div>
  {% endif %}

  {% for pname, vals in data["Aggregated Problems"].items() %}
    <h2>{{ pname }}{% if vals.get("Severity") and vals["Severity"] != "Low" %} <span class="severity-badge severity-{{ vals['Severity']|lower }}">{{ vals["Severity"] }}</span>{% endif %}</h2>

    <h3>Strengths</h3>
    <div class="section">
      {% for line in vals["Strengths"].split('\n') %}
        <p>{{ line }}</p>
      {% endfor %}
    </div>

    <h3>Areas for Improvement</h3>
    <div class="section">
      {% for line in vals["Areas for Improvement"].split('\n') %}
        <p>{{ line }}</p>
      {% endfor %}
    </div>

    <h3>Skill Assessment</h3>
    <div class="status-bar">
      <div class="status-fill"
           style="width:{{ ratings[vals['Skill Assessment']].percent }}%;
                  background-color:{{ ratings[vals['Skill Assessment']].color }};">
      </div>
    </div>
  {% endfor %}
</body></html>
""")


def aggregate_feedback(model_name: str, output_dir: str) -> None:
    """Aggregate feedback across all patients and render to PDF.

    Reads all <output_dir>/<model_name>/cr_feedback/*.json,
    merges per-problem entries by Problem Name, consolidates
    strengths & areas, downgrades skill-assessments as needed,
    and writes one PDF + HTML.
    """
    json_dir = os.path.join(output_dir, model_name, "cr_feedback")
    problems = {}

    print(f"Aggregating feedback from: {json_dir}")
    for fname in os.listdir(json_dir):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(json_dir, fname)
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"  Skipping {fname}: invalid JSON")
                continue

        details = data.get("Feedback Details", {})

        # v2 format: problems is an array
        if "problems" in details:
            problem_list = details["problems"]
        else:
            # v1 fallback: collect Problem N keys
            problem_list = [
                content for section, content in details.items()
                if section.startswith("Problem") and isinstance(content, dict)
            ]

        for content in problem_list:
            pname = content.get("Problem Name")
            if not pname:
                continue

            entry = problems.setdefault(pname, {
                "Strengths": "",
                "Areas for Improvement": "",
                "Skill Assessment": "Excellent",
                "Severity": "Low",
            })

            s = content.get("Strengths", "").strip()
            if s:
                entry["Strengths"] += (s if not entry["Strengths"] else "\n" + s)

            a = content.get("Areas for Improvement", "").strip()
            if a:
                entry["Areas for Improvement"] += (a if not entry["Areas for Improvement"] else "\n" + a)

            current = entry["Skill Assessment"]
            new = content.get("Skill Assessment", current)
            if ASSESSMENT_RANK.get(new, 0) < ASSESSMENT_RANK.get(current, 0):
                entry["Skill Assessment"] = new

            # Track worst severity across patients
            current_sev = entry["Severity"]
            new_sev = content.get("Severity", current_sev)
            if SEVERITY_RANK.get(new_sev, 0) > SEVERITY_RANK.get(current_sev, 0):
                entry["Severity"] = new_sev

    # Sort problems by worst severity (Critical first)
    sorted_problems = dict(
        sorted(
            problems.items(),
            key=lambda item: SEVERITY_RANK.get(item[1].get("Severity", "Low"), 0),
            reverse=True,
        )
    )

    # Build severity distribution summary
    severity_dist = {"Critical": 0, "High": 0, "Moderate": 0, "Low": 0}
    for vals in sorted_problems.values():
        sev = vals.get("Severity", "Low")
        if sev in severity_dist:
            severity_dist[sev] += 1

    print(f"Aggregated {len(sorted_problems)} problems.")
    print("Generating PDF...")
    aggregated_data = {"Aggregated Problems": sorted_problems}
    html = AGGREGATE_TEMPLATE.render(
        data=aggregated_data, ratings=RATINGS, severity_dist=severity_dist,
    )
    out_pdf = os.path.join(output_dir, model_name, "cr_feedback", "aggregated_feedback.pdf")
    HTML(string=html).write_pdf(out_pdf, stylesheets=[css])
    print(f"Saved aggregated report to: {out_pdf}")

    out_html = os.path.splitext(out_pdf)[0] + ".html"
    with open(out_html, "w", encoding="utf-8") as f_html:
        f_html.write(html)
    print(f"Saved aggregated report HTML to: {out_html}")
