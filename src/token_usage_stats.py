import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV file (adjust the path if needed)
df = pd.read_csv('/Users/morris/github_projects/XPC_chart_review/generated_output/gpt-4o-2024-11-20/usage/inference_stats_chart_review_20250328-163857.csv')

# If you're unsure about the column names, you might print them:
print("Columns in CSV:", df.columns.tolist())

# Assuming your CSV has columns 'filename' for file names and 'token_count' for token usage,
# you can create a bar plot as follows:
plt.figure(figsize=(10, 6))
plt.bar(df['input_filename'], df['total_tokens'], edgecolor='black')

plt.xlabel('File Name')
plt.ylabel('Token Count')
plt.title('LLM Token Usage per File')
plt.xticks(rotation=45)  # Rotate x labels for better readability
plt.tight_layout()       # Adjust layout to prevent clipping of labels
plt.show()
