from openai import OpenAI
import time
import os
import json
import pandas as pd
import glob, os
from pathlib import Path

def openAI_XPC_inference(client, model_name_str, system_prompt, user_prompt_inputs_dir, json_schema, output_dir, overwrite_outputs=False):
    stats_list = []

    output_subdir = os.path.join(output_dir, model_name_str, json_schema["name"])
    os.makedirs(output_subdir, exist_ok=True)
    stats_subdir = os.path.join(output_dir, model_name_str, "usage")
    os.makedirs(stats_subdir, exist_ok=True)

    for path in glob.glob(os.path.join(user_prompt_inputs_dir, "*.txt")):
        filename = os.path.basename(path)
        base_filename = filename.replace(".txt", "")
        output_filename = f"{base_filename}_{json_schema['name']}.json"
        output_filepath = os.path.join(output_subdir, output_filename)
        if not overwrite_outputs and os.path.exists(output_filepath):
            print(f"Generated text for {filename} already exists. Skipping...")
            continue
        with open(os.path.join(user_prompt_inputs_dir, filename), 'r') as file:
            user_prompt = file.read()
        if json_schema["name"] == "cr_feedback":
            print(f"JSON schema name: {json_schema['name']}")
            # Using the base filename, search for the generated chart review JSON file
            output_subdir_cr = output_subdir.replace("/cr_feedback", "")
            chart_review_filename = f"{base_filename}_chart_review.json"
            chart_review_filepath = os.path.join(output_subdir_cr, "chart_review", chart_review_filename)
            if os.path.exists(chart_review_filepath):
                with open(chart_review_filepath, 'r') as file:
                    chart_review_json = json.load(file)
                # Add the chart review JSON to the user prompt
                user_prompt = f"{user_prompt}\n# Chart Review for Feedback\n{json.dumps(chart_review_json)}"
                print(f"Using chart review JSON for {filename} from {chart_review_filename}")
        timer_start = time.time()
        print(f"Generating text via OpenAI for {filename} using the {model_name_str} model with {json_schema['name']} JSON structured output...")
        response = client.responses.create(
            model=model_name_str,
            input=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            text={
                "format": json_schema
            },
            #temperature=0.1,
            max_output_tokens= 16384
            )
        timer_stop = time.time()
        timer_duration = timer_stop - timer_start
        timer_duration_seconds = "{:.3f}".format(timer_duration)
        print(f"Text generation complete for {filename} in {timer_duration_seconds} seconds.")
        try:
            response_json = json.loads(response.output_text)
        except Exception as e:
            print(f"Error parsing JSON from response for {filename}: {e}")
            continue

        plan = response_json.setdefault("Plan", {})
        if not isinstance(plan, dict):
            raise ValueError("Expected 'Plan' to be an object/dict in your JSON")

        for section in ("Anticipatory Preventative Care", "Follow Up Care"):
            # If section lives at the top level, move it under Plan
            if section in response_json:
                print(f"Conforming generated JSON to intended schema. Moving {section} to Plan")
                plan[section] = response_json.pop(section)

        with open(output_filepath, 'w') as file:
            # Convert dictionary back to JSON string with formatting
            file.write(json.dumps(response_json, indent=2))
        
        # Build stats using the assumed structure of response_json usage data
        try:
            usage_data = response.usage
            print(f"Usage stats: (input_tokens: {usage_data.input_tokens}, output_tokens: {usage_data.output_tokens}, total_tokens: {usage_data.total_tokens})\n")
            stats = {
                "input_filename": filename,
                "output_filename": output_filename,
                "model_name": model_name_str,
                "json_schema": json_schema["name"],
                "input_tokens": usage_data.input_tokens,
                "cached_input_tokens": usage_data.input_tokens_details.cached_tokens,
                "output_tokens": usage_data.output_tokens,
                "total_tokens": usage_data.total_tokens,
                "time_to_generate": timer_duration_seconds
            }
        except Exception as e:
            print(f"Error extracting usage data for {filename}: {e}")
            stats = {}
        
        stats_list.append(stats)
    
    # Save the stats to a CSV file using pandas
    stats_df = pd.DataFrame(stats_list)
    file_name_date_time = time.strftime("%Y%m%d-%H%M%S")
    stats_filename = f"inference_stats_{json_schema['name']}_{file_name_date_time}.csv"
    stats_filepath = os.path.join(stats_subdir, stats_filename)
    stats_df.to_csv(stats_filepath, index=False)