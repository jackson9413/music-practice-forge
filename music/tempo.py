"""Tempo ladders, plateau detection and momentum analysis."""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

from .instruments import INSTRUMENT_BY_KEY

INTERVENTIONS = [
    "Play the stuck passage at 90% of the tempo for two minutes, then 95%. Stop when it is clean twice.",
    "Loop only the bar where it breaks - 8 repetitions, no metronome, no full run.",
    "Drop to 80% and rebuild in 1 bpm steps. Slower than feels reasonable is the point.",
    "Play along with a reference recording, record yourself, and compare the two takes bar by bar.",
    "Change the variable: play the rhythm with no notes first, then add notes at the same tempo.",
    "Audit the setup - tuning, posture, hand position, instrument setup. Mechanical faults look like tempo faults.",
    "Take a full day off and come back at 80%. Fatigue mimics a plateau.",
]

CLICK_PATTERNS = [
    ("Click every beat, accent the first"),
    ("Click every beat, accent the first and the third"),
    ("Click eighth notes, accent the first of each bar"),
    ("Click eighth notes with a backbeat accent - hardest useful pattern"),
]


def _click_for(bpm: int) -> str:
    if bpm < 70:
        return CLICK_PATTERNS[0]
    if bpm < 100:
        return CLICK_PATTERNS[1]
    if bpm < 140:
        return CLICK_PATTERNS[2]
    return CLICK_PATTERNS[3]


def build_ladder(
    current: int,
    target: int,
    instrument: str = "piano",
    level: str = "intermediate",
    sessions_per_week: int = 4,
    ladder_minutes_per_week: int = 45,
    piece: str = "",
) -> dict:
    """Build a rung-by-rung tempo ladder between the current and target tempo."""
    prof = INSTRUMENT_BY_KEY.get(instrument)
    cap = prof.tempo_step_cap if prof else 5
    current = max(20, int(current or 0))
    target = max(20, int(target or 0))
    sessions_per_week = max(1, int(sessions_per_week or 1))
    ladder_minutes_per_week = max(10, int(ladder_minutes_per_week or 10))
    piece_name = piece.strip() or "the piece"

    flags: List[str] = []
    rungs: List[dict] = []

    if current == 0:
        return {
            "status": "unknown",
            "current_tempo": current,
            "target_tempo": target,
            "rungs": [],
            "flags": ["No current tempo given - play the piece once and note the tempo you can hold cleanly."],
            "weeks_estimate": 0,
            "step_size": 0,
        }

    if target <= current:
        return {
            "status": "hold",
            "current_tempo": current,
            "target_tempo": target,
            "rungs": [
                {
                    "index": 1,
                    "bpm": current,
                    "delta": 0,
                    "minutes": max(5, _round5(ladder_minutes_per_week / 3)),
                    "click": _click_for(current),
                    "instruction": f"Hold {current} bpm for a week and make it boring. Consistency before speed.",
                    "week": 1,
                }
            ],
            "flags": [
                f"Target is not above the current tempo. Spend this week making {current} bpm reliable, then set a new target."
            ],
            "weeks_estimate": 1,
            "step_size": 0,
        }

    step = max(2, min(cap, int(round(current * 0.05)) or 2))
    span = target - current
    step_capped = False
    if math.ceil(span / step) > 12:
        step = int(math.ceil(span / 12))
        step_capped = True
    step = max(2, step)

    bpm_list = []
    b = current
    while b < target:
        bpm_list.append(b)
        b += step
    bpm_list.append(target)

    max_new_per_week = 3
    per_rung_minutes = max(5, _round5(ladder_minutes_per_week / max_new_per_week))
    weeks_needed = int(math.ceil(len(bpm_list) / max_new_per_week))

    for i, bpm in enumerate(bpm_list):
        week = i // max_new_per_week + 1
        if bpm == target:
            instruction = (
                f"Target rung: play {piece_name} at {bpm} bpm, full run, record it once and listen back."
            )
        else:
            instruction = (
                f"Rung {i + 1}: play the hard bars at {bpm} bpm, three clean reps, then one recorded take. "
                f"Only move up when the take is clean."
            )
        rungs.append(
            {
                "index": i + 1,
                "bpm": bpm,
                "delta": bpm - current,
                "minutes": per_rung_minutes,
                "click": _click_for(bpm),
                "instruction": instruction,
                "week": week,
            }
        )

    # Two touches per rung (reach it, then confirm it) divided by sessions per week.
    raw_weeks = (len(bpm_list) * 2) / float(sessions_per_week)
    weeks_estimate = max(1, int(math.ceil(raw_weeks * 1.25)))

    if weeks_estimate > 16:
        flags.append(
            f"At {sessions_per_week} sessions a week this target is about {weeks_estimate} weeks away. "
            "Either lower the target or plan for a longer project."
        )
    if len(bpm_list) <= 3:
        flags.append("Very short ladder - you are close. Keep the steps small anyway so each one is clean.")
    if level == "beginner" and span > 40:
        flags.append("A beginner aiming more than 40 bpm above current usually plateaus. Split the gap.")
    if step >= cap and span > 20:
        flags.append(f"A {step} bpm step is at the top of what this instrument tolerates; expect a plateau at the end.")
    if step_capped:
        flags.append(
            f"The gap is too wide for {cap} bpm steps, so the ladder uses {step} bpm jumps. Expect more repetitions per rung."
        )

    return {
        "status": "climb",
        "current_tempo": current,
        "target_tempo": target,
        "step_size": step,
        "rungs": rungs,
        "flags": flags,
        "weeks_estimate": weeks_estimate,
        "weeks_needed": weeks_needed,
        "per_rung_minutes": per_rung_minutes,
    }


def _round5(value: float) -> int:
    return max(0, int(round(value / 5.0)) * 5)


def detect_plateaus(entries: Sequence[dict]) -> List[dict]:
    """Find pieces where the tempo has stopped moving."""
    by_piece: Dict[str, List[dict]] = {}
    for e in entries:
        piece = (e.get("piece") or "Untitled").strip() or "Untitled"
        by_piece.setdefault(piece, []).append(e)

    out: List[dict] = []
    for piece, items in by_piece.items():
        items = sorted(items, key=lambda e: (str(e.get("session_date") or ""), e.get("id") or 0))
        if len(items) < 3:
            continue
        last2 = items[-2:]
        earlier = items[:-2]
        best_recent = max((e.get("tempo") or 0) for e in last2)
        best_earlier = max((e.get("tempo") or 0) for e in earlier) if earlier else best_recent
        if best_recent <= best_earlier:
            out.append(
                {
                    "piece": piece,
                    "attempts": len(items),
                    "stuck_tempo": best_recent,
                    "flat_sessions": len(last2),
                    "suggestions": INTERVENTIONS[:4],
                }
            )
    return out


def momentum(entries: Sequence[dict], plan_weekly_minutes: int = 0) -> dict:
    """Summarise logged practice: volume, streak and tempo trend."""
    if not entries:
        return {
            "sessions": 0,
            "minutes": 0,
            "streak_days": 0,
            "recent_sessions": 0,
            "recent_minutes": 0,
            "tempo_trend": None,
            "coverage_pct": 0,
            "notes": ["No sessions logged yet. The journal is what turns this app from a planner into feedback."],
        }

    entries = sorted(entries, key=lambda e: (str(e.get("session_date") or ""), e.get("id") or 0))
    minutes = sum(int(e.get("minutes") or 0) for e in entries)
    dates = sorted({str(e.get("session_date"))[:10] for e in entries if e.get("session_date")})

    streak = 0
    if dates:
        from datetime import date, timedelta

        try:
            last = date.fromisoformat(dates[-1])
        except ValueError:
            last = None
        if last:
            today = date.today()
            gap = (today - last).days
            if gap <= 1:
                streak = 1
                probe = last - timedelta(days=1)
                while any(d == probe.isoformat() for d in dates):
                    streak += 1
                    probe -= timedelta(days=1)

    recent = entries[-10:]
    recent_minutes = sum(int(e.get("minutes") or 0) for e in recent)

    gains: List[int] = []
    for i in range(1, len(entries)):
        prev = entries[i - 1].get("tempo") or 0
        cur = entries[i].get("tempo") or 0
        if prev and cur:
            gains.append(cur - prev)
    positive = [g for g in gains if g > 0]
    tempo_trend = round(sum(gains) / len(gains), 1) if gains else None

    notes: List[str] = []
    coverage = 0
    if plan_weekly_minutes:
        from datetime import date, timedelta

        try:
            latest = date.fromisoformat(dates[-1])
        except ValueError:
            latest = None
        if latest:
            week_start = latest - timedelta(days=6)
            last_week = 0
            for e in entries:
                try:
                    d = date.fromisoformat(str(e.get("session_date"))[:10])
                except ValueError:
                    continue
                if d >= week_start:
                    last_week += int(e.get("minutes") or 0)
            coverage = min(150, int(round(100.0 * last_week / float(plan_weekly_minutes))))
        notes.append(f"Last {len(recent)} sessions averaged {recent_minutes / max(1, len(recent)):.0f} minutes.")
    if streak >= 5:
        notes.append(f"{streak}-day logging streak. That is the difference between practising and hoping.")
    elif streak == 0:
        notes.append("No session logged in the last day or two - the plan is only as good as the next repetition.")
    if positive:
        notes.append(f"{len(positive)} of your last {len(gains)} logged sessions improved the tempo.")
    elif gains:
        notes.append("Your last few sessions did not move the tempo. Read the plateau suggestions before adding volume.")

    return {
        "sessions": len(entries),
        "minutes": minutes,
        "hours": round(minutes / 60.0, 1),
        "streak_days": streak,
        "recent_sessions": len(recent),
        "recent_minutes": recent_minutes,
        "tempo_trend": tempo_trend,
        "coverage_pct": coverage if plan_weekly_minutes else 0,
        "notes": notes,
    }
