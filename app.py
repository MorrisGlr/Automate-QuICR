import pandas as pd
import os
import json
from openai import OpenAI
from google import genai
from dotenv import load_dotenv
import spacy
import scispacy
from spacy.tokens import Span
from scispacy.abbreviation import AbbreviationDetector
from scispacy.umls_linking import UmlsEntityLinker
from src.openAI_XPC_inference import openAI_XPC_inference
from src.gemini_XPC_inference import gemini_XPC_inference
from src.chart_review_json_to_pdf import chart_review_json_to_pdf
from src.cr_feedback_json_to_pdf import cr_feedback_json_to_pdf
from src.drug_pricing import extract_medications
from src.drug_pricing import load_medication_pipeline
from src.aggregate_feedback_pdf import aggregate_feedback

# set working directory
wk_dir = "/Users/morris/github_projects/XPC_chart_review"
os.chdir(wk_dir)

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
umls_api_key = os.getenv("UMLS_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Defining paths
user_prompt_inputs_dir = "data"
output_dir = os.path.join(wk_dir, "generated_output")

# Prompts (Chart Review and Feedback)
with open("prompt/system/system_prompt_chart_review_2.txt", "r", encoding='utf-8') as f:
    system_prompt_cr = f.read()

with open("prompt/system/system_prompt_feedback_1_sans_json.txt", "r", encoding='utf-8') as f:
    system_prompt_fb = f.read()

# JSON Schemas (Chart Review and Feedback)
json_schema_cr = json.load(open("prompt/json_schema/chart_review.json", "r", encoding='utf-8'))
json_schema_fb = json.load(open("prompt/json_schema/cr_feedback.json", "r", encoding='utf-8'))

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)
model_name_str = "o4-mini-2025-04-16"

# Initialize the Gemini client
#client = genai.Client(api_key=gemini_api_key)
gemini_model_str = "gemini-2.5-pro-exp-03-25"

# Run OpenAI_XPC_inference for Chart Review
#openAI_XPC_inference(client, model_name_str, system_prompt_cr, user_prompt_inputs_dir, json_schema_cr, output_dir, overwrite_outputs=True)

# Run OpenAI_XPC_inference for Feedback
#openAI_XPC_inference(client, model_name_str, system_prompt_fb, user_prompt_inputs_dir, json_schema_fb, output_dir, overwrite_outputs=True)

# Run Gemini_XPC_inference for Chart Review
#gemini_XPC_inference(client, gemini_model_str, system_prompt_cr, user_prompt_inputs_dir, json_schema_cr, output_dir, overwrite_outputs=True)

# Run drug pricing
# Load the medication pipeline
'''
pricing_df1 = pd.read_csv("drug_pricing/walmart_drug_pricing.csv", usecols=["source","generic_drug_name","30_day_cost"])
pricing_df2 = pd.read_csv("drug_pricing/costplus_drug_pricing_cleaned.csv", usecols=["source","generic_drug_name","30_day_cost"])
extract_medications(model_name_str, output_dir, pricing_dfs=[pricing_df1, pricing_df2], model="en_core_sci_md", umls_api_key=umls_api_key)
'''

# Convert the chart review JSON files to a formatted PDF.
#chart_review_json_to_pdf(model_name_str, output_dir)
#chart_review_json_to_pdf(gemini_model_str, output_dir)

# Convert the feedback JSON files to a formatted PDF.
# cr_feedback_json_to_pdf(model_name_str, output_dir)

# Convert the aggregated feedback JSON files to a formatted PDF.
aggregate_feedback(model_name_str, output_dir)