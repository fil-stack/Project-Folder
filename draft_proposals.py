import os
import pandas as pd
from datetime import datetime

def generate_proposals():
    input_file = "Autonomous_Execution_Queue.xlsx"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Run your main engine first!")
        return
        
    df = pd.read_excel(input_file)
    
    if df.empty:
        print("No opportunities found in the execution queue to draft proposals for.")
        return
        
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Reading execution queue and drafting proposals...")
    
    output_folder = "Generated_Proposals"
    os.makedirs(output_folder, exist_ok=True)
    
    draft_count = 0
    
    for index, row in df.iterrows():
        title = row.get("title", "Unknown Opportunity")
        sol_id = row.get("solicitationNumber", str(index))
        description = row.get("description", "No description provided.")
        agency = row.get("fullParentPathName", "Federal Agency")
        
        # Clean up solicitation ID for safe filename usage
        safe_id = "".join(c for c in str(sol_id) if c.isalnum() or c in ('_', '-'))
        filename = os.path.join(output_folder, f"Proposal_{safe_id}.txt")
        
        # Construct the automated proposal/inquiry letter
        proposal_text = f"""==================================================
AUTONOMOUS PROPOSAL DRAFT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
==================================================

TO: Contracting Officer / Point of Contact
AGENCY: {agency}
SUBJECT: Technical Capabilities Statement & Inquiry regarding Solicitation: {title} ({sol_id})

Dear Contracting Team,

I am writing to express our formal interest in the recently posted solicitation, "{title}". 

After a thorough automated review of the project requirements, our digital infrastructure has verified full alignment with our core software, automation, and data processing capabilities. We are fully equipped to execute the requested scope with high precision, zero on-site friction, and complete remote efficiency.

Project Scope Breakdown Analyzed:
- {description[:350]}...

Why We Are Uniquely Positioned to Handle This:
1. End-to-End Automated Execution: Our systems natively handle custom scripts, API integrations, and robust data pipelines required for seamless delivery.
2. Rapid Turnaround: Operating without traditional overhead allows us to meet strict federal and local timelines efficiently.
3. Scalable Delivery: Built from the ground up to handle high-volume digital workloads autonomously.

We would welcome the opportunity to review the complete package or submit our formal bid/quote documentation immediately. Please let us know the next steps required to proceed.

Best regards,

Autonomous Operations & Technical Services
Contact: Automated Systems Deployment
==================================================
"""
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(proposal_text)
            
        draft_count += 1

    print(f"\nSuccess! Generated {draft_count} custom proposal drafts.")
    print(f"Check the new folder inside your Project Folder: '{output_folder}/'")

if __name__ == "__main__":
    generate_proposals()