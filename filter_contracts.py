from datetime import datetime
import csv
import pandas as pd

input_file = "filtered_tech_contracts.csv"
output_file = "refined_tech_contracts.csv"

# Keywords tailored to Clearline Digital Solutions' IT & software focus
keywords = [
    "software",
    "python",
    "data",
    "developer",
    "it",
    "information technology",
    "application",
    "system",
    "api",
    "cyber",
    "cloud",
    "database",
]

# Today's date reference for active check
current_date = datetime.now()

filtered_rows = []
header = []

with open(input_file, mode="r", encoding="utf-8", errors="ignore") as infile:
  reader = csv.reader(infile)
  header = next(reader)
  filtered_rows.append(header)

  # Find the index of the Current Response Date column
  try:
    date_idx = header.index("Current Response Date")
  except ValueError:
    date_idx = 8  # fallback index

  for row in reader:
    row_text = " ".join(row).lower()

    # Check keyword match
    has_keyword = any(kw in row_text for kw in keywords)

    if has_keyword:
      # Check response date if available
      date_str = row[date_idx] if len(row) > date_idx else ""
      try:
        cleaned_date = (
            date_str.replace(" UTC", "")
            .replace("EST", "")
            .replace("EDT", "")
            .strip()
        )
        response_date = pd.to_datetime(cleaned_date, errors="coerce")

        # Keep only if response date is in the future (or missing/TBD)
        if pd.isna(response_date) or response_date >= current_date:
          filtered_rows.append(row)
      except:
        # If date parsing fails, keep it to be safe
        filtered_rows.append(row)

# Save the truly active, refined results
with open(output_file, mode="w", encoding="utf-8", newline="") as outfile:
  writer = csv.writer(outfile)
  writer.writerows(filtered_rows)

print(
    f"Filtering complete! Found {len(filtered_rows) - 1} active, relevant"
    f" contracts and saved them to {output_file}."
)