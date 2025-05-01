import json
from jinja2 import Environment, BaseLoader
from weasyprint import HTML, CSS
import os

# ——————————————————————————————————————————————————————————————
# CSS implementing Swiss design principles, font‑faces, grid, colors, spacing
css_string = """
@page {
  size: Letter;       /* 8.5in × 11in */
  margin: 1in;        /* top/right/bottom/left = 1in */
}
@font-face {
  font-family: "Helvetica";
  src: url("templates/fonts/Helvetica.ttf");
}
@font-face {
  font-family: "SF Pro Text";
  src: url("templates/fonts/SFProText-Regular.ttf") format("truetype");
  font-weight: normal;
}
@font-face {
  font-family: "SF Pro Text";
  src: url("templates/fonts/SFProText-Bold.ttf") format("truetype");
  font-weight: bold;
}

body {
  font-family: "SF Pro Text", sans-serif;
  color: #000;
  margin: 0;
  line-height: 1.4;
}
h1 {
  font-family: "Helvetica", sans-serif;
  font-size: 20pt;
  color: #558a86;  /* headers */
  margin-top: 0.1em;
  margin-bottom: 0.1em;
}
h2 {
  font-family: "Helvetica", sans-serif;
  font-size: 16pt;
  color: #558a86;
  margin-top: 1em;
  margin-bottom: 0.3em;
}
/* Level 3 headers – default black */
h3 {
  font-family: "SF Pro Text", sans-serif;
  font-weight: bold;
  font-size: 11pt;
  color: #000;
  margin: 0;
  padding: 0;
}
/* Orange for specific “Considerations…” items */
h3.consideration {
  color: #f77e5e;
}
/* Highlight box for MDM improvements */
.highlight-box {
  background-color: #dfe0e2;
  border-radius: 6px;
  padding: 0.4em 0.8em;
  margin-top: 1.5em;
  margin-bottom: 1.5em;
}
.highlight-box h2 {
  margin-top: 0;              /* eliminate the 1em gap inside the box */
  margin-bottom: 0.3em;       /* just enough space before the list */
}
/* Remove grid – simple block flow */
.no-grid {
  display: block;
  margin-bottom: 1em;
}
/* Two‑column layout for key/value rows */
.row {
  display: grid;
  grid-template-columns: 30% 70%;
  column-gap: 1em;
  align-items: start;
  margin-bottom: 0.5em;
}
/* Generic drug pricing table */
table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1em;
}
th, td {
  border: 1px solid #ccc;
  padding: 0.3em 0.5em;
  text-align: left;
}
thead {
  background-color: #f0f0f0;
}
/* Body text paragraphs */
p {
  font-family: "SF Pro Text", sans-serif;
  font-size: 10pt;
  margin: 0;
}
"""

# ——————————————————————————————————————————————————————————————
# Jinja2 template: map JSON keys → H1, H2, H3, highlight box
template_string = """
{% macro render_highlights(key, value) %}
  <div class="highlight-box no-grid">
    <h2>{{ key }}</h2>
    {% for line in value.split('\n') %}
      <p>{{ line }}</p>
    {% endfor %}
  </div>
{% endmacro %}

{% macro render_string(key, value) %}
  <h1>{{ key }}</h1>
  <div class="no-grid">
    {% for line in value.split('\n') %}
      <p>{{ line }}</p>
    {% endfor %}
  </div>
{% endmacro %}

{% macro render_plan(plan) %}
  <h1>Plan</h1>
  {% for subkey, content in plan.items() %}
    {% if subkey.startswith("Problem") %}
      <h2>{{ content["Problem Name"] }}</h2>
      {% for field, txt in content.items() if field != "Problem Name" %}
        <div class="row">
          <h3 {% if "Considerations" in field %}class="consideration"{% endif %}>{{ field }}</h3>
          <p>{{ txt.replace('\n','<br/>') }}</p>
        </div>
      {% endfor %}
    {% elif subkey in ["Anticipatory Preventative Care", "Follow Up Care"] %}
      <h2>{{ subkey }}</h2>
      <div class="row">
        {% for item_key, item_val in content.items() %}
          <h3>{{ item_key }}</h3>
          <p>{{ item_val }}</p>
        {% endfor %}
      </div>
    {% elif subkey == "Generic Drug Pricing" %}
      {{ render_pricing(content) }}
    {% endif %}
  {% endfor %}
{% endmacro %}

{% macro render_mapping_list(key, mapping) %}
  <h2>{{ key }}</h2>
  <div class="no-grid">
    {% for subkey, subval in mapping.items() %}
      <h3>{{ subkey }}</h3>
      <p>{{ subval }}</p>
    {% endfor %}
  </div>
{% endmacro %}

{% macro render_pricing(rows) %}
  <h2>Generic Drug Pricing</h2>
  <table>
    <thead>
      <tr>
        <th>Mention</th>
        <th>Generic Name</th>
        <th>Source</th>
        <th>30 Day Cost</th>
      </tr>
    </thead>
    <tbody>
      {% for drug in rows %}
        <tr>
          <td>{{ drug["Mention"] }}</td>
          <td>{{ drug["Generic Name"] }}</td>
          <td>{{ drug["Source"] }}</td>
          <td>{{ drug["30 Day Cost"] }}</td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
{% endmacro %}

<!DOCTYPE html>
<html>
  <body>
  {% for key, value in data.items() %}
    {% if key.startswith("Key Highlights for Medical Decision-Making") %}
      {{ render_highlights(key, value) }}
    {% elif key == "Plan" %}
      {{ render_plan(value) }}
    {% elif value is string %}
      {{ render_string(key, value) }}
    {% elif value is sequence %}
      {{ render_string(key, value | join('\n')) }}
    {% elif value is mapping %}
      {# Fallback to mapping list for any other dict #}
      {{ render_mapping_list(key, value) }}
    {% endif %}
  {% endfor %}
  </body>
</html>
"""


def chart_review_json_to_pdf(model_name: str, output_dir: SyntaxWarning):
    pdf_dir = os.path.join(output_dir, model_name, "chart_review/pdf")
    os.makedirs(pdf_dir, exist_ok=True)
    json_dir = os.path.join(output_dir, model_name, "chart_review/drug_pricing")
    for json_file in os.listdir(json_dir):
        if json_file.endswith(".json"):
            json_path = os.path.join(json_dir, json_file)
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"Processing {json_file} file generated by {model_name}for PDF formatting...")
            # Render HTML
            env = Environment(loader=BaseLoader())
            tpl = env.from_string(template_string)
            html_out = tpl.render(data=data)

            # Write PDF
            base_filename = json_file.replace(".json", "")
            pdf_filename = f"{base_filename}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)
            HTML(string=html_out).write_pdf(pdf_path, stylesheets=[CSS(string=css_string)])
            print(f"Saved {json_file} as PDF: {pdf_path}")