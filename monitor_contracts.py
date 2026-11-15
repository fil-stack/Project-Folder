import csv
import json
import urllib.request
from datetime import datetime, timedelta

# Configuration
API_KEY = 'SAM-1514b520-7deb-432a-8580-6c7943ec4ecd'
TARGET_NAICS = '541511'
OUTPUT_FILE = 'refined_tech_contracts.csv'  # Matches app.py REFINED_CSV
LOG_FILE = 'execution_log.txt'

# Words that indicate giant/classified defense contracts to skip
EXCLUDE_KEYWORDS = [
    'top secret', 'ts/sci', 'secret clearance', 'siprnet', 
    'classified facility', 'scif', 'weapon system', 'radar'
]

def is_future_deadline(deadline_str):
    """Returns True if the deadline is in the future (or if none is listed yet)."""
    if not deadline_str:
        return True
    try:
        # SAM.gov typically returns ISO format e.g. '2026-11-25T14:00:00-05:00' or '2026-11-25'
        clean_date = deadline_str.split('T')[0]
        due_date = datetime.strptime(clean_date, '%Y-%m-%d')
        return due_date.date() >= datetime.now().date()
    except ValueError:
        return True

def run_contract_monitor():
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # Dynamically query the last 14 days
    posted_from = (now - timedelta(days=14)).strftime('%m/%d/%Y')
    posted_to = now.strftime('%m/%d/%Y')
    
    print(f"[{timestamp}] Fetching Small Business & Sources Sought leads ({posted_from} to {posted_to})...")
    
    # Query SAM.gov v2 API (ptype=r,o,k targets Sources Sought & Solicitations)
    url = (
        f"https://api.sam.gov/prod/opportunities/v2/search?"
        f"api_key={API_KEY}&ncode={TARGET_NAICS}"
        f"&postedFrom={posted_from}&postedTo={posted_to}"
        f"&ptype=r,o,k&limit=250"
    )
    
    matched_rows = []
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            # SAM.gov v2 uses 'opportunitiesData'
            opportunities = data.get('opportunitiesData', [])

            for opp in opportunities:
                naics = str(opp.get('naicsCode', ''))
                title = opp.get('title', '')
                opp_type = opp.get('type', '')
                set_aside = str(opp.get('typeOfSetAside', '') or opp.get('setAsideCode', '')).upper()
                deadline = opp.get('responseDeadLine', '') or opp.get('reponseDeadLine', '')
                active = str(opp.get('active', '')).lower()

                # 1. Must match NAICS 541511 and be active
                if naics != TARGET_NAICS or active == 'no':
                    continue

                # 2. Must have a future (open) response deadline
                if not is_future_deadline(deadline):
                    continue

                # 3. Realistic Small Business Filter:
                # Keep if it is a Small Business Set-Aside (SBA) OR a Sources Sought (early market research)
                is_small_biz = 'SBA' in set_aside or 'SMALL BUSINESS' in str(opp.get('setAside', '')).upper()
                is_sources_sought = 'sources sought' in opp_type.lower()
                if not (is_small_biz or is_sources_sought):
                    continue

                # 4. Skip classified/clearance-heavy opportunities
                if any(bad_word in title.lower() for bad_word in EXCLUDE_KEYWORDS):
                    continue

                row = {
                    'Contracting Office': opp.get('fullParentPathName', 'Federal Agency'),
                    'Notice ID': opp.get('noticeId', ''),
                    'Contract Opportunity Type': f"{opp_type} ({set_aside or 'Open Market Research'})",
                    'Opportunity Title': title,
                    'NAICS': naics,
                    'Current Response Date': deadline.split('T')[0] if deadline else 'TBD',
                    'Status': 'Active',
                    'SAM Link': f"https://sam.gov/opp/{opp.get('noticeId', '')}/view"
                }
                matched_rows.append(row)

        if matched_rows:
            fieldnames = list(matched_rows[0].keys())
            with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(matched_rows)
            result_msg = f"SUCCESS: Saved {len(matched_rows)} realistic Small Business leads to {OUTPUT_FILE}."
        else:
            result_msg = "INFO: No new Small Business / Sources Sought leads matched the strict filters today."

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