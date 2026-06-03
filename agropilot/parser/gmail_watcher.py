import argparse
import base64
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from agropilot.parser.pipeline_runner import run_pipeline_from_rfq, save_run_result


def _decode_b64url(data: str) -> str:
    if not data:
        return ""
    try:
        return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_text_from_payload(payload: Dict[str, Any]) -> str:
    # Direct body
    body = (payload.get("body") or {}).get("data")
    if body:
        return _decode_b64url(body)

    # Multipart walk (prefer plain text)
    best_plain = ""
    best_html = ""
    stack: List[Dict[str, Any]] = list(payload.get("parts") or [])
    while stack:
        p = stack.pop(0) or {}
        mime = (p.get("mimeType") or "").lower()
        bdata = ((p.get("body") or {}).get("data")) or ""
        if mime == "text/plain" and bdata and not best_plain:
            best_plain = _decode_b64url(bdata)
        elif mime == "text/html" and bdata and not best_html:
            best_html = _decode_b64url(bdata)
        stack.extend(p.get("parts") or [])

    if best_plain.strip():
        return best_plain
    if best_html.strip():
        # lightweight strip
        import re

        text = re.sub(r"<[^>]+>", " ", best_html)
        text = re.sub(r"\s+", " ", text).strip()
        return text
    return ""


def _load_state(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"seen_ids": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"seen_ids": []}


def _save_state(path: str, state: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _gmail_service(token_path: str) -> Any:
    scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
    creds = Credentials.from_authorized_user_file(token_path, scopes)
    return build("gmail", "v1", credentials=creds)


def fetch_latest_message_ids(service: Any, query: str, max_results: int) -> List[str]:
    resp = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    msgs = resp.get("messages") or []
    return [m["id"] for m in msgs if m.get("id")]


def fetch_message_full(service: Any, msg_id: str) -> Dict[str, Any]:
    return service.users().messages().get(userId="me", id=msg_id, format="full").execute()


def headers_map(msg: Dict[str, Any]) -> Dict[str, str]:
    headers = (msg.get("payload") or {}).get("headers") or []
    return {h.get("name", "").lower(): h.get("value", "") for h in headers}


def run_once(
    *,
    token_path: str,
    query: str,
    max_results: int,
    state_path: str,
    out_dir: str,
) -> int:
    service = _gmail_service(token_path)
    state = _load_state(state_path)
    seen = set(state.get("seen_ids") or [])

    ids = fetch_latest_message_ids(service, query=query, max_results=max_results)
    new_ids = [i for i in ids if i not in seen]
    if not new_ids:
        return 0

    processed = 0
    # process oldest-first to preserve order
    for msg_id in reversed(new_ids):
        msg = fetch_message_full(service, msg_id)
        hdr = headers_map(msg)
        payload = msg.get("payload") or {}
        body = _extract_text_from_payload(payload).strip()

        # Feed the parser the raw email body (same as manual paste flow).
        # Keep headers as metadata only to avoid confusing the parser.
        result = run_pipeline_from_rfq(body)
        save_run_result(
            result,
            out_dir=out_dir,
            email_meta={
                "gmail_message_id": msg_id,
                "from": hdr.get("from", ""),
                "subject": hdr.get("subject", ""),
                "date": hdr.get("date", ""),
                "query": query,
            },
            rfq_source_id=f"gmail_{msg_id}",
        )

        seen.add(msg_id)
        processed += 1

    state["seen_ids"] = list(seen)[-500:]  # cap growth
    _save_state(state_path, state)
    return processed


def main() -> None:
    ap = argparse.ArgumentParser(description="Poll Gmail inbox and auto-run AgriQuote pipeline.")
    ap.add_argument("--token", default=os.getenv("GMAIL_TOKEN_PATH", os.path.join(os.path.dirname(__file__), "token_gmail.json")))
    ap.add_argument("--query", default="in:inbox newer_than:7d")
    ap.add_argument("--interval", type=int, default=10, help="Poll interval in seconds")
    ap.add_argument("--max-results", type=int, default=5)
    ap.add_argument("--state-file", default=os.path.join(os.path.dirname(__file__), ".watcher_state.json"))
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(__file__), "auto_runs"))
    args = ap.parse_args()

    if not os.path.exists(args.token):
        raise SystemExit(f"Gmail token file not found: {args.token}")

    print(f"[gmail_watcher] token={args.token}")
    print(f"[gmail_watcher] query={args.query}")
    print(f"[gmail_watcher] interval={args.interval}s out_dir={args.out_dir}")

    while True:
        try:
            n = run_once(
                token_path=args.token,
                query=args.query,
                max_results=args.max_results,
                state_path=args.state_file,
                out_dir=args.out_dir,
            )
            if n:
                print(f"[{datetime.now().isoformat(timespec='seconds')}] processed {n} new email(s)")
        except Exception as e:
            print(f"[{datetime.now().isoformat(timespec='seconds')}] error: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()

