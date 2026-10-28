"""Turn a musician's situation into a concrete practice session and a week of sessions."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence

from .instruments import (
    INSTRUMENT_BY_KEY,
    LEVELS,
    drills_for,
    any_drills_for,
    label_for_area,
)

# Base weight of each block in a standard session.
BASE_WEIGHTS: Dict[str, float] = {
    "warmup": 0.14,
    "slow": 0.18,
    "ladder": 0.22,
    "repertoire": 0.22,
    "reading": 0.16,
    "log": 0.08,
}

BLOCK_TITLES: Dict[str, str] = {
    "warmup": "Warm-up & technique",
    "slow": "Slow & isolated work",
    "ladder": "Tempo ladder / metronome",
    "repertoire": "Repertoire",
    "reading": "Reading & ear",
    "log": "Cooldown & log",
}

BLOCK_WHY: Dict[str, str] = {
    "warmup": "Loose the hands before you ask them for accuracy - 10 minutes here saves 20 later.",
    "slow": "Slow work is where the actual learning happens; the fast version is just the reward.",
    "ladder": "Raising tempo by steps is the only reliable way to make it stick.",
    "repertoire": "Connect the material you have drilled into something you can actually play.",
    "reading": "Unfamiliar material keeps the reading system alive and independent of the piece.",
    "log": "Two minutes of writing decides what the next session does better.",
}

STOP_RULES: Dict[str, str] = {
    "warmup": "Stop when the sound stops improving, not when the clock says stop - usually 2-3 minutes after it feels easy.",
    "slow": "Stop the moment you can play it three times clean. The first collapse is the signal to stop.",
    "ladder": "Stop after two consecutive failed reps at the same rung. Log the rung, do not push through it.",
    "repertoire": "Play it clean once before the point of collapse. One clean run beats five broken ones.",
    "reading": "Stop at the clock even mid-piece. Unfinished is fine; guessing is not.",
    "log": "Write the single next action before you put the instrument down.",
}

# Which weak spot pushes which block.
WEAK_TO_BLOCKS: Dict[str, List[str]] = {
    "technique": ["warmup", "slow"],
    "rhythm": ["ladder"],
    "intonation": ["slow"],
    "articulation": ["slow", "repertoire"],
    "dynamics": ["repertoire"],
    "tempo": ["ladder"],
    "sight-reading": ["reading"],
    "ear": ["reading"],
    "memory": ["repertoire", "log"],
    "stamina": ["slow", "repertoire"],
}

FOCUS_PRESETS: Dict[str, Dict[str, float]] = {
    "balanced": dict(BASE_WEIGHTS),
    "technique": {"warmup": 0.24, "slow": 0.30, "ladder": 0.16, "repertoire": 0.14, "reading": 0.10, "log": 0.06},
    "repertoire": {"warmup": 0.10, "slow": 0.12, "ladder": 0.26, "repertoire": 0.40, "reading": 0.06, "log": 0.06},
    "exam": {"warmup": 0.14, "slow": 0.16, "ladder": 0.34, "repertoire": 0.26, "reading": 0.04, "log": 0.06},
}

WEEK_THEMES = [
    {"key": "technique", "title": "Technique & control",
     "areas": ["technique", "intonation", "articulation"], "boost": ["warmup", "slow"]},
    {"key": "ladder", "title": "Tempo ladder",
     "areas": ["rhythm", "tempo"], "boost": ["ladder"]},
    {"key": "repertoire", "title": "Repertoire polish",
     "areas": ["dynamics", "memory", "articulation"], "boost": ["repertoire"]},
    {"key": "reading", "title": "Reading & ear",
     "areas": ["sight-reading", "ear"], "boost": ["reading"]},
    {"key": "performance", "title": "Performance run-through",
     "areas": ["tempo", "dynamics", "stamina"], "boost": ["repertoire", "ladder"]},
]

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@dataclass
class DrillRef:
    id: str
    name: str
    how: str
    area: str


@dataclass
class Block:
    key: str
    title: str
    area: str
    minutes: int
    why: str
    stop_rule: str
    drills: List[DrillRef] = field(default_factory=list)


@dataclass
class Session:
    theme: str
    theme_title: str
    total_minutes: int
    blocks: List[Block]
    focus_areas: List[str]
    focus_notes: List[str]
    plan_notes: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WeekSession:
    day: str
    day_index: int
    theme: str
    theme_title: str
    minutes: int
    focus_areas: List[str]
    headline: str


@dataclass
class WeekPlan:
    sessions_per_week: int
    session_minutes: int
    weekly_minutes: int
    weekly_hours: float
    sessions: List[WeekSession]
    rest_days: List[str]
    flags: List[str]


def _round5(value: float) -> int:
    return max(0, int(round(value / 5.0)) * 5)


def allocate(weights: Dict[str, float], budget: int, minimum: int = 5, step: int = 5) -> Dict[str, int]:
    """Split a minute budget across blocks.

    Blocks are sized in whole steps (5 minutes by default) and the allocation is
    steered by how far each block sits from its ideal share, so a block never
    loses time to another block that is still under its share.
    """
    keys = list(weights.keys())
    unit = max(1, step)
    total_units = budget // unit
    remainder = budget - total_units * unit
    min_units = max(1, minimum // unit)
    total_w = sum(weights[k] for k in keys) or 1.0

    while len(keys) > 1 and len(keys) * min_units > total_units:
        drop = min(keys, key=lambda k: weights[k])
        keys.remove(drop)

    ideal = {k: total_units * weights[k] / total_w for k in keys}
    units = {k: max(min_units, int(round(ideal[k]))) for k in keys}

    guard = 0
    while sum(units.values()) != total_units and guard < 500:
        guard += 1
        current = sum(units.values())
        if current > total_units:
            cands = [k for k in keys if units[k] - 1 >= min_units]
            if not cands:
                break
            k = max(cands, key=lambda k: (units[k] - ideal[k], weights[k]))
            units[k] -= 1
        else:
            k = max(keys, key=lambda k: (ideal[k] - units[k], weights[k]))
            units[k] += 1

    alloc = {k: units[k] * unit for k in keys}
    if remainder and keys:
        top = max(keys, key=lambda k: weights[k])
        alloc[top] += remainder
    return alloc


def _block_keys(budget: int) -> List[str]:
    keys = list(BASE_WEIGHTS.keys())
    if budget < 40:
        keys.remove("reading")
    if budget < 30:
        keys.remove("log")
    if budget < 25:
        keys.remove("slow")
    return keys


def pick_drills(instrument: str, level: str, areas: Sequence[str], limit: int = 2,
                used: Optional[set] = None) -> List[DrillRef]:
    used = used if used is not None else set()
    out: List[DrillRef] = []
    seen = set()
    for area in areas:
        for d in drills_for(instrument, area, level):
            if d.id in seen or d.id in used:
                continue
            seen.add(d.id)
            out.append(DrillRef(d.id, d.name, d.how, label_for_area(d.area)))
            if len(out) >= limit:
                return out
    if not out:
        for d in any_drills_for(instrument, level):
            if d.id in used or d.id in seen:
                continue
            seen.add(d.id)
            out.append(DrillRef(d.id, d.name, d.how, label_for_area(d.area)))
            if len(out) >= limit:
                break
    return out


def _weak_area_weight(weak_spots: List[str]) -> Dict[str, float]:
    boosts: Dict[str, float] = {}
    for spot in weak_spots:
        for block in WEAK_TO_BLOCKS.get(spot, []):
            boosts[block] = boosts.get(block, 0.0) + 0.11
    return boosts


def build_session(
    instrument: str,
    minutes: int,
    weak_spots: List[str],
    piece: str = "",
    level: str = "intermediate",
    focus_preset: str = "balanced",
    theme: Optional[dict] = None,
    tempo_info: Optional[dict] = None,
) -> Session:
    """Build one practice session that adds up to exactly `minutes`."""
    minutes = max(10, int(minutes))
    prof = INSTRUMENT_BY_KEY.get(instrument)
    weights = dict(FOCUS_PRESETS.get(focus_preset, BASE_WEIGHTS))
    for block, bump in _weak_area_weight(weak_spots).items():
        weights[block] = weights.get(block, 0.0) + bump
    if theme:
        for block in theme.get("boost", []):
            weights[block] = weights.get(block, 0.0) + 0.12

    keys = _block_keys(minutes)
    weights = {k: weights[k] for k in keys if k in weights}
    alloc = allocate(weights, minutes)

    primary_slow_area = next((s for s in weak_spots if s in ("intonation", "articulation", "technique")), "technique")
    piece_name = piece.strip() or "the current piece"

    blocks: List[Block] = []
    used_drills: set = set()
    for key in keys:
        mins = alloc.get(key, 0)
        if mins <= 0:
            continue
        if key == "warmup":
            areas = ["technique", "warmup"]
            area_label = "Technique"
        elif key == "slow":
            areas = [primary_slow_area, "technique"]
            area_label = label_for_area(primary_slow_area)
        elif key == "ladder":
            areas = ["rhythm", "tempo"]
            area_label = "Tempo"
        elif key == "repertoire":
            areas = ["dynamics", "memory", "articulation"]
            area_label = "Repertoire"
        elif key == "reading":
            areas = ["sight-reading", "ear"]
            area_label = "Reading"
        else:
            areas = ["memory", "technique"]
            area_label = "Log"

        drills = pick_drills(instrument, level, areas, limit=2 if key != "log" else 1,
                          used=used_drills)
        used_drills.update(d.id for d in drills)
        blocks.append(
            Block(
                key=key,
                title=BLOCK_TITLES[key],
                area=area_label,
                minutes=mins,
                why=BLOCK_WHY[key],
                stop_rule=STOP_RULES[key],
                drills=drills,
            )
        )

    focus_areas = list(weak_spots)
    focus_notes: List[str] = []
    if prof:
        if prof.focus_sections:
            focus_notes.append(
                "Watch " + prof.focus_sections[0] + " specifically today - it drifts before the others do."
            )
    if tempo_info and tempo_info.get("current_tempo"):
        focus_notes.append(
            f"Ladder block starts at {tempo_info['current_tempo']} bpm and stops at "
            f"{tempo_info.get('session_target', tempo_info['current_tempo'])} bpm."
        )
    if not weak_spots:
        focus_notes.append("No weak spot selected - this is a maintenance session, keep it light.")

    plan_notes: List[str] = []
    plan_notes.append(f"Total is exactly {sum(b.minutes for b in blocks)} minutes; the blocks are sized to fit the clock.")
    hardest = max(blocks, key=lambda b: b.minutes) if blocks else None
    if hardest and hardest.minutes > minutes * 0.45:
        plan_notes.append(
            f"'{hardest.title}' takes {hardest.minutes} minutes - over half the session. Split it if attention drops."
        )
    if minutes >= 90:
        plan_notes.append("Long session: take a real 5-minute break between blocks, not a scrolling break.")
    elif minutes <= 20:
        plan_notes.append("Short session: one drill per block, no multitasking, phone in another room.")
    if piece.strip():
        plan_notes.append(f"Repertoire block is scoped to '{piece.strip()}' only - pick one passage, not the whole piece.")

    return Session(
        theme=theme["key"] if theme else "balanced",
        theme_title=theme["title"] if theme else "Balanced session",
        total_minutes=minutes,
        blocks=blocks,
        focus_areas=focus_areas,
        focus_notes=focus_notes,
        plan_notes=plan_notes,
    )


def build_week(
    instrument: str,
    minutes: int,
    sessions_per_week: int,
    weak_spots: List[str],
    piece: str = "",
    level: str = "intermediate",
    focus_preset: str = "balanced",
) -> WeekPlan:
    """Lay sessions across the week so every weak spot gets covered."""
    sessions_per_week = max(1, min(7, int(sessions_per_week)))
    minutes = max(10, int(minutes))
    weekly_minutes = minutes * sessions_per_week

    # Spread session days across the week, keeping one longer gap for recovery.
    if sessions_per_week >= 6:
        days = [0, 1, 2, 3, 4, 5]
    elif sessions_per_week == 5:
        days = [0, 1, 2, 3, 4]
    elif sessions_per_week == 4:
        days = [0, 1, 3, 4]
    elif sessions_per_week == 3:
        days = [0, 2, 4]
    elif sessions_per_week == 2:
        days = [1, 4]
    else:
        days = [2]

    ordered_weak = weak_spots or ["technique"]
    sessions: List[WeekSession] = []
    used_areas: set = set()

    for i, day_idx in enumerate(days):
        theme = WEEK_THEMES[i % len(WEEK_THEMES)]
        theme_areas = [a for a in theme["areas"] if a in ordered_weak]
        if not theme_areas:
            # Rotate through weak spots so nothing goes a full week untouched.
            theme_areas = [ordered_weak[i % len(ordered_weak)]]
            title = f"{theme['title']} ({label_for_area(theme_areas[0])})"
        else:
            title = theme["title"]
        used_areas.update(theme_areas)

        session = build_session(
            instrument=instrument,
            minutes=minutes,
            weak_spots=theme_areas,
            piece=piece,
            level=level,
            focus_preset=focus_preset,
            theme=theme,
        )
        headline = session.blocks[0].title if session.blocks else "Practice"
        if len(session.blocks) > 1:
            headline += " + " + session.blocks[-1].title.lower()
        sessions.append(
            WeekSession(
                day=DAY_NAMES[day_idx],
                day_index=day_idx,
                theme=theme["key"],
                theme_title=title,
                minutes=minutes,
                focus_areas=theme_areas,
                headline=headline,
            )
        )

    missed = [a for a in ordered_weak if a not in used_areas]
    rest_days = [DAY_NAMES[d] for d in range(7) if d not in days]

    flags: List[str] = []
    if weekly_minutes > 1200:
        flags.append(
            f"{weekly_minutes / 60:.0f} h/week is a lot. Most gains come from 5-6 focused hours; check for burnout."
        )
    if minutes > 180:
        flags.append(f"{minutes} minutes in one sitting is past the point of diminishing returns. Consider two shorter blocks.")
    if sessions_per_week <= 2 and weekly_minutes < 180:
        flags.append("Under three hours a week, progress on new repertoire will stall. Add a third short session.")
    if len(rest_days) == 1:
        flags.append("Only one rest day this week - muscles and attention both need a day with no instrument.")
    if missed:
        flags.append(
            "Not covered this week: " + ", ".join(label_for_area(m) for m in missed) +
            ". Add a short session or accept the gap on purpose."
        )

    return WeekPlan(
        sessions_per_week=sessions_per_week,
        session_minutes=minutes,
        weekly_minutes=weekly_minutes,
        weekly_hours=round(weekly_minutes / 60.0, 1),
        sessions=sessions,
        rest_days=rest_days,
        flags=flags,
    )
