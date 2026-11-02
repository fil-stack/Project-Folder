import os
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- CONFIGURATION (Update with your Google Workspace details if needed) ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-business-email@yourdomain.com"  # Replace with your Google Workspace email
SENDER_PASSWORD = "your-app-password"                  # Replace with your Google Workspace App Password
# -------------------------------------------------------------------------

def dispatch_proposals():
    queue_file = "Autonomous_Execution_Queue.xlsx"
    proposal_folder = "Generated_Proposals"
    
    if not os.path.exists(queue_file):
        print(f"Error: {queue_file} not found. Run your engine first!")
        return
        
    df = pd.read_excel(queue_file)
    if df.empty:
        print("No opportunities found in the execution queue.")
        return
        
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Initializing automated proposal dispatch...")
    
    sent_count = 0
    
    for index, row in df.iterrows():
        title = row.get("title", "Opportunity")
        sol_id = row.get("solicitationNumber", str(index))
        
        # Look for the corresponding proposal file
        safe_id = "".join(c for c in str(sol_id) if c.isalnum() or c in ('_', '-'))
        filename = os.path.join(proposal_folder, f"Proposal_{safe_id}.txt")
        
        if not os.path.exists(filename):
            continue
            
        with open(filename, "r", encoding="utf-8") as f:
            proposal_body = f.read()
            
        # Note: If the SAM.gov export contains a contact email field, we pull it here. 
        # If not available in the public data feed, we log it for review or use a default target.
        recipient_email = row.get("pointOfContact.email", "contracting-office@sam.gov")
        
        if pd.isna(recipient_email) or not recipient_email:
            recipient_email = "target-lead@gov-portal.com" # Fallback placeholder if contact email is omitted in public feed

        # Construct Email
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = f"Formal Proposal / Capability Response: {title} ({sol_id})"
        msg.attach(MIMEText(proposal_body, "plain"))
        
        try:
            # Connect to SMTP server and send
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
            server.quit()
            
            print(f"SUCCESS: Dispatched proposal for [{title}] to {recipient_email}")
            sent_count += 1
        except Exception as e:
            print(f"ERROR sending proposal for {title}: {e}")

    print(f"\nDispatch complete. Successfully sent {sent_count} proposals autonomously.")

if __name__ == "__main__":
    dispatch_proposals()