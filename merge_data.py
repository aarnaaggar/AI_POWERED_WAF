import pandas as pd
import os
import random

def load_payloads(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            # Read all lines that have at least 3 characters
            return [line.strip() for line in f if line.strip() and len(line.strip()) > 2]
    except Exception as e:
        return []

# 1. Load Malicious Data (READ EVERYTHING)
malicious_payloads = []
payload_dir = 'payloads'

if os.path.exists(payload_dir):
    for filename in os.listdir(payload_dir):
        filepath = os.path.join(payload_dir, filename)
        # Check if it's a file (ignoring extensions entirely)
        if os.path.isfile(filepath):
            extracted = load_payloads(filepath)
            malicious_payloads.extend(extracted)
            print(f"Loaded {len(extracted)} payloads from {filename}")

# 2. Inject TRICKY Evasion & Core Attacks heavily
core_attacks = [
    "U N I O N   S E L E C T   * F R O M   u s e r s",
    "s E l E c T * f R o M a d m i n",
    "admin%00' OR 1=1",
    "%3Cscript%3Ealert(1)%3C%2Fscript%3E",
    "<sCrIpT>pRoMpT('Hacked')</ScRiPt>",
    "1' o r '1'='1",
    "admin'/* bypass */OR 1=1",
    "' OR 1=1 --",
    "' OR '1'='1",
    "admin' --",
    "<script>alert(document.cookie)</script>",
    "onerror=alert(1)",
    "javascript:alert(1)",
    "../../../../etc/passwd",
    "../../../windows/win.ini",
    "; cat /etc/passwd",
    "| whoami"
]

# Multiply the core attacks massively (17 attacks * 600 = 10,200 guaranteed malicious rows)
malicious_payloads.extend(core_attacks * 600) 

# Add some randomness to create unique malicious payloads
for _ in range(3000):
    malicious_payloads.append(f"' OR {random.randint(1,9)}={random.randint(1,9)} --")
    malicious_payloads.append(f"<script>var a={random.randint(1,999)};alert(a)</script>")

# 3. Generate Benign Data (Ensure we have at least 30,000 to match)
safe_words = ["home", "about", "contact", "user", "profile", "settings", "search", "index", "dashboard", "login", "register", "blog", "cart", "checkout"]
benign_payloads = []

for _ in range(25000):
    benign_payloads.append(random.choice(safe_words))
    benign_payloads.append(f"/{random.choice(safe_words)}?id={random.randint(1, 9999)}")
    benign_payloads.append(f"/{random.choice(safe_words)}?session={random.randint(10000, 99999)}")
    # Generate random alphanumeric tokens
    benign_payloads.append(''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=random.randint(8, 15))))

# 4. FORCE STRICT 50/50 BALANCING
df_malicious = pd.DataFrame({'payload': malicious_payloads, 'label': 1})
df_benign = pd.DataFrame({'payload': benign_payloads, 'label': 0})

# Find the exact matched length to perfectly balance it
exact_length = min(len(df_malicious), len(df_benign))

print(f"\nBefore Balancing - Found {len(df_malicious)} Malicious and {len(df_benign)} Benign.")

# Sample them to be perfectly equal
df_malicious = df_malicious.sample(n=exact_length, random_state=42)
df_benign = df_benign.sample(n=exact_length, random_state=42)

# Combine and shuffle
df_final = pd.concat([df_malicious, df_benign]).sample(frac=1, random_state=42).reset_index(drop=True)
df_final.to_csv('owasp_data.csv', index=False)

print(f"\n✅ Saved EXACTLY balanced dataset: {len(df_final)} rows total.")
print(f"   - Malicious: {len(df_malicious)}")
print(f"   - Benign: {len(df_benign)}")