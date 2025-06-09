# FTP Portal

A web-based FTP portal that allows both public access to default FTP files and user-specific access with upload capabilities.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- On Linux/Mac:
```bash
source venv/bin/activate
```
- On Windows:
```bash
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following variables:
```
FTP_HOST=your_ftp_host
FTP_USER=your_default_ftp_user
FTP_PASS=your_default_ftp_password
SECRET_KEY=your_secret_key_for_sessions
```

## Running the Application

1. Make sure your virtual environment is activated

2. Run the Flask application:
```bash
python app.py
```

3. Access the application at `http://localhost:5000`

## Features

- Public access to default FTP files (download only)
- User login to access personal FTP space
- File upload and download for logged-in users
- Modern, responsive UI using Bootstrap

## Requirements

- Python 3.7 or higher
- FTP server with user accounts
- Internet connection to access the FTP server 