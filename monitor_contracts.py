import csv
import json
import urllib.request
from datetime import datetime

# Configuration
API_KEY = 'SAM-b6c2c24e-f505-4efa-9f3b-7d8992c127de'
  # Replace with your actual key
TARGET_NAICS = '541511'
OUTPUT_FILE = 'filtered_tech_contracts.csv'
LOG_FILE = 'execution_log.txt'

def run_contract_monitor():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] Fetching live contracts from SAM.gov API...")
    
    url = f"https://api.sam.gov/prod/opportunities/v2/search?api_key={API_KEY}&ncode={TARGET_NAICS}&postedFrom=01/01/2026&postedTo=08/29/2026&limit=100"
    
    matched_rows = []
    
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            opportunities = data.get('opportunities', [])

            for opp in opportunities:
                # Filter locally to ensure it matches your target NAICS
                if str(opp.get('naicsCode', '')) == TARGET_NAICS:
                    row = {
                        'Contracting Office': opp.get('fullParentPathName', ''),
                        'Notice ID': opp.get('noticeId', ''),
                        'Contract Opportunity Type': opp.get('type', ''),
                        'Opportunity Title': opp.get('title', ''),
                        'NAICS': opp.get('naicsCode', ''),
                        'Current Response Date': opp.get('responseDeadLine', ''),
                        'Status': opp.get('status', '')
                    }
                    matched_rows.append(row)

        if matched_rows:
            fieldnames = list(matched_rows[0].keys())
            with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(matched_rows)
            result_msg = f"SUCCESS: Fetched and saved {len(matched_rows)} live contracts to {OUTPUT_FILE}."
        else:
            result_msg = "INFO: No matching contracts returned from the API during this run."

        print(result_msg)

        with open(LOG_FILE, mode='a', encoding='utf-8') as logfile:
            logfile.write(f"[{timestamp}] {result_msg}\n")

    except Exception as e:
        error_msg = f"ERROR: An exception occurred during API execution: {e}"
        print(error_msg)
        with open(LOG_FILE, mode='a', encoding='utf-8') as logfile:
            logfile.write(f"[{timestamp}] {error_msg}\n")



if __name__ == '__main__':
    run_contract_monitor()