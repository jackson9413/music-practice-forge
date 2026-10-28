"""Session-readiness scoring across five axes."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from .instruments import label_for_area
from .planner import WEAK_TO_BLOCKS, Session, WeekPlan

RECOMMENDED_WEEKLY = {
    "beginner": (120, 300),
    "intermediate": (240, 600),
    "advanced": (360, 900),
}

AXIS_WEIGHTS = {
    "pacing": 0.20,
    "goal_alignment": 0.25,
    "load_balance": 0.20,
    "tempo_feasibility": 0.20,
    "journal_momentum": 0.15,
}

AXIS_LABELS = {
    "pacing": "Pacing",
    "goal_alignment": "Goal alignment",
    "load_balance": "Load balance",
    "tempo_feasibility": "Tempo feasibility",
    "journal_momentum": "Journal momentum",
}


def _axis(key: str, value: float, reasons: List[str]) -> dict:
    value = max(0, min(100, int(round(value))))
    return {"key": key, "label": AXIS_LABELS[key], "score": value, "reasons": reasons}


def score_readiness(
    session: Session,
    week: WeekPlan,
    ladder: dict,
    momentum: dict,
    weak_spots: Sequence[str],
    level: str = "intermediate",
) -> dict:
    axes: List[dict] = []

    # --- pacing -------------------------------------------------------------
    reasons: List[str] = []
    total = sum(b.minutes for b in session.blocks)
    score = 0.0
    if total == session.total_minutes:
        score += 45
        reasons.append(f"Blocks add up to exactly {total} minutes.")
    else:
        score += 45 * (1 - min(1, abs(total - session.total_minutes) / max(1, session.total_minutes)))
        reasons.append(f"Blocks add up to {total} minutes but the budget is {session.total_minutes}.")
    longest = max((b.minutes for b in session.blocks), default=0)
    if longest <= session.total_minutes * 0.5:
        score += 25
        reasons.append("No single block eats more than half the session.")
    else:
        score += 10
        reasons.append(f"The longest block is {longest} minutes - over half the session.")
    if all(b.minutes >= 5 for b in session.blocks):
        score += 15
        reasons.append("Every block is long enough to actually enter a state.")
    else:
        reasons.append("At least one block is too short to be useful.")
    if all(b.stop_rule for b in session.blocks):
        score += 15
        reasons.append("Every block has a stop rule, so the session ends on quality instead of exhaustion.")
    axes.append(_axis("pacing", score, reasons))

    # --- goal alignment -----------------------------------------------------
    reasons = []
    weak = list(weak_spots)
    if not weak:
        axes.append(_axis("goal_alignment", 60, ["No weak spot selected - pick at least one so the session has a job."]))
    else:
        covered = set()
        for spot in weak:
            for block in WEAK_TO_BLOCKS.get(spot, []):
                covered.add(block)
        session_blocks = {b.key for b in session.blocks}
        hit = covered & session_blocks
        pct = len(hit) / float(len(covered)) if covered else 0.0
        score = 60 * pct
        reasons.append(
            "Session blocks address: " + (", ".join(sorted(hit)) if hit else "nothing you flagged") + "."
        )
        week_areas = set()
        for s in week.sessions:
            week_areas.update(s.focus_areas)
        missed = [w for w in weak if w not in week_areas]
        score += 40 * (1 - len(missed) / float(len(weak)))
        if missed:
            reasons.append("Not scheduled this week: " + ", ".join(label_for_area(m) for m in missed) + ".")
        else:
            reasons.append("Every weak spot you flagged is scheduled somewhere this week.")
    axes.append(_axis("goal_alignment", score, reasons))

    # --- load balance -------------------------------------------------------
    reasons = []
    lo, hi = RECOMMENDED_WEEKLY.get(level, RECOMMENDED_WEEKLY["intermediate"])
    weekly = week.weekly_minutes
    if lo <= weekly <= hi:
        score = 100.0
        reasons.append(f"{weekly} minutes a week sits inside the recommended band for a {level} ({lo}-{hi}).")
    elif weekly < lo:
        score = max(0.0, 100 - 120 * (lo - weekly) / float(lo))
        reasons.append(f"{weekly} minutes a week is below the recommended {lo} for a {level}.")
    else:
        score = max(0.0, 100 - 70 * (weekly - hi) / float(hi))
        reasons.append(f"{weekly} minutes a week is above the recommended {hi} for a {level}.")
    if len(week.rest_days) >= 1:
        score += 0.0
        reasons.append(f"Rest days: {', '.join(week.rest_days)}.")
    else:
        score -= 10
        reasons.append("No rest day is scheduled - recovery is where the adaptation happens.")
    axes.append(_axis("load_balance", score, reasons))

    # --- tempo feasibility --------------------------------------------------
    reasons = []
    status = ladder.get("status")
    weeks = ladder.get("weeks_estimate") or 0
    if status == "climb":
        if weeks <= 4:
            score = 100.0
        elif weeks <= 8:
            score = 92 - (weeks - 4) * 4
        elif weeks <= 16:
            score = 68 - (weeks - 8) * 2.5
        else:
            score = 30.0
        reasons.append(f"The ladder puts the target about {weeks} weeks away at this session rate.")
        if ladder.get("flags"):
            reasons.append(ladder["flags"][0])
    elif status == "hold":
        score = 85.0
        reasons.append("Target tempo is not above the current one - this week is about reliability.")
    else:
        score = 55.0
        reasons.append("No current tempo recorded, so the ladder cannot be sized yet.")
    axes.append(_axis("tempo_feasibility", score, reasons))

    # --- journal momentum ---------------------------------------------------
    reasons = []
    sessions_logged = momentum.get("sessions", 0)
    if sessions_logged == 0:
        score = 35.0
        reasons.append("No sessions logged yet, so there is no feedback loop to trust.")
    else:
        streak = momentum.get("streak_days", 0)
        score = 30 + min(35, streak * 6)
        reasons.append(f"{sessions_logged} sessions logged, {streak}-day streak.")
        recent_min = momentum.get("recent_minutes", 0)
        if week.weekly_minutes and recent_min:
            avg = recent_min / max(1, momentum.get("recent_sessions", 1))
            ratio = avg / float(max(1, week.session_minutes))
            score += min(20, int(ratio * 20))
            if ratio < 0.7:
                reasons.append(f"Recent sessions average {avg:.0f} minutes against a {week.session_minutes} minute plan.")
            else:
                reasons.append(f"Recent sessions average {avg:.0f} minutes - close to the plan.")
        trend = momentum.get("tempo_trend")
        if trend is not None:
            score += 15 if trend > 0 else (5 if trend == 0 else -10)
            reasons.append(f"Tempo trend across logged sessions: {trend:+} bpm per session.")
    axes.append(_axis("journal_momentum", score, reasons))

    overall = sum(a["score"] * AXIS_WEIGHTS[a["key"]] for a in axes)
    overall = int(round(overall))

    if overall >= 85:
        grade = "Ready to practise"
    elif overall >= 70:
        grade = "Solid plan"
    elif overall >= 55:
        grade = "Workable, with gaps"
    else:
        grade = "Needs reshaping"

    weakest = sorted(axes, key=lambda a: a["score"])[:2]
    next_actions: List[str] = []
    for a in weakest:
        if a["reasons"]:
            next_actions.append("{}: {}".format(a["label"], a["reasons"][-1]))

    return {
        "overall": overall,
        "grade": grade,
        "axes": axes,
        "next_actions": next_actions,
        "weights": AXIS_WEIGHTS,
    }
