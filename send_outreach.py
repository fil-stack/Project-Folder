import csv
import dns.resolver

def is_valid_email_domain(email: str) -> bool:
    """
    Validates whether the domain of an email address has active MX records.
    Returns True if the domain can receive mail, False otherwise.
    """
    try:
        domain = email.split('@')[1]
        # Query MX records for the domain
        records = dns.resolver.resolve(domain, 'MX')
        return len(records) > 0
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, Exception):
        # Fallback check: try querying A records if MX fails
        try:
            a_records = dns.resolver.resolve(domain, 'A')
            return len(a_records) > 0
        except Exception:
            return False

def clean_and_load_leads(csv_filename):
    valid_leads = []
    print(f"Checking domains in {csv_filename}...")
    
    with open(csv_filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('email')
            if email and is_valid_email_domain(email):
                valid_leads.append(row)
            else:
                print(f"Skipping dead or invalid domain: {email}")
                
    print(f"Found {len(valid_leads)} valid leads ready for outreach.")
    return valid_leads

if __name__ == "__main__":
    # Replace 'leads.csv' with your actual lead file name if different
    leads = clean_and_load_leads('leads.csv')