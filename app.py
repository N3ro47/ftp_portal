import os
from flask import Flask, render_template, send_file, request, abort, redirect, url_for, flash, session
from ftplib import FTP, error_perm 
from io import BytesIO
from dotenv import load_dotenv
from functools import wraps
from pathlib import Path

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

def get_files_and_dirs(ftp, path):
    dirs, files = [], []

    try:
        if path:
            ftp.cwd(path)

        for name, facts in ftp.mlsd():
            if name in ['.', '..']:
                continue
            item_type = facts.get('type')
            if item_type == 'dir':
                dirs.append({'name': name, 'type': 'dir'})
            elif item_type == 'file':
                files.append({'name': name, 'type': 'file'})

    except error_perm as e:
        if str(e).startswith('500'): # Check if it's an "Unknown command" error

            listing = []
            ftp.dir(listing.append)

            for line in listing:
                parts = line.split()
                if len(parts) < 9:
                    continue

                name = ' '.join(parts[8:])
                if name in ['.', '..']:
                    continue

                if line.startswith('d'):
                    dirs.append({'name': name, 'type': 'dir'})
                elif line.startswith('-'):
                    files.append({'name': name, 'type': 'file'})

        else:
            flash(f"Could not list directory '{path}': {e}", "danger")

    except Exception as e:
        flash(f"An unexpected FTP error occurred: {e}", "danger")

    return sorted(dirs, key=lambda x: x['name']), sorted(files, key=lambda x: x['name'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            ftp = get_ftp_connection(username, password)
            ftp.quit()
            session['user'] = username
            session['password'] = password
            
            return redirect(url_for('browse'))
        except Exception as e:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('browse'))

@app.route('/')
def index():
    return redirect(url_for('browse'))

@app.route('/user')
def user_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('browse'))

@app.route('/browse/', defaults={'path': ''})
@app.route('/browse/<path:path>')
def browse(path):
    is_logged_in = 'user' in session
    ftp = None
    try:
        if is_logged_in:
            ftp = get_ftp_connection(session['user'], session['password'])
        else:
            ftp = get_ftp_connection()

        dirs, files = get_files_and_dirs(ftp, path)
        ftp.quit()

        path_parts = list(Path(path).parts)

        return render_template('index.html',
                               dirs=dirs,
                               files=files,
                               is_logged_in=is_logged_in,
                               current_path=path,
                               path_parts=path_parts)
    except Exception as e:
        if ftp:
            ftp.quit()
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

        download_name = os.path.basename(filename)
        return send_file(memory_file, as_attachment=True, download_name=download_name)
    except Exception as e:
        return f"Download error: {e}", 500

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        abort(401, 'Please login to upload files')

    if 'file' not in request.files or request.files['file'].filename == '':
        flash('No file selected for upload.', 'warning')
        return redirect(request.referrer or url_for('browse'))

    file = request.files['file']
    target_path = request.form.get('path', '')
    remote_filepath = os.path.join(target_path, file.filename)

    try:
        ftp = get_ftp_connection(session['user'], session['password'])
        ftp.storbinary(f'STOR {remote_filepath}', file)
        ftp.quit()
        flash(f'Successfully uploaded "{file.filename}"', 'success')
        return redirect(url_for('browse', path=target_path))
    except Exception as e:
        flash(f"Upload error: {e}", "danger")
        return redirect(url_for('browse', path=target_path))


@app.route('/delete/<path:filename>', methods=['POST'])
def delete(filename):
    if 'user' not in session:
        abort(401, 'Please login to delete files')

    try:
        ftp = get_ftp_connection(session['user'], session['password'])
        ftp.delete(filename)
        ftp.quit()
        flash(f'Successfully deleted "{os.path.basename(filename)}"', 'success')
    except Exception as e:
        flash(f'Delete error: {e}', 'danger')

    parent_path = os.path.dirname(filename)
    return redirect(url_for('browse', path=parent_path))

#if __name__ == '__main__':
#    app.run(debug=True, host='0.0.0.0', port=5000)
