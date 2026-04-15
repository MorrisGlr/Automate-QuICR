import json
import os

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
""")

# Skill assessment rating display config
RATINGS = {
    "Critical Gap":      {"percent":  25, "color": "#e57373"},
    "Needs Improvement": {"percent":  50, "color": "#ffd54f"},
    "Meets Expectations":{"percent":  75, "color": "#81d4fa"},
    "Excellent":         {"percent": 100, "color": "#81c784"},
}

template = Environment(loader=BaseLoader()).from_string(r"""
<!DOCTYPE html>
<html><body>

  <h1>Feedback Summary</h1>
  <div class="section">
    {% for line in data["Feedback Summary"].split('\n') %}
      <p>{{ line }}</p>
    {% endfor %}
  </div>

  <h1>Feedback Details</h1>

  {# Render Assessment Section first if present #}
  {% if data["Feedback Details"]["Assessment Section"] is defined %}
    <h2>Assessment Section</h2>
    {% set as_section = data["Feedback Details"]["Assessment Section"] %}
    {% for key, val in as_section.items() %}
      <h3>{{ key }}</h3>
      <div class="section">
        {% for line in val.split('\n') %}
          <p>{{ line }}</p>
        {% endfor %}
      </div>
    {% endfor %}
  {% endif %}

  {# Render problems array (v2) or Problem N keys (v1 fallback) #}
  {% if data["Feedback Details"]["problems"] is defined %}
    {% for problem in data["Feedback Details"]["problems"] %}
      <h2>{{ problem["Problem Name"] }}{% if problem.get("Severity") and problem["Severity"] != "Low" %} <span class="severity-badge severity-{{ problem['Severity']|lower }}">{{ problem["Severity"] }}</span>{% endif %}</h2>
      {% for key, val in problem.items() if key not in ["Problem Name", "Severity"] %}
        {% if key == "Skill Assessment" %}
          <h3>{{ key }}</h3>
          <div class="status-bar">
            <div class="status-fill"
                 style="width:{{ ratings[val].percent }}%;
                        background-color:{{ ratings[val].color }};">
            </div>
          </div>
        {% elif key == "Strengths" or key.startswith("Areas for Improvement") %}
          <h3>{{ key }}</h3>
          <div class="section">
            {% for line in val.split('\n') %}
              <p>{{ line }}</p>
            {% endfor %}
          </div>
        {% else %}
          <h3>{{ key }}</h3>
          <div class="section">
            {% for line in val.split('\n') %}
              <p>{{ line }}</p>
            {% endfor %}
          </div>
        {% endif %}
      {% endfor %}
    {% endfor %}
  {% else %}
    {# v1 fallback #}
    {% for section, content in data["Feedback Details"].items() %}
      {% if section.startswith("Problem") %}
        <h2>{{ section }}</h2>
        {% for key, val in content.items() %}
          {% if key == "Skill Assessment" %}
            <h3>{{ key }}</h3>
            <div class="status-bar">
              <div class="status-fill"
                   style="width:{{ ratings[val].percent }}%;
                          background-color:{{ ratings[val].color }};">
              </div>
            </div>
          {% else %}
            <h3>{{ key }}</h3>
            <div class="section">
              {% for line in val.split('\n') %}
                <p>{{ line }}</p>
              {% endfor %}
            </div>
          {% endif %}
        {% endfor %}
      {% endif %}
    {% endfor %}
  {% endif %}

  {# Render remaining non-problem sections #}
  {% for section_name in ["Anticipatory Preventative Care Section Feedback", "Follow Up Care Feedback"] %}
    {% if data["Feedback Details"][section_name] is defined %}
      <h2>{{ section_name }}</h2>
      {% set sec = data["Feedback Details"][section_name] %}
      {% if sec is string %}
        <div class="section">
          {% for line in sec.split('\n') %}
            <p>{{ line }}</p>
          {% endfor %}
        </div>
      {% else %}
        {% for key, val in sec.items() %}
          {% if val is string %}
            <h3>{{ key }}</h3>
            <div class="section">
              {% for line in val.split('\n') %}
                <p>{{ line }}</p>
              {% endfor %}
            </div>
          {% elif val is mapping %}
            <h2>{{ key }}</h2>
            {% for subkey, subval in val.items() %}
              {% if subval is string %}
                <h3>{{ subkey }}</h3>
                <div class="section">
                  {% for line in subval.split('\n') %}
                    <p>{{ line }}</p>
                  {% endfor %}
                </div>
              {% endif %}
            {% endfor %}
          {% endif %}
        {% endfor %}
      {% endif %}
    {% endif %}
  {% endfor %}

  {% if data["Feedback Details"]["Overall Recommendations"] is defined %}
    <h2>Overall Recommendations</h2>
    <div class="section">
      {% for line in data["Feedback Details"]["Overall Recommendations"].split('\n') %}
        <p>{{ line }}</p>
      {% endfor %}
    </div>
  {% endif %}

</body></html>
""")


def cr_feedback_json_to_pdf(model_name: str, output_dir: str) -> None:
    """Render feedback JSON files to PDF.

    Reads from <output_dir>/<model_name>/cr_feedback/ and writes PDFs to
    <output_dir>/<model_name>/cr_feedback/pdf/.
    """
    pdf_dir = os.path.join(output_dir, model_name, "cr_feedback/pdf")
    os.makedirs(pdf_dir, exist_ok=True)
    json_dir = os.path.join(output_dir, model_name, "cr_feedback")

    for json_file in os.listdir(json_dir):
        if json_file.endswith(".json"):
            json_path = os.path.join(json_dir, json_file)
            with open(json_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    print(f"Skipping {json_file}: invalid JSON")
                    continue

            print(f"Processing {json_file} file generated by {model_name} for PDF formatting...")
            html = template.render(data=data, ratings=RATINGS)

            base_filename = json_file.replace(".json", "")
            pdf_filename = f"{base_filename}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)
            HTML(string=html).write_pdf(pdf_path, stylesheets=[css])
            print(f"Saved {json_file} as PDF: {pdf_path}")
