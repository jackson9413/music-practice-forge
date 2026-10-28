"""Assemble the full practice plan payload used by the API and the UI."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from .db import list_sessions
from .instruments import AREAS, AREA_LABELS, INSTRUMENT_BY_KEY, LEVELS, any_drills_for
from .planner import WEEK_THEMES, build_session, build_week
from .scoring import score_readiness
from .tempo import build_ladder, detect_plateaus, momentum


def _int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_plan(payload: dict) -> dict:
    instrument = (payload.get("instrument") or "piano").strip()
    if instrument not in INSTRUMENT_BY_KEY:
        instrument = "piano"

    level = (payload.get("level") or "intermediate").strip()
    if level not in LEVELS:
        level = "intermediate"

    minutes = max(10, min(240, _int(payload.get("minutes"), 45)))
    sessions_per_week = max(1, min(7, _int(payload.get("sessions_per_week"), 4)))
    piece = (payload.get("piece") or "").strip()
    focus_preset = (payload.get("focus_preset") or "balanced").strip()

    raw_spots = payload.get("weak_spots") or []
    if isinstance(raw_spots, str):
        raw_spots = [raw_spots]
    weak_spots = [s for s in raw_spots if s in AREAS]

    current_tempo = _int(payload.get("current_tempo"), 0)
    target_tempo = _int(payload.get("target_tempo"), 0)

    week = build_week(
        instrument=instrument,
        minutes=minutes,
        sessions_per_week=sessions_per_week,
        weak_spots=weak_spots,
        piece=piece,
        level=level,
        focus_preset=focus_preset,
    )

    today_theme = None
    if week.sessions:
        tkey = week.sessions[0].theme
        today_theme = next((t for t in WEEK_THEMES if t["key"] == tkey), None)

    session = build_session(
        instrument=instrument,
        minutes=minutes,
        weak_spots=weak_spots,
        piece=piece,
        level=level,
        focus_preset=focus_preset,
        theme=today_theme,
    )

    ladder_block = next((b for b in session.blocks if b.key == "ladder"), None)
    ladder_minutes_week = (ladder_block.minutes if ladder_block else 10) * sessions_per_week

    ladder = build_ladder(
        current=current_tempo,
        target=target_tempo,
        instrument=instrument,
        level=level,
        sessions_per_week=sessions_per_week,
        ladder_minutes_per_week=ladder_minutes_week,
        piece=piece,
    )

    entries = list_sessions(limit=300)
    mom = momentum(entries, week.weekly_minutes)
    plateaus = detect_plateaus(entries)

    score = score_readiness(session, week, ladder, mom, weak_spots, level)

    prof = INSTRUMENT_BY_KEY[instrument]
    drills = [
        {
            "id": d.id,
            "name": d.name,
            "area": AREA_LABELS.get(d.area, d.area),
            "minutes": d.minutes,
            "how": d.how,
        }
        for d in any_drills_for(instrument, level)
    ]

    return {
        "session": session.to_dict(),
        "week": {
            "sessions_per_week": week.sessions_per_week,
            "session_minutes": week.session_minutes,
            "weekly_minutes": week.weekly_minutes,
            "weekly_hours": week.weekly_hours,
            "sessions": [
                {
                    "day": s.day,
                    "day_index": s.day_index,
                    "theme": s.theme,
                    "theme_title": s.theme_title,
                    "minutes": s.minutes,
                    "focus_areas": [AREA_LABELS.get(a, a) for a in s.focus_areas],
                    "headline": s.headline,
                }
                for s in week.sessions
            ],
            "rest_days": week.rest_days,
            "flags": week.flags,
        },
        "ladder": ladder,
        "journal": {"momentum": mom, "plateaus": plateaus, "entries": entries[-12:]},
        "score": score,
        "instrument": {
            "key": prof.key,
            "label": prof.label,
            "family": prof.family,
            "summary": prof.summary,
            "focus_sections": list(prof.focus_sections),
        },
        "meta": {
            "minutes": minutes,
            "sessions_per_week": sessions_per_week,
            "piece": piece,
            "level": level,
            "focus_preset": focus_preset,
            "weak_spots": weak_spots,
            "current_tempo": current_tempo,
            "target_tempo": target_tempo,
        },
        "drills": drills,
    }
