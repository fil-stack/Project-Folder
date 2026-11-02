import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime

# --- CONFIGURATION ---
IMAP_SERVER = "imap.gmail.com"
EMAIL_USER = "fil@clearlinedigitalsolutions.com"
EMAIL_PASSWORD = "ptbsijmqdgyibdbt"  # Your secure app password
PROCESSED_LOG = "inbox_history.txt"
# ---------------------

def load_processed_history():
    """Loads a set of already processed email subjects to avoid duplicate reviews."""
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, "r", encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip())
    return set()

def record_processed_email(subject_str):
    """Logs processed email subjects."""
    with open(PROCESSED_LOG, "a", encoding="utf-8") as f:
        f.write(str(subject_str).strip() + "\n")

def scan_inbox_notifications():
    print("\n--- Scanning Gmail Inbox for State & Local Procurement Alerts ---")
    processed_history = load_processed_history()
    
    try:
        # Connect to Gmail IMAP securely on port 993
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
        mail.login(EMAIL_USER, EMAIL_PASSWORD)
        mail.select("INBOX")
        
        # Search for unread emails
        status, messages = mail.search(None, '(UNSEEN)')
        if status != 'OK':
            print("No new unread messages found.")
            mail.logout()
            return 0
            
        email_ids = messages[0].split()
        if not email_ids:
            print("Inbox is clean: No new unread messages.")
            mail.logout()
            return 0
            
        matches_found = []
        
        for e_id in email_ids:
            res, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode subject header safely
                    subject_header = decode_header(msg["Subject"])[0]
                    subject = subject_header[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(subject_header[1] or 'utf-8', errors='ignore')
                    else:
                        subject = str(subject)
                        
                    sender = msg.get("From", "")
                    
                    # Check if already processed
                    if subject.strip().lower() in processed_history:
                        continue
                        
                    # Extract email body text
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                except:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            pass
                            
                    text_blob = f"{subject} {body}".lower()
                    
                    # Filter for state procurement keywords or known portals
                    procurement_sources = ["fiscal.ca.gov", "cal eprocure", "bid", "solicitation", "rfp", "ifb", "procurement"]
                    is_procurement = any(src in text_blob for src in procurement_sources)
                    
                    if not is_procurement:
                        continue
                        
                    # Check against software/data/mailing wheelhouse triggers
                    software_triggers = ["software", "data", "system", "it", "development", "portal", "automated", "report", "database", "mailing", "printing"]
                    matches = sum(1 for trig in software_triggers if trig in text_blob)
                    
                    if matches >= 2:
                        match_info = {
                            "subject": subject,
                            "sender": sender,
                            "snippet": body[:300].replace('\n', ' '),
                            "matches_count": matches
                        }
                        matches_found.append(match_info)
                        record_processed_email(subject)
                        
        mail.logout()
        
        if not matches_found:
            print("Scan complete: No new software/data procurement alerts found in unread mail.")
            return 0
            
        print(f"\nFound {len(matches_found)} matching state/local opportunity alerts!")
        for idx, match in enumerate(matches_found, 1):
            print(f"\n[{idx}] SUBJECT: {match['subject']}")
            print(f"    SENDER: {match['sender']}")
            print(f"    SNIPPET: {match['snippet']}...")
            
        return len(matches_found)
        
    except Exception as e:
        print(f"Error scanning inbox: {e}")
        return 0

if __name__ == "__main__":
    print("=== STARTING INBOX PROCUREMENT SCANNER ===")
    scan_inbox_notifications()
    print("=== INBOX SCANNER FINISHED ===")