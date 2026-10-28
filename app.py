"""music-practice-forge - a local-first deliberate practice planner for musicians."""

from __future__ import annotations

import os
import sys
from typing import Any, Dict

from flask import Flask, jsonify, request, render_template

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from music.db import add_session, delete_session, init_db, list_sessions, pieces
from music.engine import build_plan
from music.instruments import AREA_LABELS, AREAS, DRILLS, INSTRUMENTS, LEVELS
from music.tempo import detect_plateaus, momentum

app = Flask(__name__)
init_db()


@app.route("/")
def index():
    return render_template(
        "index.html",
        instruments=[{"key": i.key, "label": i.label, "family": i.family, "summary": i.summary} for i in INSTRUMENTS],
        areas=[{"key": a, "label": AREA_LABELS.get(a, a)} for a in AREAS],
        levels=LEVELS,
    )


@app.route("/api/plan", methods=["POST"])
def api_plan():
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(build_plan(payload))
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"error": str(exc)}), 400


@app.route("/api/instruments")
def api_instruments():
    return jsonify(
        {
            "instruments": [
                {"key": i.key, "label": i.label, "family": i.family, "summary": i.summary,
                 "focus_sections": list(i.focus_sections)}
                for i in INSTRUMENTS
            ],
            "areas": [{"key": a, "label": AREA_LABELS.get(a, a)} for a in AREAS],
            "drills": [
                {"id": d.id, "name": d.name, "area": AREA_LABELS.get(d.area, d.area),
                 "minutes": d.minutes, "how": d.how,
                 "instruments": list(d.instruments), "level_min": d.level_min}
                for d in DRILLS
            ],
        }
    )


@app.route("/api/sessions", methods=["GET"])
def api_sessions():
    entries = list_sessions(limit=300)
    return jsonify(
        {
            "sessions": entries,
            "pieces": pieces(),
            "momentum": momentum(entries),
            "plateaus": detect_plateaus(entries),
        }
    )


@app.route("/api/sessions", methods=["POST"])
def api_add_session():
    data = request.get_json(silent=True) or {}
    try:
        row = add_session(
            session_date=(data.get("session_date") or "").strip(),
            piece=(data.get("piece") or "").strip(),
            instrument=(data.get("instrument") or "").strip(),
            area=(data.get("area") or "").strip(),
            tempo=data.get("tempo"),
            minutes=int(data.get("minutes") or 0),
            quality=int(data.get("quality") or 3),
            notes=(data.get("notes") or "").strip(),
        )
    except Exception as exc:  # pragma: no cover
        return jsonify({"error": str(exc)}), 400
    entries = list_sessions(limit=300)
    return jsonify({"session": row, "sessions": entries, "momentum": momentum(entries),
                    "plateaus": detect_plateaus(entries)})


@app.route("/api/sessions/<int:session_id>", methods=["DELETE"])
def api_delete_session(session_id: int):
    ok = delete_session(session_id)
    entries = list_sessions(limit=300)
    return jsonify({"deleted": ok, "sessions": entries, "momentum": momentum(entries),
                    "plateaus": detect_plateaus(entries)})


@app.route("/api/export/sheet.md", methods=["POST"])
def api_export():
    """Render a printable practice sheet as markdown."""
    payload = request.get_json(silent=True) or {}
    plan = build_plan(payload)
    session = plan["session"]
    meta = plan["meta"]
    lines = []
    lines.append(f"# Practice sheet - {meta['piece'] or 'general practice'}")
    lines.append("")
    lines.append(f"**Instrument:** {plan['instrument']['label']}  |  **Level:** {meta['level']}  |  "
                 f"**Total:** {session['total_minutes']} min")
    if meta["weak_spots"]:
        lines.append(f"**Focus:** {', '.join(AREA_LABELS.get(a, a) for a in meta['weak_spots'])}")
    lines.append("")
    lines.append(f"## {session['theme_title']}")
    lines.append("")
    for b in session["blocks"]:
        lines.append(f"### {b['title']} ({b['minutes']} min) - {b['area']}")
        lines.append(f"_{b['why']}_")
        lines.append("")
        for d in b["drills"]:
            lines.append(f"- **{d['name']}** - {d['how']}")
        lines.append(f"- Stop rule: {b['stop_rule']}")
        lines.append("")
    ladder = plan["ladder"]
    if ladder.get("rungs"):
        lines.append("## Tempo ladder")
        lines.append("")
        lines.append("| # | bpm | week | minutes | click |")
        lines.append("|---|-----|------|---------|-------|")
        for r in ladder["rungs"]:
            lines.append(f"| {r['index']} | {r['bpm']} | {r['week']} | {r['minutes']} | {r['click']} |")
        lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- ")
    return "\n".join(lines), 200, {"Content-Type": "text/markdown; charset=utf-8"}


@app.route("/healthz")
def healthz():
    return jsonify({"ok": True, "service": "music-practice-forge"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5017"))
    app.run(host="127.0.0.1", port=port, debug=False)
