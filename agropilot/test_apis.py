import os
import sys
import json
import time

try:
    import requests
except ImportError:
    print("Error: 'requests' library is not installed. Please run: pip install requests")
    sys.exit(1)

import dotenv
from dotenv import load_dotenv

# Load variables from .env
dotenv_path = dotenv.find_dotenv()
load_dotenv(dotenv_path)

print(f"DEBUG: Loaded .env from: {dotenv_path}")
print(f"DEBUG: Environment keys: {[k for k in os.environ.keys() if 'SALESFORCE' in k or 'DOCUSIGN' in k or 'GOOGLE' in k or 'TAVILY' in k or 'SLACK' in k]}")

def print_result(api_name, success, message, details=None):
    status = "🟢 SUCCESS" if success else "🔴 FAILED"
    print(f"\n=========================================")
    print(f"Testing: {api_name}")
    print(f"Status:  {status}")
    print(f"Details: {message}")
    if details:
        print(f"Response: {json.dumps(details, indent=2)}")
    print(f"=========================================")

def test_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print_result("Gemini API", False, "GOOGLE_API_KEY not found in .env")
        return
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
            google_api_key=api_key,
            timeout=10
        )
        resp = llm.invoke([HumanMessage(content="Hello, respond with only the word 'Connected' if you receive this.")])
        text = resp.content.strip()
        print_result("Gemini API", True, f"Successfully communicated with Gemini. Response: '{text}'")
    except Exception as e:
        # Fallback to direct HTTP
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-3.1-flash-lite:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": "Hello, respond with only the word 'Connected' if you receive this."}]}]}
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                res_data = response.json()
                text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
                print_result("Gemini API", True, f"Successfully communicated with Gemini (HTTP). Response: '{text}'")
            else:
                # Let's try listing the models to see what is available or if key is bad
                list_url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
                list_resp = requests.get(list_url, timeout=10)
                if list_resp.status_code == 200:
                    models = [m.get("name") for m in list_resp.json().get("models", [])]
                    print_result("Gemini API", False, f"Model not found, but key is valid. Available models for this key: {models}")
                else:
                    print_result("Gemini API", False, f"HTTP Error {response.status_code}. Model list request failed: {list_resp.text}")
        except Exception as http_e:
            print_result("Gemini API", False, f"SDK Exception: {e} | HTTP Exception: {http_e}")

def test_tavily():
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print_result("Tavily API", False, "TAVILY_API_KEY not found in .env")
        return
    
    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    data = {"api_key": api_key, "query": "agriculture", "max_results": 1}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            print_result("Tavily API", True, "Successfully connected to Tavily.")
        else:
            print_result("Tavily API", False, f"HTTP Error {response.status_code}", response.text)
    except Exception as e:
        print_result("Tavily API", False, f"Exception occurred: {e}")

def test_slack():
    token = os.getenv("SLACK_API_KEY")
    if not token:
        print_result("Slack API", False, "SLACK_API_KEY not found in .env")
        return
    
    url = "https://slack.com/api/auth.test"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, timeout=10)
        res_data = response.json()
        if response.status_code == 200 and res_data.get("ok"):
            print_result("Slack API", True, f"Successfully connected. Bot User: {res_data.get('user')} (Workspace: {res_data.get('team')})")
        else:
            print_result("Slack API", False, "Authentication failed.", res_data)
    except Exception as e:
        print_result("Slack API", False, f"Exception occurred: {e}")

def test_salesforce():
    client_id = os.getenv("SALESFORCE_CLIENT_ID")
    client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
    username = os.getenv("SALESFORCE_USERNAME")
    password = os.getenv("SALESFORCE_PASSWORD")
    login_url = os.getenv("SALESFORCE_LOGIN_URL", "https://login.salesforce.com").strip()
    
    missing = []
    if not client_id: missing.append("SALESFORCE_CLIENT_ID")
    if not client_secret: missing.append("SALESFORCE_CLIENT_SECRET")
    if not username: missing.append("SALESFORCE_USERNAME")
    if not password: missing.append("SALESFORCE_PASSWORD")
    
    if missing:
        print_result("Salesforce API", False, f"Missing Salesforce credentials in .env: {', '.join(missing)}")
        return
    
    # Salesforce OAuth token endpoint
    token_url = f"{login_url}/services/oauth2/token"
    # ----------------------------------------------------------------------
    # Build the JWT Bearer assertion (requires private key)
    # ----------------------------------------------------------------------
    import time, jwt, pathlib
    private_key_path = os.getenv("SALESFORCE_PRIVATE_KEY_PATH")
    if not private_key_path or not pathlib.Path(private_key_path).exists():
        print_result("Salesforce API", False, "Missing Salesforce private key for JWT flow.")
        return
    with open(private_key_path, "r") as key_file:
        private_key = key_file.read()
    # JWT claims
    now = int(time.time())
    payload = {
        "iss": client_id,
        "sub": username,
        "aud": login_url,
        "exp": now + 300,
    }
    assertion = jwt.encode(payload, private_key, algorithm="RS256")
    # Request token using JWT Bearer flow
    token_data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion,
    }
    try:
        response = requests.post(token_url, data=token_data, timeout=10)
        res_data = response.json()
        if response.status_code == 200:
            print_result("Salesforce API", True, "Successfully authenticated via JWT.", {
                "instance_url": res_data.get("instance_url"),
                "access_token": res_data.get("access_token"),
            })
        else:
            print_result("Salesforce API", False, f"Authentication failed. HTTP {response.status_code}", res_data)
    except Exception as e:
        print_result("Salesforce API", False, f"Exception occurred: {e}")

def test_docusign():
    user_id = os.getenv("DOCUSIGN_USER_ID")
    account_id = os.getenv("DOCUSIGN_API_ACCOUNT_ID")
    integration_key = os.getenv("DOCUSIGN_INTEGRATION_KEY")
    private_key_path = os.getenv("DOCUSIGN_PRIVATE_KEY_PATH")
    auth_server = os.getenv("DOCUSIGN_AUTH_SERVER", "account-d.docusign.com").strip()
    
    if not all([user_id, account_id, integration_key, private_key_path]):
        print_result("DocuSign API", False, "One or more DocuSign credentials (User ID, Account ID, Integration Key, Private Key Path) missing in .env")
        return
    
    if not os.path.exists(private_key_path):
        print_result("DocuSign API", False, f"Private key file not found at path: {private_key_path}")
        return
    
    try:
        # We need PyJWT and cryptography to sign DocuSign JWT assertions.
        import jwt
        from datetime import datetime, timedelta
    except ImportError:
        print_result("DocuSign API", False, "Python 'PyJWT' and 'cryptography' packages are required to sign DocuSign requests. Install with: pip install PyJWT cryptography")
        return
        
    try:
        with open(private_key_path, "r") as f:
            private_key = f.read()
            
        # Create JWT payload
        now = int(time.time())
        payload = {
            "iss": integration_key,
            "sub": user_id,
            "iat": now,
            "exp": now + 3600,
            "aud": auth_server,
            "scope": "signature impersonation"
        }
        
        # Sign JWT
        assertion = jwt.encode(payload, private_key, algorithm="RS256")
        
        # Request access token
        url = f"https://{auth_server}/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion
        }
        
        response = requests.post(url, headers=headers, data=data, timeout=10)
        res_data = response.json()
        
        if response.status_code == 200:
            print_result("DocuSign API", True, "Successfully authenticated. Access token retrieved.", {
                "token_type": res_data.get("token_type"),
                "expires_in": res_data.get("expires_in")
            })
        else:
            # Check for consent required error which is very common for first-time DocuSign API users
            error = res_data.get("error")
            if error == "consent_required":
                consent_url = f"https://{auth_server}/oauth/auth?response_type=code&scope=signature%20impersonation&client_id={integration_key}&redirect_uri=https://localhost"
                print_result("DocuSign API", False, f"Consent Required! You must grant consent to your application first.\nOpen this URL in your browser, log in, grant permissions, then run this test script again:\n\n{consent_url}")
            else:
                print_result("DocuSign API", False, f"Authentication failed. HTTP {response.status_code}", res_data)
    except Exception as e:
        print_result("DocuSign API", False, f"Exception occurred: {e}")
def test_gmail():
    import os
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds_path = os.getenv("CREDENTIAL_GMAIL_PATH", "credential_gmail.json")
    token_path = "token_gmail.json"
    scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

    if not os.path.exists(creds_path):
        print_result("Gmail API", False, f"Credentials file not found at {creds_path}")
        return

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, scopes)
        creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])
        label_names = [lbl["name"] for lbl in labels]
        print_result("Gmail API", True, f"Retrieved {len(labels)} labels", {"labels": label_names})
    except Exception as e:
        print_result("Gmail API", False, f"Exception occurred: {e}")

if __name__ == "__main__":
    print("=== STARTING API TESTS ===")
    test_gemini()
    test_tavily()
    test_slack()
    test_salesforce()
    test_docusign()
    test_gmail()
    
    print("\n=== API TESTS COMPLETED ===")
