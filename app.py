from flask import Flask, render_template, request, jsonify
import smtplib
from email.mime.text import MIMEText
import os
import pandas as pd
import fitz  # PyMuPDF

app = Flask(__name__)

# --- Existing Demo File Processing Logic ---
@app.route('/api/process-demo', methods=['POST'])
def process_demo():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded."}), 400
    
    file = request.files['file']
    intent = request.form.get('intent', 'fleet_parsing') # Captures the selected tile intent!
    filename = file.filename
    ext = filename.split('.')[-1].lower()

    if ext == 'csv':
        df = pd.read_csv(file)
        total_rows = len(df)
        processed_df = df.head(50)
        return jsonify({
            'status': 'success',
            'intent_received': intent,
            'filename': filename,
            'total_rows': total_rows,
            'rows_processed': len(processed_df),
            'sample_data': processed_df.to_dict(orient='records'),
            'message': f'Free Trial Limit Applied: Processed {len(processed_df)} of {total_rows} rows.' if total_rows > 50 else "Full file processed!"
        })

    elif ext == 'pdf':
        doc = fitz.open(stream=file.read(), filetype="pdf")
        total_pages = len(doc)
        extracted_text = ""
        for i in range(min(2, total_pages)):
            extracted_text += f"--- PAGE {i+1} ---\n" + doc[i].get_text()
        
        return jsonify({
            'status': 'success',
            'intent_received': intent,
            'filename': filename,
            'total_pages_detected': total_pages,
            'pages_processed': min(2, total_pages),
            'sample_text': extracted_text,
            'message': f'Free Trial Limit Applied: Extracted {min(2, total_pages)} of {total_pages} pages.' if total_pages > 2 else "Full document extracted!"
        })

    return jsonify({"status": "error", "message": "Unsupported file format. Please upload CSV or PDF."}), 400


# --- New Contact Form Backend Endpoint ---
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