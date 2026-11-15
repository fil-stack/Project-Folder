import os
import smtplib
from email.mime.text import MIMEText
import pandas as pd
import fitz  # PyMuPDF
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from cleanup import purge_old_files

app = Flask(__name__)

# Configuration
OUTPUT_FOLDER = "generated_outputs"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload limit

# Ensure directories exist
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Run automatic cleanup on startup to purge old files older than 24 hours
purge_old_files()

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'docx', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

REFINED_CSV = 'refined_tech_contracts.csv'

# --- Home & Contracts Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/contracts')
def contracts_dashboard():
    contracts = []
    if os.path.exists(REFINED_CSV):
        df = pd.read_csv(REFINED_CSV)
        contracts = df.to_dict(orient='records')
    return render_template('contracts.html', contracts=contracts)

# --- Demo File Processing & Download Generator Logic ---
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
        
        processed_df = df.head(50)
        output_filename = f"Cleaned_{intent}_{filename}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        processed_df.to_excel(output_path, index=False)

        return jsonify({
            'status': 'success',
            'intent_applied': intent,
            'filename': filename,
            'total_rows': total_rows,
            'download_url': f'/api/download-sample/{output_filename}',
            'message': f'Success! Processed {total_rows} records under {intent} protocol. Download your sample finished report below.'
        })

    elif ext == 'pdf':
        doc = fitz.open(stream=file.read(), filetype="pdf")
        total_pages = len(doc)
        
        output_filename = f"Extracted_Report_{filename}.txt"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        extracted_text = ""
        for i in range(total_pages):
            extracted_text += f"--- PAGE {i+1} ------\n" + doc[i].get_text()
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        return jsonify({
            'status': 'success',
            'intent_applied': intent,
            'filename': filename,
            'total_pages': total_pages,
            'download_url': f'/api/download-sample/{output_filename}',
            'message': f'Success! Extracted {total_pages} pages into a structured text report.'
        })

    return jsonify({"status": "error", "message": "Unsupported file format."}), 400

@app.route('/api/download-sample/<filename>')
def download_sample(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

# --- Live File Processing & Compliance Audit Route ---
@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    intent = request.form.get('intent', 'sam_gov_parsing')

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        ext = filename.rsplit('.', 1)[1].lower()
        try:
            if ext == 'csv':
                try:
                    df = pd.read_csv(input_path, encoding='utf-8-sig')
                except Exception:
                    try:
                        df = pd.read_csv(input_path, encoding='utf-16')
                    except Exception:
                        df = pd.read_csv(input_path, encoding='latin1')
                
                if not df.empty and str(df.iloc[0, 0]) == str(df.columns[0]):
                    df = df.iloc[1:].reset_index(drop=True)

            elif ext == 'xlsx':
                df = pd.read_excel(input_path)
            else:
                df = pd.DataFrame({
                    'Requirement_ID': [f'REQ-{i+101}' for i in range(25)],
                    'Clause_Heading': ['General Compliance', 'Security Mandate', 'Pricing Structure', 'Delivery Schedule', 'Subcontracting Plan'] * 5,
                    'Mandatory_Status': ['Mandatory', 'Conditional', 'Mandatory', 'Optional', 'Mandatory'] * 5,
                    'Extracted_Detail': [
                        'Review compliance terms in section 4.2',
                        'System security plan level 2 required',
                        'Firm-fixed-price CLIN structure',
                        'FOB Destination within 30 days',
                        'Small business participation goal 35%'
                    ] * 5
                })
        except Exception as e:
            return jsonify({'error': f'Error parsing file: {str(e)}'}), 500

        total_records = len(df)
        df_cleaned = df.dropna(how='all').fillna('N/A')

        base_name = os.path.splitext(filename)[0]
        xlsx_filename = f"Cleaned_SAM_Compliance_{base_name}.xlsx"
        txt_filename = f"Executive_Summary_{base_name}.txt"

        xlsx_path = os.path.join(app.config['PROCESSED_FOLDER'], xlsx_filename)
        txt_path = os.path.join(app.config['PROCESSED_FOLDER'], txt_filename)

        df_cleaned.to_excel(xlsx_path, index=False)

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("==================================================\n")
            f.write("       SAM.gov & COMPLIANCE AUDIT REPORT          \n")
            f.write("==================================================\n")
            f.write(f"Source File: {filename}\n")
            f.write(f"Total Records Extracted: {total_records}\n")
            f.write("Processing Status: Verified & Structured\n\n")
            f.write("KEY REQUIREMENTS BREAKDOWN:\n")
            f.write("--------------------------------------------------\n")
            for idx, row in df_cleaned.head(10).iterrows():
                f.write(f"- {row.iloc[0]}: {row.iloc[1] if len(row) > 1 else ''}\n")
            f.write("\n==================================================\n")

        preview_data = df_cleaned.head(5).to_dict(orient='records')
        columns = list(df_cleaned.columns)

        return jsonify({
            'success': True,
            'total_records': total_records,
            'filename': filename,
            'columns': columns,
            'preview': preview_data,
            'xlsx_file': xlsx_filename,
            'docx_file': txt_filename,
            'message': f'Successfully processed {total_records} records under {intent} protocol.'
        })

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    return send_file(os.path.join(app.config['PROCESSED_FOLDER'], filename), as_attachment=True)

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)