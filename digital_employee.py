import time
import random
import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
EMAIL_USER = "fil@clearlinedigitalsolutions.com"
EMAIL_PASS = "amdjvajrnwnrrnuk" # Application Password

# Throttling limits (protects sender domain reputation)
MAX_EMAILS_PER_BATCH = 5
MIN_DELAY_SECONDS = 300  # 5 minutes
MAX_DELAY_SECONDS = 480  # 8 minutes

def clean_header(header_val):
    if not header_val:
        return ""
    decoded = decode_header(header_val)
    parts = []
    for val, enc in decoded:
        if isinstance(val, bytes):
            parts.append(val.decode(enc or 'utf-8', errors='ignore'))
        else:
            parts.append(str(val))
    return "".join(parts)

def check_inbox_and_draft_replies():
    print("[*] Connecting to Inbox...")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("INBOX")

        # Search for unread messages
        status, messages = mail.search(None, 'UNSEEN')
        if status != "OK":
            print("[!] Could not search inbox.")
            return

        email_ids = messages[0].split()
        print(f"[*] Found {len(email_ids)} unread messages.")

        for e_id in email_ids:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for part in msg_data:
                if isinstance(part, tuple):
                    msg = email.message_from_bytes(part[1])
                    sender = clean_header(msg.get("From"))
                    subject = clean_header(msg.get("Subject"))
                    
                    print(f"\n[NEW MESSAGE] From: {sender} | Subject: {subject}")
                    
                    # Log message for review / mobile alert
                    with open("pending_approvals.txt", "a", encoding="utf-8") as f:
                        f.write(f"SENDER: {sender}\nSUBJECT: {subject}\nSTATUS: PENDING_REVIEW\n---\n")
                    
                    print("    -> Flagged and added to pending_approvals.txt")

        mail.logout()
    except Exception as e:
        print(f"[!] Error checking inbox: {e}")

def run_throttled_outreach_queue(outreach_list):
    """
    Sends outreach emails with randomized delays to prevent spam flags.
    """
    sent_count = 0
    for target in outreach_list[:MAX_EMAILS_PER_BATCH]:
        recipient = target["email"]
        subject = target["subject"]
        body = target["body"]

        print(f"[*] Dispatching outreach to {recipient}...")
        
        # Send Email via SMTP
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_USER
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP_SSL(SMTP_SERVER, 465)
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, recipient, msg.as_string())
            server.quit()

            sent_count += 1
            print(f"    [✔] Successfully sent to {recipient}")

            # Safe Throttle Delay
            delay = random.randint(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
            print(f"    [⏳] Throttling for {delay // 60} minutes to maintain domain health...")
            time.sleep(delay)

        except Exception as e:
            print(f"    [!] Failed to send to {recipient}: {e}")

    print(f"\n[✔] Batch complete. Sent {sent_count} emails safely.")

if __name__ == "__main__":
    print("=== DIGITAL EMPLOYEE AGENT RUNNER ===")
    check_inbox_and_draft_replies()