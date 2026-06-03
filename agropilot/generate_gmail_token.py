#!/usr/bin/env python3
"""
Generate Gmail OAuth2 token from credential gmail.
Saves token to token_gmail.json for use with Gmail API.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
]

def generate_gmail_token(credentials_file: str, output_file: str = "token_gmail.json"):
    """
    Generate Gmail OAuth2 token.
    
    Args:
        credentials_file: Path to credential_gmail.json file
        output_file: Path where to save the generated token
    """
    
    if not os.path.exists(credentials_file):
        print(f"❌ Error: Credentials file not found: {credentials_file}")
        return False
    
    try:
        print(f"📂 Using credentials: {credentials_file}")
        print(f"🔐 Requesting Gmail access...")
        
        # Create OAuth2 flow from credentials
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_file, 
            scopes=SCOPES
        )
        
        # Run local browser-based authentication
        print("🌐 Opening browser for authentication...")
        creds = flow.run_local_server(port=0)
        
        # Save token as JSON
        token_json = creds.to_json()
        with open(output_file, "w") as f:
            f.write(token_json)
        
        print(f"✅ Success! Token saved to: {output_file}")
        
        # Show token info
        token_data = json.loads(token_json)
        print(f"   - Token expiry: {token_data.get('expiry', 'N/A')}")
        print(f"   - Scopes: {', '.join(token_data.get('scopes', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    # Use provided file or default
    creds_file = sys.argv[1] if len(sys.argv) > 1 else "credential_gmail.json"
    
    generate_gmail_token(creds_file)
