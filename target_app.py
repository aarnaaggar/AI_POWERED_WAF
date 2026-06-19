# target_app.py
from flask import Flask, request

app = Flask(__name__)

# The sleek login page
LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Nexus Bank | Secure Core</title>
    <style>
        body { font-family: 'Courier New', monospace; background-color: #050810; color: #8aa4c8; margin: 0; padding: 0; }
        .header { background: #0a0f1d; padding: 25px; border-bottom: 2px solid #00e676; text-align: center; }
        .header h1 { margin: 0; color: #00e676; letter-spacing: 4px; font-size: 32px; text-transform: uppercase; }
        .warning-bar { background: #ff1744; color: #fff; padding: 8px; text-align: center; font-size: 13px; font-weight: bold; letter-spacing: 2px; }
        .content { max-width: 500px; margin: 60px auto; background: #0c1222; padding: 40px; border-radius: 6px; border: 1px solid #1f2b44; }
        input { width: 100%; padding: 15px; margin-bottom: 20px; background: #050810; border: 1px solid #283759; color: #00e676; font-family: 'Courier New', monospace; box-sizing: border-box; font-size: 16px; outline: none; }
        button { width: 100%; padding: 15px; background: #00e676; color: #050810; border: none; font-weight: bold; font-size: 16px; cursor: pointer; letter-spacing: 2px; transition: 0.3s; }
        button:hover { background: #00c853; }
        .error { color: #ff1744; margin-bottom: 20px; font-weight: bold; text-align: center; }
    </style>
</head>
<body>
    <div class="warning-bar">RESTRICTED ACCESS - LEVEL 4 CLEARANCE REQUIRED</div>
    <div class="header"><h1>NEXUS GLOBAL FINANCE</h1></div>
    <div class="content">
        <h2 style="color: #fff; margin-top: 0; border-bottom: 1px solid #1f2b44; padding-bottom: 10px;">> Identity Verification</h2>
        {error_msg}
        <form method="POST" action="/proxy/api/v1/auth"> 
            <input type="text" name="admin_id" placeholder="Admin ID (Use: ADM_001)">
            <input type="password" name="password" placeholder="Passcode (Use: nexus2026)">
            <button type="submit">Initialize Link</button>
        </form>
    </div>
</body>
</html>
"""

# The Success Dashboard (If login is correct)
SUCCESS_PAGE = """
<!DOCTYPE html>
<html>
<body style="font-family: 'Courier New', monospace; background-color: #050810; color: #00e676; text-align: center; padding-top: 100px;">
    <h1 style="font-size: 40px;">✅ ACCESS GRANTED</h1>
    <h2>Welcome to the Nexus Core Ledger, Admin.</h2>
    <p style="color: #8aa4c8;">Secure connection established via ShieldAI WAF.</p>
    <a href="/" style="color: #007bff; text-decoration: none;">[ Logout / Disconnect ]</a>
</body>
</html>
"""




@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def home(path):
    # Using .replace instead of .format to avoid CSS curly brace conflicts
    return LOGIN_PAGE.replace("{error_msg}", "")

@app.route('/api/v1/auth', methods=['POST'])
def auth():
    # Capture the POST data
    admin_id = request.form.get('admin_id')
    password = request.form.get('password')
    
    # Check credentials
    if admin_id == 'ADM_001' and password == 'nexus2026':
        return SUCCESS_PAGE
    else:
        error_html = "<div class='error'>[!] ERROR: INVALID CREDENTIALS</div>"
        return LOGIN_PAGE.replace("{error_msg}", error_html)

if __name__ == '__main__':
    app.run(port=5001, debug=True)


