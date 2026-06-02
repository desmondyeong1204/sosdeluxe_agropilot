"""
app_patch.py — Drop-in patch for app.py
Wires the MCP agent into the HITL "APPROVE & SUBMIT" button.

HOW TO INTEGRATE:
1. Copy mcp_server.py and mcp_agent.py into your agropilot/ folder alongside agent.py
2. Add this import at the top of app.py:
     from mcp_agent import run_post_approval_agent
3. Replace the existing HITL approval button block in app.py with the one below.

Find this section in app.py:
    with col_a:
        if st.button("✅  APPROVE & SUBMIT CONFIGURATION", ...):
            st.session_state.approved = True
            st.rerun()

Replace with the block below (copy from the triple-quoted string).
"""

PATCH = """
    with col_a:
        if st.button("✅  APPROVE & SUBMIT CONFIGURATION", type="primary", use_container_width=True):
            with st.spinner("🤖 Agent dispatching downstream actions..."):
                # ── TRUE AGENTIC DISPATCH ─────────────────────────────────
                # The LLM agent dynamically decides tool order and handles gaps.
                # No hardcoded sequence — true ReAct loop.
                from mcp_agent import run_post_approval_agent
                dispatch_result = run_post_approval_agent(st.session_state.final_state)
                st.session_state.dispatch_result = dispatch_result
                # ─────────────────────────────────────────────────────────

            st.session_state.approved = True
            st.rerun()
"""

# ─────────────────────────────────────────────────────────────────────────────
# COMPLETION SCREEN PATCH
# Replace the completion screen in app.py with this version
# which shows real dispatch results instead of hardcoded badges.
# ─────────────────────────────────────────────────────────────────────────────

COMPLETION_SCREEN_PATCH = """
if st.session_state.get("approved") and st.session_state.final_state:
    fs      = st.session_state.final_state
    hitl    = fs.get("hitl", {})
    elapsed = st.session_state.elapsed
    parsed  = fs.get("parsed_rfq", {})
    audit   = fs.get("compliance", {})
    blocking = [o for o in audit.get("objections", []) if o.get("severity") == "BLOCKING"]
    dispatch = st.session_state.get("dispatch_result", {})

    raw_location = parsed.get('farm_location') or 'Story County, Iowa, USA'
    location_parts = raw_location.split(',')
    region_display = location_parts[-1].strip() if location_parts else raw_location
    curr_sym = parsed.get("currency_symbol", hitl.get("currency_symbol", "$"))

    # Build action badges dynamically from real dispatch results
    completed = dispatch.get("actions_completed", [])
    failed    = dispatch.get("actions_failed", [])

    ACTION_LABELS = {
        "salesforce_create_opportunity": "SALESFORCE CREATED",
        "docusign_send_envelope":        "DOCUSIGN SENT",
        "slack_notify_manager":          "SLACK NOTIFIED",
        "gmail_send_quote":              "QUOTE EMAILED",
    }

    badges_html = ""
    for action_key, label in ACTION_LABELS.items():
        if any(action_key in c for c in completed):
            badges_html += f'<div class="action-badge">✓ {label}</div>'
        elif any(action_key in f for f in failed):
            badges_html += f'<div class="action-badge" style="border-color:#f43f5e;color:#fda4af;">⚠ {label} (failed)</div>'
        else:
            badges_html += f'<div class="action-badge" style="opacity:0.4">— {label} (skipped)</div>'

    sf_url = dispatch.get("salesforce_url", "")
    sf_link = f'<a href="{sf_url}" target="_blank" style="color:#818cf8;font-size:12px;">View in Salesforce →</a>' if sf_url else ""

    st.markdown(f\"""
    <div class="completion-screen">
      <div class="completion-check">✓</div>
      <div class="completion-title">Quote Sent. Deal in Motion.</div>
      <div class="completion-sub">
        Total elapsed agent time: <span class="green">{fmt_time(elapsed)}</span>
        &nbsp;|&nbsp; Manual equivalent: <span class="red">9 days</span>
      </div>
      <div class="completion-actions">{badges_html}</div>
      {sf_link}
      <div class="completion-stats">
        <div class="stat">
          <div class="stat-label">Client Region</div>
          <div class="stat-value green">{region_display}</div>
        </div>
        <div class="stat">
          <div class="stat-label">Errors Caught</div>
          <div class="stat-value yellow">{len(blocking)} Resolved</div>
        </div>
        <div class="stat">
          <div class="stat-label">Total Value Secured</div>
          <div class="stat-value white">{curr_sym}{hitl.get('quote_total',0):,.0f}</div>
        </div>
      </div>
    </div>
    \""", unsafe_allow_html=True)

    if dispatch.get("summary"):
        st.markdown(
            f"<div style='font-size:13px;color:#64748b;text-align:center;margin-top:-16px;padding-bottom:16px;'>"
            f"Agent: {dispatch['summary']}</div>",
            unsafe_allow_html=True
        )

    if st.button("↺  RUN AGAIN", key="run_again"):
        for k in ["approved","pipeline_done","final_state","elapsed","all_logs","dispatch_result"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()
    st.stop()
"""

if __name__ == "__main__":
    print("app_patch.py — integration instructions:")
    print("=" * 60)
    print(PATCH)
    print("=" * 60)
    print("See docstring at top of file for full instructions.")
