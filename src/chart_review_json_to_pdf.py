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
<!DOCTYPE html>
<html>
  <body>
  {% for key, value in data.items() %}

    {# — Key Highlights — #}
    {% if key.startswith("Key Highlights for Medical Decision-Making") %}
      <div class="highlight-box no-grid">
        <h2>{{ key }}</h2>
        {% if value is string %}
          {% for line in value.split('\\n') %}
            <p>{{ line }}</p>
          {% endfor %}
        {% elif value is iterable %}
          {% for item in value %}
            <p>{{ item }}</p>
          {% endfor %}
        {% endif %}
      </div>

    {# — Top‑level strings (always catch strings first!) — #}
    {% elif value is string %}
      <h1>{{ key }}</h1>
      <div class="no-grid">
        {% for line in value.split('\n') %}
          <p>{{ line }}</p>
        {% endfor %}
      </div>

    {# — Any actual lists (now only real lists, not strings) — #}
    {% elif value is iterable and not value is string and not value is mapping %}
      <h1>{{ key }}</h1>
      <div class="no-grid">
        {% for item in value %}
          <p>{{ item }}</p>
        {% endfor %}
      </div>

    {# — Plan: render each problem explicitly — #}
    {% elif key == "Plan" %}
      <h1>{{ key }}</h1>
     {% for prob in value.values() %}
       <h2>{{ prob["Problem Name"] }}</h2>
       {% for field, txt in prob.items() if field!="Problem Name" %}
         <div class="row">
           <h3 {% if "Considerations" in field %}class="consideration"{% endif %}>
             {{ field }}
           </h3>
           {# Only call replace on real strings #}
           {% if txt is string %}
             <p>{{ txt.replace('\\n','<br/>') }}</p>
           {% elif txt is mapping %}
             {# If somehow nested deeper, loop its items too #}
             {% for subk, subv in txt.items() %}
               <h3>{{ subk }}</h3>
               <p>{{ subv }}</p>
             {% endfor %}
           {% endif %}
         </div>
       {% endfor %}
     {% endfor %}

    {# — All other mappings (Anticipatory… / Follow Up… ) — #}
    {% elif value is mapping %}
      <h1>{{ key }}</h1>
      {% for subkey, subval in value.items() %}
        <h2>{{ subkey }}</h2>
        <div class="no-grid">
          {% if subval is string %}
            {% for line in subval.split('\\n') %}
              <p>{{ line }}</p>
            {% endfor %}
          {% elif subval is mapping %}
            {% for inner_k, inner_v in subval.items() %}
              <div class="row">
                <h3>{{ inner_k }}</h3>
                {% if inner_v is string %}
                  <p>{{ inner_v }}</p>
                {% endif %}
              </div>
            {% endfor %}
          {% endif %}
        </div>
      {% endfor %}
    {% endif %}

  {% endfor %}
  </body>
</html>
"""


def chart_review_json_to_pdf(model_name: str, output_dir: SyntaxWarning):
    pdf_dir = os.path.join(output_dir, model_name, "chart_review/pdf")
    os.makedirs(pdf_dir, exist_ok=True)
    json_dir = os.path.join(output_dir, model_name, "chart_review")
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