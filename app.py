import os
from flask import Flask, render_template, send_file, request, abort, redirect, url_for, flash, session
from ftplib import FTP
from io import BytesIO
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

FTP_HOST = os.getenv('FTP_HOST')
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')

def get_ftp_connection(username=None, password=None):
    ftp = FTP(FTP_HOST)
    if username and password:
        ftp.login(username, password)
    else:
        ftp.login(FTP_USER, FTP_PASS)
    return ftp

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            # Test FTP connection with user credentials
            ftp = get_ftp_connection(username, password)
            ftp.quit()
            session['user'] = username
            session['password'] = password
            return redirect(url_for('user_dashboard'))
        except Exception as e:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/')
def index():
    try:
        ftp = get_ftp_connection()
        files = ftp.nlst()
        ftp.quit()
        return render_template('index.html', files=files, is_logged_in=False)
    except Exception as e:
        return f"FTP error: {e}", 500

@app.route('/user')
def user_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    try:
        ftp = get_ftp_connection(session['user'], session['password'])
        files = ftp.nlst()
        ftp.quit()
        return render_template('index.html', files=files, is_logged_in=True)
    except Exception as e:
        return f"FTP error: {e}", 500

@app.route('/download/<path:filename>')
def download(filename):
    try:
        if 'user' in session:
            ftp = get_ftp_connection(session['user'], session['password'])
        else:
            ftp = get_ftp_connection()
        memory_file = BytesIO()
        ftp.retrbinary(f'RETR {filename}', memory_file.write)
        memory_file.seek(0)
        ftp.quit()
        return send_file(memory_file, as_attachment=True, download_name=filename)
    except Exception as e:
        return f"Download error: {e}", 500

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return 'Please login to upload files', 401
    
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    try:
        ftp = get_ftp_connection(session['user'], session['password'])
        ftp.storbinary(f'STOR {file.filename}', file)
        ftp.quit()
        return redirect(url_for('user_dashboard'))
    except Exception as e:
        return f"Upload error: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
