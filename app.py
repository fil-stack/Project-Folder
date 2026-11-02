import os
import pandas as pd
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF for handling PDF page limits

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB Max upload cap

ALLOWED_EXTENSIONS = {'csv', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/process-demo', methods=['POST'])
def process_demo():
    user_email = request.form.get('email')
    if not user_email or '@' not in user_email:
        return jsonify({'error': 'Valid corporate or business email is required.'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded.'}), 400
        
    file = request.files['file']
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()

    # Log the lead email to your pipeline tracking file
    with open('demo_leads.csv', 'a') as f:
        f.write(f"{user_email},{filename}\n")

    # Handle CSV Demo Processing
    if ext == 'csv':
        df = pd.read_csv(file)
        total_rows = len(df)
        
        # Enforce Free Trial Limit: Max 50 Rows
        processed_df = df.head(50)
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'total_rows_detected': total_rows,
            'rows_processed': len(processed_df),
            'sample_data': processed_df.to_dict(orient='records'),
            'message': f"Free Trial Limit Applied: Processed {len(processed_df)} of {total_rows} rows." if total_rows > 50 else "Full file processed!"
        })

    # Handle PDF Data Extraction Demo
    elif ext == 'pdf':
        doc = fitz.open(stream=file.read(), filetype="pdf")
        total_pages = len(doc)
        
        # Enforce Free Trial Limit: Max 2 Pages
        extracted_text = ""
        for i in range(min(2, total_pages)):
            extracted_text += f"--- PAGE {i+1} ---\n" + doc[i].get_text()
            
        return jsonify({
            'status': 'success',
            'filename': filename,
            'total_pages_detected': total_pages,
            'pages_processed': min(2, total_pages),
            'sample_text': extracted_text,
            'message': f"Free Trial Limit Applied: Extracted {min(2, total_pages)} of {total_pages} pages." if total_pages > 2 else "Full document extracted!"
        })
@app.route('/')
def home():
    return render_template('index.html')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)