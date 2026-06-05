import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from agropilot.agent_configuration.agent import QuoteState, build_graph


@dataclass
class PipelineRunResult:
    success: bool
    rfq_id: str
    started_at: str
    finished_at: str
    elapsed_s: int
    final_state: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def run_pipeline_from_rfq(rfq_email_text: str, max_debate_rounds: int = 3) -> PipelineRunResult:
    started = datetime.now()
    graph = build_graph()

    initial: QuoteState = {
        "rfq_email": rfq_email_text,
        "parsed_rfq": {},
        "bom": [],
        "compliance": {},
        "sentinel": {},
        "debate_round": 0,
        "max_debate_rounds": max_debate_rounds,
        "compliance_cleared": False,
        "final_quotation": "",
        "hitl": {},
        "log": [],
    }

    accumulated_state: Dict[str, Any] = dict(initial)

    try:
        for step in graph.stream(initial):
            node_name = list(step.keys())[0]
            node_state = step[node_name]
            for key, val in node_state.items():
                if key == "log":
                    accumulated_state["log"] = accumulated_state.get("log", []) + val
                else:
                    accumulated_state[key] = val

        finished = datetime.now()
        hitl = (accumulated_state.get("hitl") or {})
        parsed = (accumulated_state.get("parsed_rfq") or {})
        rfq_id = hitl.get("rfq_id") or parsed.get("rfq_id") or "RFQ-UNKNOWN"

        return PipelineRunResult(
            success=True,
            rfq_id=rfq_id,
            started_at=started.isoformat(timespec="seconds"),
            finished_at=finished.isoformat(timespec="seconds"),
            elapsed_s=int((finished - started).total_seconds()),
            final_state=accumulated_state,
        )
    except Exception as e:
        finished = datetime.now()
        return PipelineRunResult(
            success=False,
            rfq_id="RFQ-ERROR",
            started_at=started.isoformat(timespec="seconds"),
            finished_at=finished.isoformat(timespec="seconds"),
            elapsed_s=int((finished - started).total_seconds()),
            final_state=None,
            error=str(e),
        )


def save_run_result(
    result: PipelineRunResult,
    out_dir: str,
    *,
    email_meta: Optional[Dict[str, Any]] = None,
    rfq_source_id: Optional[str] = None,
) -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_id = (rfq_source_id or result.rfq_id or "rfq").replace("/", "_").replace(" ", "_")
    path = os.path.join(out_dir, f"{ts}__{safe_id}.json")

    payload: Dict[str, Any] = {
        "success": result.success,
        "rfq_id": result.rfq_id,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
        "elapsed_s": result.elapsed_s,
        "error": result.error,
        "email_meta": email_meta or {},
        "final_state": result.final_state,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path

