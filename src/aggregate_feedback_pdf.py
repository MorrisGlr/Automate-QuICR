import os
import json
from jinja2 import Environment, BaseLoader
from weasyprint import HTML, CSS

# --- Page & typography CSS (same as your original) ---
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

/* Status bar container + fill */
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
""")

# --- Skill-assessment mapping for status bars ---
ASSESSMENT_RANK = {
    "Critical Gap": 1,
    "Needs Improvement": 2,
    "Meets Expectations": 3,
    "Excellent": 4,
}
RATINGS = {
    name: {"percent": (rank * 25), 
           "color": color}
    for name, (rank, color) in {
        "Critical Gap":      (1, "#e57373"),
        "Needs Improvement": (2, "#ffd54f"),
        "Meets Expectations":(3, "#81d4fa"),
        "Excellent":         (4, "#81c784"),
    }.items()
}

# --- Jinja template for the aggregated report ---
AGGREGATE_TEMPLATE = Environment(loader=BaseLoader()).from_string(r"""
<!DOCTYPE html>
<html><body>
  <h1>Aggregated Feedback Report</h1>
  {% for pname, vals in data["Aggregated Problems"].items() %}
    <h2>{{ pname }}</h2>

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

def aggregate_feedback(model_name: str, output_dir: str):
    """
    Reads all <output_dir>/<model_name>/cr_feedback/*.json,
    merges per-problem entries by Problem Name, consolidates
    strengths & areas, downgrades skill-assessments as needed,
    and writes one PDF.
    """
    json_dir = os.path.join(output_dir, model_name, "cr_feedback")
    problems = {}

    print(f"Aggregating feedback from: {json_dir}")
    for fname in os.listdir(json_dir):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(json_dir, fname)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        details = data.get("Feedback Details", {})
        for section, content in details.items():
            if not section.startswith("Problem"):
                continue
            pname = content.get("Problem Name")
            if not pname:
                continue

            entry = problems.setdefault(pname, {
                "Strengths": "",
                "Areas for Improvement": "",
                "Skill Assessment": "Excellent"
            })

            # merge strengths
            s = content.get("Strengths", "").strip()
            if s:
                entry["Strengths"] += (s if not entry["Strengths"] else "\n" + s)

            # merge areas
            a = content.get("Areas for Improvement", "").strip()
            if a:
                entry["Areas for Improvement"] += (a if not entry["Areas for Improvement"] else "\n" + a)

            # downgrade assessment if needed
            current = entry["Skill Assessment"]
            new = content.get("Skill Assessment", current)
            if ASSESSMENT_RANK.get(new, 0) < ASSESSMENT_RANK.get(current, 0):
                entry["Skill Assessment"] = new

    # render HTML + PDF
    print(f"Aggregated {len(problems)} problems.")
    print("Generating PDF...")
    aggregated_data = {"Aggregated Problems": problems}
    html = AGGREGATE_TEMPLATE.render(data=aggregated_data, ratings=RATINGS)
    out_pdf = os.path.join(output_dir, model_name, "cr_feedback", "aggregated_feedback.pdf")
    HTML(string=html).write_pdf(out_pdf, stylesheets=[css])
    print(f"Saved aggregated report to: {out_pdf}")

    # Save the rendered HTML for inspection
    out_html = os.path.splitext(out_pdf)[0] + ".html"
    with open(out_html, "w", encoding="utf-8") as f_html:
        f_html.write(html)
    print(f"Saved aggregated report HTML to: {out_html}")