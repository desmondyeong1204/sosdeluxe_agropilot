"""
mcp_server.py — AgriQuote True MCP Tool Server
AI Marathon 2026 · Problem Statement 1: The Autonomous Sales Engineer

Registers all external API tools as MCP-compliant tool definitions.
The agent DYNAMICALLY selects which tools to call — no hardcoded order.

Tools exposed:
  salesforce_create_opportunity   → Layer 4: CRM record creation
  salesforce_get_account          → Layer 4: look up existing account
  docusign_send_envelope          → Layer 4: e-signature dispatch
  slack_notify_manager            → Layer 4: deal notification
  gmail_send_quote                → Layer 4: quote delivery to prospect
  tavily_search_equipment         → Layer 1: real-time product/pricing search
  tavily_search_compliance        → Layer 1: live regulatory lookup
  validate_intent                 → Layer 2 GUARDRAIL: intent classifier

Run standalone:
  python mcp_server.py
"""

import os, json, logging, base64, textwrap
from datetime import datetime
from typing import Any
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from urllib.parse import urlparse

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("agriquote.mcp")

mcp = FastMCP("AgriQuote MCP Server")


def _host_only(value: str) -> str:
    """Normalize a host value that may include scheme/path."""
    if not value:
        return value
    v = value.strip()
    if "://" in v:
        parsed = urlparse(v)
        return parsed.netloc or v
    return v.split("/")[0]

# ─────────────────────────────────────────────────────────────────────────────
# GUARDRAIL LAYER — Intent Validator (must pass before any write tool fires)
# ─────────────────────────────────────────────────────────────────────────────

ALLOWED_INTENTS = {
    "create_crm_record", "send_esignature", "notify_team",
    "send_quote_email", "search_product_data", "search_compliance_rules",
    "lookup_account", "generate_quote",
    # Also allow tool-names directly (LLM sometimes uses these as action labels)
    "salesforce_get_account", "salesforce_create_opportunity",
    "docusign_send_envelope", "slack_notify_manager", "gmail_send_quote",
    "tavily_search_equipment", "tavily_search_compliance",
}

BLOCKED_PATTERNS = [
    "ignore previous", "disregard instructions", "jailbreak",
    "act as", "pretend you are", "bypass", "override system",
    "delete all", "drop table", "exec(", "eval(",
    "system prompt", "forget your instructions",
    "__import__", "os.system", "subprocess",
]

@mcp.tool()
def validate_intent(action: str, payload_summary: str) -> dict:
    """
    GUARDRAIL — validates that a requested tool action is within allowed scope.
    Must be called before any write tool (Salesforce, DocuSign, Slack, Gmail).
    Returns {approved: bool, reason: str}.

    Args:
        action: the intended action name (must be in ALLOWED_INTENTS)
        payload_summary: brief plain-English description of what will be sent
    """
    # Check action scope
    if action not in ALLOWED_INTENTS:
        log.warning(f"GUARDRAIL BLOCKED: unknown action '{action}'")
        return {
            "approved": False,
            "reason": f"Action '{action}' is not in the permitted action scope. Allowed: {sorted(ALLOWED_INTENTS)}"
        }

    # Check for prompt injection patterns in payload
    combined = (action + " " + payload_summary).lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in combined:
            log.warning(f"GUARDRAIL BLOCKED: injection pattern detected: '{pattern}'")
            return {
                "approved": False,
                "reason": f"Payload rejected — potential prompt injection pattern detected: '{pattern}'"
            }

    log.info(f"GUARDRAIL APPROVED: action='{action}'")
    return {"approved": True, "reason": "Intent validated — within permitted scope."}


# ─────────────────────────────────────────────────────────────────────────────
# SALESFORCE TOOLS
# ─────────────────────────────────────────────────────────────────────────────

def _sf_client():
    """
    Returns an authenticated Salesforce client.

    Important: this project’s Salesforce org has SOAP login disabled, so we must
    use OAuth (JWT bearer) rather than username/password SOAP login.
    """
    from simple_salesforce import Salesforce
    import jwt as pyjwt
    import pathlib
    import requests as req
    import time as _time

    login_url = (os.getenv("SALESFORCE_LOGIN_URL") or "https://login.salesforce.com").strip()
    client_id = os.getenv("SALESFORCE_CLIENT_ID")
    username = os.getenv("SALESFORCE_USERNAME")
    private_key_path = os.getenv("SALESFORCE_PRIVATE_KEY_PATH")

    if not client_id or not username or not private_key_path:
        raise RuntimeError("Missing SALESFORCE_CLIENT_ID / SALESFORCE_USERNAME / SALESFORCE_PRIVATE_KEY_PATH")

    pk_path = pathlib.Path(private_key_path)
    if not pk_path.exists():
        raise RuntimeError(f"Salesforce private key not found at {private_key_path}")

    private_key = pk_path.read_text()
    now = int(_time.time())
    payload = {"iss": client_id, "sub": username, "aud": login_url, "exp": now + 300}
    assertion = pyjwt.encode(payload, private_key, algorithm="RS256")

    token_url = f"{login_url}/services/oauth2/token"
    token_resp = req.post(
        token_url,
        data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion},
        timeout=20,
    )
    token_resp.raise_for_status()
    token_json = token_resp.json()

    access_token = token_json["access_token"]
    instance_url = token_json["instance_url"]

    # simple-salesforce can operate with an existing OAuth session_id.
    return Salesforce(instance_url=instance_url, session_id=access_token, version="60.0")


@mcp.tool()
def salesforce_get_account(company_name: str) -> dict:
    """
    Look up an existing Salesforce Account by company name.
    Returns account ID and details if found, or signals 'not_found'.

    Args:
        company_name: the dealer or farm operator company name to search
    """
    try:
        sf = _sf_client()
        escaped = company_name.replace("'", "\\'")
        result = sf.query(
            f"SELECT Id, Name, BillingState, Phone FROM Account "
            f"WHERE Name LIKE '%{escaped}%' LIMIT 1"
        )
        records = result.get("records", [])
        if records:
            r = records[0]
            log.info(f"SF account found: {r['Id']} — {r['Name']}")
            return {"found": True, "account_id": r["Id"], "name": r["Name"], "state": r.get("BillingState")}
        return {"found": False, "account_id": None, "name": company_name}
    except Exception as e:
        log.error(f"SF get_account error: {e}")
        return {"found": False, "error": str(e), "account_id": None}


@mcp.tool()
def salesforce_create_opportunity(
    rfq_id: str,
    dealer_company: str,
    farm_operator: str,
    equipment: str,
    quote_total: float,
    close_date: str,
    stage: str = "Proposal/Price Quote",
    description: str = "",
) -> dict:
    """
    Create a Salesforce Opportunity record for an approved AgriQuote deal.
    Automatically links to existing Account if found, otherwise creates a new one.

    Args:
        rfq_id: AgriQuote RFQ identifier e.g. AQ-2026-0412
        dealer_company: name of the dealership
        farm_operator: end customer / farm operator name
        equipment: equipment description e.g. "John Deere 7R 330 — full precision config"
        quote_total: total deal value in USD (or local currency equivalent)
        close_date: expected close date in YYYY-MM-DD format
        stage: Salesforce opportunity stage (default: Proposal/Price Quote)
        description: optional notes or compliance summary
    """
    try:
        sf = _sf_client()

        # Try to find existing account
        account = salesforce_get_account(dealer_company)
        if account.get("found"):
            account_id = account["account_id"]
        else:
            # Create a new Account
            new_acct = sf.Account.create({
                "Name": dealer_company,
                "Description": f"AgriQuote auto-created — dealer for {farm_operator}",
                "Type": "Partner",
            })
            account_id = new_acct["id"]
            log.info(f"SF new account created: {account_id}")

        opp = sf.Opportunity.create({
            "Name": f"{rfq_id} — {farm_operator} — {equipment[:40]}",
            "AccountId": account_id,
            "StageName": stage,
            "CloseDate": close_date,
            "Amount": quote_total,
            "Description": description or f"AgriQuote pipeline | Dealer: {dealer_company} | Operator: {farm_operator}",
            "LeadSource": "AgriQuote AI Pipeline",
        })

        opp_id = opp["id"]
        opp_url = f"https://login.salesforce.com/{opp_id}"
        log.info(f"SF opportunity created: {opp_id}")
        return {
            "success": True,
            "opportunity_id": opp_id,
            "opportunity_url": opp_url,
            "account_id": account_id,
        }

    except Exception as e:
        log.error(f"SF create_opportunity error: {e}")
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# DOCUSIGN TOOL
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def docusign_send_envelope(
    signer_name: str,
    signer_email: str,
    rfq_id: str,
    quote_text: str,
    subject: str = "",
) -> dict:
    """
    Send a DocuSign envelope containing the AgriQuote quotation document.
    The quote_text is embedded as a plain-text document for e-signature.

    Args:
        signer_name: full name of the person who must sign
        signer_email: email address of the signer
        rfq_id: quote reference number for the envelope subject
        quote_text: the full quotation document text to send for signature
        subject: optional custom email subject (auto-generated if blank)
    """
    try:
        from docusign_esign import ApiClient, EnvelopesApi, EnvelopeDefinition
        from docusign_esign import Document, Signer, SignHere, Tabs, Recipients
        import jwt as pyjwt
        import requests as req
        import time as _time

        # Build JWT access token
        private_key_path = os.getenv("DOCUSIGN_PRIVATE_KEY_PATH", "docusign_private.pem")
        integration_key  = os.getenv("DOCUSIGN_INTEGRATION_KEY")
        user_id          = os.getenv("DOCUSIGN_USER_ID")
        auth_server      = _host_only(os.getenv("DOCUSIGN_AUTH_SERVER", "account-d.docusign.com"))
        account_id       = os.getenv("DOCUSIGN_API_ACCOUNT_ID")
        base_path        = os.getenv("DOCUSIGN_BASE_PATH", "https://demo.docusign.net/restapi")

        missing = [k for k, v in {
            "DOCUSIGN_PRIVATE_KEY_PATH": private_key_path,
            "DOCUSIGN_INTEGRATION_KEY": integration_key,
            "DOCUSIGN_USER_ID": user_id,
            "DOCUSIGN_API_ACCOUNT_ID": account_id,
        }.items() if not v]
        if missing:
            return {"success": False, "error": f"Missing DocuSign config: {', '.join(missing)}"}

        # Match test_apis.py behaviour: read key as text for PyJWT
        with open(private_key_path, "r") as f:
            private_key = f.read()

        # Match test_apis.py payload/claims and token exchange
        now = int(_time.time())
        payload = {
            "iss": integration_key,
            "sub": user_id,
            "iat": now,
            "exp": now + 3600,
            "aud": auth_server,
            "scope": "signature impersonation",
        }
        assertion = pyjwt.encode(payload, private_key, algorithm="RS256")
        if isinstance(assertion, bytes):
            assertion = assertion.decode("utf-8")

        token_resp = req.post(
            f"https://{auth_server}/oauth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion},
            timeout=20,
        )
        if token_resp.status_code != 200:
            # Surface the exact DocuSign error payload (critical for diagnosing 400s)
            err_text = token_resp.text
            try:
                err_json = token_resp.json()
                err_text = json.dumps(err_json)
            except Exception:
                pass
            log.error(f"DocuSign token error HTTP {token_resp.status_code}: {err_text[:500]}")
            return {"success": False, "error": f"DocuSign token request failed HTTP {token_resp.status_code}", "details": err_text}

        access_token = token_resp.json().get("access_token")
        if not access_token:
            return {"success": False, "error": "DocuSign token response missing access_token", "details": token_resp.text}

        # Build envelope
        api_client = ApiClient()
        api_client.host = base_path
        api_client.set_default_header("Authorization", f"Bearer {access_token}")

        doc_b64 = base64.b64encode(quote_text.encode()).decode()
        document = Document(
            document_base64=doc_b64,
            name=f"AgriQuote {rfq_id}",
            file_extension="txt",
            document_id="1",
        )

        sign_here = SignHere(
            anchor_string="TOTAL SECURED DEAL VALUE",
            anchor_units="pixels",
            anchor_y_offset="20",
            anchor_x_offset="0",
        )

        signer = Signer(
            email=signer_email,
            name=signer_name,
            recipient_id="1",
            routing_order="1",
            tabs=Tabs(sign_here_tabs=[sign_here]),
        )

        envelope = EnvelopeDefinition(
            email_subject=subject or f"AgriQuote {rfq_id} — Please Sign Your Equipment Configuration",
            documents=[document],
            recipients=Recipients(signers=[signer]),
            status="sent",
        )

        envelopes_api = EnvelopesApi(api_client)
        result = envelopes_api.create_envelope(account_id, envelope_definition=envelope)
        envelope_id = result.envelope_id

        log.info(f"DocuSign envelope sent: {envelope_id} → {signer_email}")
        return {
            "success": True,
            "envelope_id": envelope_id,
            "signer_email": signer_email,
            "status": "sent",
        }

    except Exception as e:
        log.error(f"DocuSign error: {e}")
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# SLACK TOOL
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def slack_notify_manager(
    rfq_id: str,
    dealer_company: str,
    farm_operator: str,
    equipment: str,
    quote_total: float,
    gross_margin_pct: float,
    win_probability_pct: int,
    recommendation: str,
    salesforce_url: str = "",
    currency_symbol: str = "$",
) -> dict:
    """
    Post a deal notification to the Slack sales manager channel.
    Triggered automatically when a quote is approved via HITL.

    Args:
        rfq_id: quote reference
        dealer_company: dealership name
        farm_operator: end customer name
        equipment: equipment summary
        quote_total: total deal value
        gross_margin_pct: blended gross margin percentage
        win_probability_pct: Sentinel win probability 0-100
        recommendation: Sentinel recommendation string
        salesforce_url: optional Salesforce opportunity URL
        currency_symbol: currency prefix for display
    """
    try:
        import requests as req

        token = os.getenv("SLACK_API_KEY") or ""
        if not token:
            return {"success": False, "error": "SLACK_API_KEY not configured"}

        channel = os.getenv("SLACK_CHANNEL", "#agriquote-deals").strip()
        # Slack API accepts channel ID or name; normalize "#name" → "name"
        if channel.startswith("#"):
            channel = channel[1:]

        rec_emoji = "✅" if "APPROVE" in recommendation.upper() else ("⚠️" if "NEGOTIATE" in recommendation.upper() else "🚨")
        margin_color = "good" if gross_margin_pct >= 20 else ("warning" if gross_margin_pct >= 10 else "danger")

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🌾 AgriQuote Deal Alert — {rfq_id}"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Dealer:*\n{dealer_company}"},
                    {"type": "mrkdwn", "text": f"*Farm Operator:*\n{farm_operator}"},
                    {"type": "mrkdwn", "text": f"*Equipment:*\n{equipment}"},
                    {"type": "mrkdwn", "text": f"*Quote Total:*\n`{currency_symbol}{quote_total:,.0f}`"},
                    {"type": "mrkdwn", "text": f"*Gross Margin:*\n`{gross_margin_pct:.1f}%`"},
                    {"type": "mrkdwn", "text": f"*Win Probability:*\n`{win_probability_pct}%`"},
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"{rec_emoji} *Recommendation:* {recommendation}"}
            },
        ]

        if salesforce_url:
            blocks.append({
                "type": "actions",
                "elements": [{
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View in Salesforce"},
                    "url": salesforce_url,
                    "style": "primary",
                }]
            })

        blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"Sent by AgriQuote AI Pipeline · {datetime.now().strftime('%Y-%m-%d %H:%M')}"}]
        })

        resp = req.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"},
            json={"channel": channel, "blocks": blocks, "text": f"AgriQuote Deal: {rfq_id}"},
            timeout=20,
        )
        data = resp.json()
        if resp.status_code == 200 and data.get("ok"):
            log.info(f"Slack notification sent: ts={data.get('ts')}")
            return {"success": True, "ts": data.get("ts"), "channel": channel}
        return {"success": False, "error": f"Slack API error HTTP {resp.status_code}", "details": data}

    except Exception as e:
        log.error(f"Slack error: {e}")
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# GMAIL TOOL
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def gmail_send_quote(
    to_email: str,
    to_name: str,
    from_name: str,
    rfq_id: str,
    equipment: str,
    quote_total: float,
    quote_text: str,
    currency_symbol: str = "$",
) -> dict:
    """
    Send the completed quotation to the prospect via Gmail.
    Uses Gmail API with OAuth2 credentials from .env.

    Args:
        to_email: recipient email address
        to_name: recipient display name
        from_name: sender display name (dealer rep)
        rfq_id: quote reference number
        equipment: equipment summary for subject line
        quote_total: total deal value for subject line
        quote_text: full quotation document text to attach/embed
        currency_symbol: currency prefix
    """
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        import os as _os

        # Prefer using an existing OAuth token file (same pattern as test_apis.py),
        # then fall back to env-based credentials.
        scopes = [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.compose",
        ]
        default_token_path = _os.path.join(_os.path.dirname(__file__), "token_gmail.json")
        token_path = _os.getenv("GMAIL_TOKEN_PATH", default_token_path)
        creds = None

        if _os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, scopes)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())

            # If token was originally minted with narrower scopes, it cannot be used for send.
            existing_scopes = set(getattr(creds, "scopes", []) or [])
            required_scopes = set(scopes)
            if existing_scopes and not required_scopes.issubset(existing_scopes):
                return {
                    "success": False,
                    "error": "Existing token_gmail.json does not include gmail.send/gmail.compose scopes.",
                    "details": {
                        "token_path": token_path,
                        "required_scopes": sorted(required_scopes),
                        "token_scopes": sorted(existing_scopes),
                    },
                }

        if not creds or not creds.valid:
            creds_data = {
                "token": os.getenv("GMAIL_ACCESS_TOKEN"),
                "refresh_token": os.getenv("GMAIL_REFRESH_TOKEN"),
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": os.getenv("GMAIL_CLIENT_ID"),
                "client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
                "scopes": scopes,
            }
            # Only build from env if we actually have the required fields.
            if not all([creds_data.get("refresh_token"), creds_data.get("client_id"), creds_data.get("client_secret")]):
                return {
                    "success": False,
                    "error": "Gmail not configured for sending. Provide token_gmail.json with gmail.send scope, "
                             "or set GMAIL_REFRESH_TOKEN + GMAIL_CLIENT_ID + GMAIL_CLIENT_SECRET.",
                }
            creds = Credentials.from_authorized_user_info(creds_data, scopes=scopes)

        service = build("gmail", "v1", credentials=creds)

        msg = MIMEMultipart("mixed")
        msg["To"] = f"{to_name} <{to_email}>"
        msg["Subject"] = f"Your AgriQuote Configuration — {rfq_id} | {equipment[:50]} | {currency_symbol}{quote_total:,.0f}"

        body = textwrap.dedent(f"""
        Dear {to_name},

        Thank you for your enquiry. Please find your AgriQuote equipment configuration
        attached to this email ({rfq_id}).

        Our AI pipeline has validated every component for technical compatibility and
        regional compliance. Please review the attached quote and sign via DocuSign
        to confirm the order.

        Equipment: {equipment}
        Total Value: {currency_symbol}{quote_total:,.0f}

        Please don't hesitate to reach out with any questions.

        Warm regards,
        {from_name}
        Powered by AgriQuote · Autonomous Sales Engineer
        """).strip()

        msg.attach(MIMEText(body, "plain"))

        # Attach quote as .txt
        attachment = MIMEBase("text", "plain")
        attachment.set_payload(quote_text.encode())
        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", f'attachment; filename="AgriQuote_{rfq_id}.txt"')
        msg.attach(attachment)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()

        log.info(f"Gmail sent: messageId={result['id']} → {to_email}")
        return {"success": True, "message_id": result["id"], "to": to_email}

    except Exception as e:
        log.error(f"Gmail error: {e}")
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# TAVILY TOOLS (Layer 1 — Knowledge Core)
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def tavily_search_equipment(query: str, max_results: int = 5) -> dict:
    """
    Search for agricultural equipment SKUs, pricing, and specifications
    using Tavily real-time web search. Used by the Configurator Agent
    to get live dealer pricing before building the BOM.

    Args:
        query: search query e.g. "John Deere 7R 330 dealer price 2026"
        max_results: number of results to return (default 5, max 10)
    """
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        results = client.search(query=query, max_results=min(max_results, 10))
        items = []
        for r in results.get("results", []):
            items.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:600],
                "score": r.get("score", 0),
            })
        log.info(f"Tavily equipment search: '{query}' → {len(items)} results")
        return {"success": True, "results": items, "query": query}
    except Exception as e:
        log.error(f"Tavily equipment search error: {e}")
        return {"success": False, "error": str(e), "results": []}


@mcp.tool()
def tavily_search_compliance(country_code: str, equipment_category: str) -> dict:
    """
    Search for current regulatory and compliance requirements for agricultural
    equipment in a specific country. Used by the Compliance Critic Agent.

    Args:
        country_code: ISO country code e.g. US, AU, EU, MY, BR
        equipment_category: equipment type e.g. tractor, combine, sprayer
    """
    try:
        from tavily import TavilyClient
        query = f"{equipment_category} agricultural equipment compliance regulations certification {country_code} 2025 2026"
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        results = client.search(query=query, max_results=5)
        items = []
        for r in results.get("results", []):
            items.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:600],
            })
        log.info(f"Tavily compliance search: {country_code} {equipment_category} → {len(items)} results")
        return {"success": True, "results": items, "country": country_code, "category": equipment_category}
    except Exception as e:
        log.error(f"Tavily compliance search error: {e}")
        return {"success": False, "error": str(e), "results": []}


# ─────────────────────────────────────────────────────────────────────────────
# SERVER ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("AgriQuote MCP Server starting — 7 tools registered")
    mcp.run(transport="stdio")
