import os
import requests
import datetime

# SAM.gov API configuration
# If you have an official API key from sam.gov, paste it inside the quotes below:
SAM_API_KEY = "YOUR_SAM_GOV_API_KEY_HERE"
HISTORY_FILE = "sent_history.txt"
REPORT_FOLDER = "Generated_Proposals"

def load_sent_history():
    """Load sent/processed solicitation IDs to prevent duplicate proposals."""
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return {line.strip().upper() for line in f if line.strip()}

def fetch_live_sam_opportunities():
    """Fetch active live contract opportunities directly from SAM.gov."""
    sent_history = load_sent_history()
    
    # Standard broader procurement keywords that match your data pipeline agent capabilities
    keywords = ["Data Ingestion", "Digital Applications", "Data Processing", "Automation"]
    
    # Live SAM.gov Public Search Endpoint
    url = "https://api.sam.gov/opportunities/v2/search"
    
    today = datetime.date.today().strftime("%m/%d/%Y")
    
    found_leads = []
    
    for kw in keywords:
        params = {
            "api_key": SAM_API_KEY,
            "q": kw,
            "status": "active",
            "limit": 10
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                for item in data.get("opportunitiesData", []):
                    sol_id = (item.get("solicitationNumber") or item.get("noticeId") or "").upper()
                    if sol_id and sol_id not in sent_history:
                        found_leads.append({
                            "solicitation_id": sol_id,
                            "title": item.get("title"),
                            "agency": item.get("department", {}).get("name", "Dept of Defense"),
                            "poc": item.get("pointOfContact", [{}])[0].get("email", "See SAM.gov listing")
                        })
        except Exception as e:
            print(f"[!] Search query error for '{kw}': {e}")
            
    return found_leads

def run_daily_sam_lead_search():
    print(f"[{datetime.date.today()}] Starting automated SAM.gov defense contract search...")
    leads = fetch_live_sam_opportunities()
    
    os.makedirs(REPORT_FOLDER, exist_ok=True)
    report_filename = os.path.join(REPORT_FOLDER, f"Daily_Lead_Report_{datetime.date.today()}.txt")
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(f"==================================================\n")
        f.write(f"DAILY CONTRACT OPPORTUNITY REPORT - {datetime.date.today()}\n")
        f.write(f"==================================================\n\n")
        
        if leads:
            f.write(f"TOTAL ACTIVE UNPROCESSED LEADS FOUND: {len(leads)}\n\n")
            for idx, lead in enumerate(leads, 1):
                f.write(f"LEAD #{idx}:\n")
                f.write(f" - Solicitation ID: {lead['solicitation_id']}\n")
                f.write(f" - Agency: {lead['agency']}\n")
                f.write(f" - Title: {lead['title']}\n")
                f.write(f" - POC: {lead['poc']}\n\n")
        else:
            f.write("No new unprocessed leads found matching criteria.\n")
            
    print(f"[✓] Daily lead processed successfully. Report saved to {report_filename}")

def auto_shutdown_system():
    print("[⚡] Task complete. Shutting down system in 60 seconds...")
    os.system("shutdown /s /f /t 60")

if __name__ == "__main__":
    run_daily_sam_lead_search()
    auto_shutdown_system()