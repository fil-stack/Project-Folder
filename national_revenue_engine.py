import os
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# --- CONFIGURATION & SECURITY ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "fil@clearlinedigitalsolutions.com"
SENDER_PASSWORD = "ptbsijmqdgyibdbt"  # Secure App Password

SAM_API_KEY = "SAM-b6c2c24e-f505-4efa-9f3b-7d8992c127de" 
SENT_HISTORY_FILE = "sent_history.txt"
LOG_FILE = "engine_activity.log"

MAX_RUN_TIME_SECONDS = 7200  
CHECK_INTERVAL_SECONDS = 300  
# --------------------------------

def log_activity(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def load_sent_history():
    if os.path.exists(SENT_HISTORY_FILE):
        with open(SENT_HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip())
    return set()

def record_sent(title):
    with open(SENT_HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(str(title).strip() + "\n")

def fetch_and_filter_opportunities():
    leads = []
    
    try:
        url = "https://api.sam.gov/opportunities/v2/search"
        today = datetime.now()
        posted_from = (today - timedelta(days=30)).strftime("%m/%d/%Y")
        posted_to = today.strftime("%m/%d/%Y")
        
        params = {
            "api_key": SAM_API_KEY,
            "limit": 50,
            "postedFrom": posted_from,
            "postedTo": posted_to,
            "ptype": "o",  
            "q": "python software data automation"
        }
        
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get("opportunitiesData", [])
            
            for opp in opportunities:
                title = opp.get("title", "")
                sol_id = opp.get("solicitationNumber", "N/A")
                agency = opp.get("fullParentPathName", "Federal Agency")
                desc = opp.get("description", "")
                link = opp.get("uiLink", "https://sam.gov")
                deadline = opp.get("responseDeadLine", "")
                
                combined_text = f"{title} {agency} {desc}".lower()
                
                # --- EXPANDED STRICT EXCLUSION BLACKLIST ---
                exclusion_keywords = [
                    "construction", "janitorial", "roofing", "painting", "plumbing", 
                    "hardware installation", "on-site support", "civil engineering", 
                    "medical equipment", "vehicle", "security guard", "awarded",
                    "repair", "engine", "gas", "chiller", "assy", "aircraft", 
                    "parts", "supplies", "valve", "pump", "filter", "cable",
                    "metal", "steel", "truck", "generator", "ball & seat",
                    "seat", "observer", "rehabilitation", "water", "wastewater", 
                    "roof", "replacement", "renovation", "program officer", 
                    "personal services", "submarine", "vessel", "charter",
                    "hospital", "health care system", "army corps of engineers",
                    "spacer", "compressor"
                ]
                if any(ex in combined_text for ex in exclusion_keywords):
                    continue  
                
                # --- INCLUSION FILTER ---
                inclusion_keywords = ["python", "software", "data", "automation", "pipeline", "api", "database", "script", "developer", "analytics"]
                if not any(inc in combined_text for inc in inclusion_keywords):
                    continue
                
                poc_email = "procurement@sam.gov"
                contacts = opp.get("pointOfContact", [])
                if contacts and isinstance(contacts, list):
                    for contact in contacts:
                        if contact.get("email"):
                            poc_email = contact.get("email")
                            break

                leads.append({
                    "title": f"[SAM.gov] {title} ({sol_id})",
                    "agency_or_company": agency,
                    "contact_email": poc_email,
                    "description": desc[:350] + "...",
                    "value": f"Active Solicitation (Deadline: {deadline[:10] if deadline else 'Open'}) | Link: {link}"
                })
        else:
            log_activity(f"SAM.gov API status code: {response.status_code}.")
    except Exception as e:
        log_activity(f"SAM.gov Connection Error: {e}")

    return leads

def send_proposal(target_email, title, proposal_body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = target_email
        msg['Subject'] = f"Proposal / Capability Statement: {title}"

        msg.attach(MIMEText(proposal_body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, target_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        log_activity(f"SMTP Dispatch Error: {e}")
        return False

def run_national_engine():
    log_activity("=== STARTING REFINED SAM.GOV ENGINE ===")
    sent_history = load_sent_history()
    
    start_time = time.time()
    run_count = 0

    while (time.time() - start_time) < MAX_RUN_TIME_SECONDS:
        run_count += 1
        elapsed_mins = int((time.time() - start_time) / 60)
        log_activity(f"--- Execution Loop #{run_count} (Elapsed: {elapsed_mins} mins) ---")
        
        leads = fetch_and_filter_opportunities()
        new_leads = [l for l in leads if l['title'].lower() not in sent_history]

        if not new_leads:
            log_activity("No matching technical contracts found in this batch. Waiting for next cycle...")
        else:
            log_activity(f"Discovered {len(new_leads)} verified software & automation opportunities!")
            
            for lead in new_leads:
                print("\n" + "="*70)
                print(f"🎯 VERIFIED TARGET: {lead['title']}")
                print(f"🏢 AGENCY: {lead['agency_or_company']}")
                print(f"💰 STATUS: {lead['value']}")
                print(f"📧 CONTACT: {lead['contact_email']}")
                print(f"📄 SCOPE: {lead['description']}")
                print("="*70)

                approval = input("\n[PERMISSION REQUIRED] Authorize proposal dispatch & local execution? (y = Yes / n = Skip / q = Quit Engine): ").strip().lower()
                
                if approval == 'q':
                    log_activity("User terminated engine execution manually.")
                    return
                elif approval == 'y':
                    log_activity(f"User APPROVED execution for: {lead['title']}")
                    
                    proposal_text = f"""Hello Team at {lead['agency_or_company']},

I am writing regarding your listing for [{lead['title']}]. 

With extensive experience in building robust Python automation scripts, custom data pipelines, and secure dispatch architectures, ClearLine Digital Solutions can deploy a streamlined, high-performance solution tailored precisely to your specifications.

We ensure rapid turnaround, clean data structuring, and bulletproof reliability without administrative bloat. 

I would love to connect to discuss how we can execute this project immediately.

Best regards,
Filiberto Prado
ClearLine Digital Solutions
"""
                    success = send_proposal(lead['contact_email'], lead['title'], proposal_text)
                    if success:
                        log_activity(f"SUCCESS: Dispatched proposal for '{lead['title']}' to {lead['contact_email']}")
                        sent_history.add(lead['title'].lower())
                        record_sent(lead['title'])
                    else:
                        log_activity(f"FAILED to dispatch proposal for '{lead['title']}'")
                else:
                    log_activity(f"User SKIPPED opportunity: {lead['title']}")

        log_activity(f"Sleeping for {CHECK_INTERVAL_SECONDS // 60} minutes before next scan...")
        time.sleep(CHECK_INTERVAL_SECONDS)
        break  

    log_activity("=== REVENUE ENGINE COMPLETED RUN CYCLE ===")

if __name__ == "__main__":
    run_national_engine()