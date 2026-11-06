from flask import Flask, render_template, request, jsonify
import smtplib
from email.mime.text import MIMEText
import os
import pandas as pd
import fitz  # PyMuPDF

app = Flask(__name__)

# --- Demo File Processing Logic with Intent Support ---
@app.route('/api/process-demo', methods=['POST'])
def process_demo():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded."}), 400
    
    file = request.files['file']
    intent = request.form.get('intent', 'fleet_parsing')
    filename = file.filename
    ext = filename.split('.')[-1].lower()

    if ext == 'csv':
        df = pd.read_csv(file)
        total_rows = len(df)
        
        if intent == 'fleet_parsing':
            summary = {"total_records": total_rows, "parsed_mode": "Fleet Dispatch & Mileage Cleansing"}
        elif intent == 'lead_gen':
            summary = {"total_leads": total_rows, "parsed_mode": "SAM.gov Contract Lead Extraction"}
        else:
            summary = {"total_rows": total_rows, "parsed_mode": "General Custom Data Pipeline"}

        processed_df = df.head(10)
        return jsonify({
            'status': 'success',
            'intent_applied': intent,
            'summary': summary,
            'filename': filename,
            'sample_data': processed_df.to_dict(orient='records'),
            'message': f'Successfully parsed {total_rows} rows under {intent} protocol.'
        })

    elif ext == 'pdf':
        doc = fitz.open(stream=file.read(), filetype="pdf")
        total_pages = len(doc)
        extracted_text = doc[0].get_text() if total_pages > 0 else ""
        
        return jsonify({
            'status': 'success',
            'intent_applied': intent,
            'filename': filename,
            'total_pages': total_pages,
            'parsed_mode': f'PDF Document Parsing for {intent}',
            'extracted_snippet': extracted_text[:300] + "...",
            'message': f'Successfully extracted text from {total_pages} page(s).'
        })

    return jsonify({"status": "error", "message": "Unsupported file format. Please upload CSV or PDF."}), 400


# --- Contact Form Backend Endpoint ---
@app.route('/api/contact', methods=['POST'])
def handle_contact():
    data = request.get_json() or request.form

    sender_name = data.get('name', 'N/A')
    sender_email = data.get('email')
    message_text = data.get('message')

    if not sender_email or not message_text:
        return jsonify({"status": "error", "message": "Email and message are required."}), 400

    subject = f"New Inquiry from {sender_name} via Clearline Website"
    body = f"Name: {sender_name}\nEmail: {sender_email}\n\nMessage:\n{message_text}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = os.environ.get('MAIL_USERNAME', sender_email)
    msg['To'] = os.environ.get('CONTACT_RECIPIENT', 'k_oss51@yahoo.com')

    try:
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_pass = os.environ.get('SMTP_PASSWORD')

        if smtp_user and smtp_pass:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return jsonify({"status": "success", "message": "Inquiry sent successfully!"}), 200
        else:
            print(f"[CONTACT FORM INQUIRY]:\n{body}")
            return jsonify({"status": "success", "message": "Inquiry received!"}), 200

    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({"status": "error", "message": "Failed to send email."}), 500


# --- Home Route ---
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)