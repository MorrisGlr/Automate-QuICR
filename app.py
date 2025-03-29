import pandas as pd
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from src.openAI_XPC_inference import openAI_XPC_inference

# set working directory
wk_dir = "/Users/morris/github_projects/XPC_chart_review"
os.chdir(wk_dir)

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
umls_api_key = os.getenv("UMLS_API_KEY")

# Defining paths
user_prompt_inputs_dir = "data"
output_dir = os.path.join(wk_dir, "generated_output")

# Prompts (Chart Review and Feedback)
with open("prompt/system/system_prompt_chart_review_1_sans_json.txt", "r", encoding='utf-8') as f:
    system_prompt_cr = f.read()

with open("prompt/system/system_prompt_feedback_1_sans_json.txt", "r", encoding='utf-8') as f:
    system_prompt_fb = f.read()

# JSON Schemas (Chart Review and Feedback)
json_schema_cr = json.load(open("prompt/json_schema/chart_review.json", "r", encoding='utf-8'))
json_schema_fb = json.load(open("prompt/json_schema/cr_feedback.json", "r", encoding='utf-8'))

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)
model_name_str = "gpt-4o-2024-11-20"

# Run OpenAI_XPC_inference for Chart Review
openAI_XPC_inference(client, model_name_str, system_prompt_cr, user_prompt_inputs_dir, json_schema_cr, output_dir, overwrite_outputs=True)

# Run OpenAI_XPC_inference for Feedback
openAI_XPC_inference(client, model_name_str, system_prompt_fb, user_prompt_inputs_dir, json_schema_fb, output_dir, overwrite_outputs=True)