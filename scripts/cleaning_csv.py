import pandas as pd
import re

# Load CSV (try utf-8-sig, fall back to ISO-8859-1)
try:
    df = pd.read_csv('costplus_drug_pricing.csv', encoding='utf-8-sig')
except UnicodeDecodeError:
    df = pd.read_csv('costplus_drug_pricing.csv', encoding='ISO-8859-1')

# Remove "(Generic for …)" labels
gen_pattern = re.compile(r'\s*\(Generic for [^)]+\)')
df = df.applymap(lambda x: gen_pattern.sub('', x) if isinstance(x, str) else x)

# Define cleaning function
def deep_clean(text):
    if not isinstance(text, str):
        return text

    # 1) Try to undo Latin1→UTF8 mis-decoding
    try:
        text = text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

    # 2) Explicitly strip common junk
    for bad, good in {
        '\xa0': ' ',   # non-breaking space
        '¬†': ' ',
    }.items():
        text = text.replace(bad, good)

    # 3) Collapse *any* run of non-ASCII between word chars into a hyphen
    text = re.sub(r'(?<=\w)[^\x00-\x7F]+(?=\w)', '-', text)

    # 4) Collapse multiple hyphens into one, trim edges
    text = re.sub(r'-{2,}', '-', text).strip('-')

    return text

# Apply to every string cell
df_cleaned = df.applymap(deep_clean)

# Save out
df_cleaned.to_csv('costplus_drug_pricing_cleaned.csv', index=False)