from flask import Flask, render_template, request, redirect, url_for, send_file
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from PIL import Image
from io import BytesIO
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ERROR_CORRECTION_MAP = {
    'L': ERROR_CORRECT_L,
    'M': ERROR_CORRECT_M,
    'Q': ERROR_CORRECT_Q,
    'H': ERROR_CORRECT_H,
}

@app.route('/health', methods=['GET', 'POST'])
def health():
    return {"ok": True}, 200

@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        link = request.form.get('link')
        box_size = int(request.form.get('box_size', 10))
        border = int(request.form.get('border', 4))
        fill_color = request.form.get('fill_color', 'black')
        back_color = request.form.get('back_color', 'white')
        error_level = request.form.get('error_correction', 'H')

        # Handle uploaded logo image
        logo_file = request.files.get('logo')
        logo_path = None
        if logo_file and logo_file.filename:
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_file.filename)
            logo_file.save(logo_path)

        # Generate QR Code
        qr = qrcode.QRCode(
            error_correction=ERROR_CORRECTION_MAP.get(error_level, ERROR_CORRECT_H),
            box_size=box_size,
            border=border,
        )
        qr.add_data(link)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGB')

        # If logo provided, embed it
        if logo_path:
            logo = Image.open(logo_path)

            # Calculate logo size as 15% of QR code
            qr_width, qr_height = img_qr.size
            factor = 5
            size = qr_width // factor
            logo.thumbnail((size, size), Image.LANCZOS)

            # Calculate position and paste logo
            pos = ((qr_width - logo.size[0]) // 2, (qr_height - logo.size[1]) // 2)
            img_qr.paste(logo, pos)

        # Save to BytesIO
        buf = BytesIO()
        img_qr.save(buf, format='PNG')
        buf.seek(0)

        return send_file(buf, mimetype='image/png', as_attachment=False, download_name='qr.png')

    return render_template('upload.html')

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)