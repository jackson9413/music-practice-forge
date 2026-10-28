"""Instrument profiles and the drill bank used to build practice sessions.

Everything here is plain data so the planner stays deterministic and testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# Weak-spot areas a musician can select. Order matters: it drives UI ordering.
AREAS: List[str] = [
    "technique",
    "rhythm",
    "intonation",
    "articulation",
    "dynamics",
    "tempo",
    "sight-reading",
    "ear",
    "memory",
    "stamina",
]

AREA_LABELS: Dict[str, str] = {
    "technique": "Technique",
    "rhythm": "Rhythm",
    "intonation": "Intonation",
    "articulation": "Articulation",
    "dynamics": "Dynamics",
    "tempo": "Tempo",
    "sight-reading": "Sight-reading",
    "ear": "Ear training",
    "memory": "Memorisation",
    "stamina": "Stamina / endurance",
}

LEVELS: List[str] = ["beginner", "intermediate", "advanced"]


@dataclass(frozen=True)
class Drill:
    """A single named practice activity."""

    id: str
    name: str
    area: str
    minutes: int
    how: str
    instruments: Tuple[str, ...] = ()
    families: Tuple[str, ...] = ()
    level_min: int = 1  # 1 beginner, 2 intermediate, 3 advanced


@dataclass(frozen=True)
class Instrument:
    key: str
    label: str
    family: str
    summary: str
    focus_sections: Tuple[str, ...] = ()
    tempo_step_cap: int = 6      # max bpm added per rung at intermediate level
    metronome_click: str = "4/4, accent on beat 1"
    default_goals: Tuple[str, ...] = ()


DRILLS: List[Drill] = [
    # ---------------- universal ----------------
    Drill("metronome-pulse", "Metronome pulse ladder", "rhythm", 10,
          "Start at 60 bpm, subdivide in eighths, add a click on the off-beat for the last minute.",
          level_min=1),
    Drill("chunk-loop", "Chunked repetition loop", "technique", 10,
          "Isolate the single hardest 2-bar chunk; play it 8 times slowly, no edits in between.",
          level_min=1),
    Drill("slow-isolated", "Slow-tempo isolation", "technique", 12,
          "Play the passage at 60-70% tempo with exaggerated motion, then add the tempo back.",
          level_min=1),
    Drill("timed-reading", "Timed sight-reading", "sight-reading", 10,
          "Read fresh material with a metronome at 70 bpm; never stop to fix a mistake, keep going.",
          level_min=1),
    Drill("ear-intervals", "Interval recognition", "ear", 8,
          "Sing or name 20 random intervals played by a reference track; log the misses.",
          level_min=1),
    Drill("scale-patterns", "Scale and pattern technique", "technique", 12,
          "Long-tone scales with a metronome; add accents, then thirds, then sixths.",
          level_min=1),
    Drill("long-tone", "Long-tone control", "stamina", 8,
          "Hold a steady note for 8 counts; watch the pulse drift and correct before it builds.",
          level_min=1),
    Drill("record-compare", "Record and compare", "memory", 8,
          "Record one clean take, play it back, and write the single biggest gap to fix.",
          level_min=1),
    Drill("improv-free", "Free improv over a groove", "ear", 8,
          "Improvise 8 minutes over a drone or loop using only one scale.",
          level_min=2),
    Drill("articulation-bow", "Articulation ladder", "articulation", 10,
          "Same phrase at tenuto, marcato, staccato, then spiccato; keep the pitch constant.",
          level_min=2),
    Drill("dynamic-shape", "Dynamic shaping", "dynamics", 10,
          "Play one phrase at ppp, mp, mf, ff, then random dynamics on the beat.",
          level_min=2),
    Drill("memory-spaced", "Spaced repetition review", "memory", 12,
          "Play yesterday's section from memory, note where you fell apart, retest after a break.",
          level_min=2),

    # ---------------- piano ----------------
    Drill("piano-hanon", "Hanon patterns", "technique", 12,
          "Two-octave patterns, both hands in unison then in contrary motion; metronome on.",
          instruments=("piano",), level_min=2),
    Drill("piano-voice-lead", "Chord voice-leading", "technique", 12,
          "Move through a progression keeping the top voice as smooth as possible.",
          instruments=("piano",), level_min=2),
    Drill("piano-hands-separate", "Hands separately, then together", "technique", 12,
          "Right hand alone, left hand alone, then attempt the combination at 80% tempo.",
          instruments=("piano",)),
    Drill("piano-trill", "Trills and double-note drills", "technique", 8,
          "Four-finger trill on a held key, then trill with melody above.",
          instruments=("piano",), level_min=2),
    Drill("piano-pedal", "Pedal technique", "articulation", 8,
          "Syncopated pedal changes under a static chord; aim for no audible gaps.",
          instruments=("piano",), level_min=2),
    Drill("piano-octaves", "Octave and stretch technique", "technique", 8,
          "Octave passage slowly with relaxed wrist, only as wide as you can hold cleanly.",
          instruments=("piano",), level_min=3),
    Drill("piano-read-hands", "Read with both hands ahead", "sight-reading", 10,
          "Read one page keeping both hands two beats ahead of the sounding note.",
          instruments=("piano",), level_min=2),

    # ---------------- guitar / bass / ukulele ----------------
    Drill("g-chord-change", "Chord change drill", "technique", 12,
          "Change between two chords on the beat for 2 minutes; reset only if it lands late.",
          instruments=("guitar", "bass", "ukulele"), level_min=1),
    Drill("g-metro-pick", "Alternate picking with metronome", "rhythm", 10,
          "Sixteenth-note picking at 60 bpm, accent the downstrokes, then random accents.",
          instruments=("guitar", "bass"), level_min=1),
    Drill("g-fret-mute", "Fretting-hand muting drill", "technique", 8,
          "Mute with the fretting hand while the picking hand keeps a steady pulse.",
          instruments=("guitar", "bass"), level_min=2),
    Drill("g-string-crossing", "String crossing", "rhythm", 10,
          "Alternate between non-adjacent strings to keep both hands honest.",
          instruments=("guitar", "bass"), level_min=2),
    Drill("g-fingerstyle", "Fingerstyle independence", "technique", 12,
          "Thumb and fingers on fixed patterns; keep the thumb quiet until the pattern locks.",
          instruments=("guitar",), level_min=2),
    Drill("g-barre", "Barre chord holds", "technique", 10,
          "Hold a barre for 30 seconds, release, repeat; check fretting pressure each round.",
          instruments=("guitar",), level_min=2),
    Drill("g-sweep", "Sweep picking speed", "rhythm", 8,
          "Sixteenth-note sweeps at a metronome tempo, two-octave patterns only.",
          instruments=("guitar",), level_min=3),
    Drill("g-per-position", "Two notes per position", "technique", 10,
          "One scale position at a time, one finger per fret, no position shifts.",
          instruments=("guitar", "bass"), level_min=2),
    Drill("bass-timbre", "Timbre and tone matching", "dynamics", 10,
          "Record one note, then match its weight and attack by feel, not by volume.",
          instruments=("bass",), level_min=2),
    Drill("u-strumming", "Strum pattern grid", "rhythm", 10,
          "Up-down strumming on a 16th-note grid, accent the 2 and 4, then vary.",
          instruments=("ukulele",), level_min=1),
    Drill("u-nodes", "Nailing tone and intonation", "intonation", 8,
          "Play the same chord shape on different strings; listen for beating and fix it.",
          instruments=("ukulele",), level_min=2),

    # ---------------- voice ----------------
    Drill("v-sirens", "Sirens", "stamina", 6,
          "Slide from low to high and back on a breath, then start in the middle of the range.",
          instruments=("voice",), level_min=1),
    Drill("v-sow", "Sow (ng) sounds", "warmup", 6,
          "Low 'v' into a hum, feel the vibration move to the mask.",
          instruments=("voice",), level_min=1),
    Drill("v-vowels", "Vowel isolation", "intonation", 10,
          "Hold 'ah' then 'ee' on one note; check that the pitch does not drift.",
          instruments=("voice",)),
    Drill("v-lip-trill", "Lip trill", "stamina", 6,
          "Trill on 'oo' and build to a phrase, resetting the breath before the top of the phrase.",
          instruments=("voice",)),
    Drill("v-support", "Breath support", "stamina", 8,
          "Inhale low and wide, speak the phrase on the outgoing breath, notice where it collapses.",
          instruments=("voice",)),
    Drill("v-resonance", "Resonance sweep", "dynamics", 8,
          "Hum one pitch and move it from chest to mask and back, keeping the volume equal.",
          instruments=("voice",), level_min=2),
    Drill("v-diction", "Diction over a triad", "articulation", 10,
          "Speak a text over a slow triad, then sing it, keeping consonants crisp.",
          instruments=("voice",), level_min=2),

    # ---------------- strings (violin, cello) ----------------
    Drill("s-open-strings", "Open-string intonation", "intonation", 10,
          "Match each open string against a drone, then against the fifth above.",
          instruments=("violin", "cello"), level_min=1),
    Drill("s-bowing", "Bow distribution", "articulation", 10,
          "Long bows split into equal segments, marking where the sound dies.",
          instruments=("violin", "cello"), level_min=2),
    Drill("s-shift", "Position shift drill", "technique", 12,
          "Shift between two positions on a held string, arriving in tune on the first bow.",
          instruments=("violin", "cello"), level_min=2),
    Drill("s-locked-shift", "Locked position scale", "technique", 10,
          "One scale entirely in one position, thumb where it belongs, no shifts.",
          instruments=("violin", "cello"), level_min=2),
    Drill("s-string-crossing", "String crossing on strings", "rhythm", 10,
          "Cross between adjacent strings on the beat at a metronome tempo.",
          instruments=("violin", "cello"), level_min=2),

    # ---------------- woodwinds ----------------
    Drill("w-tonguing", "Tonguing control", "articulation", 10,
          "Repeat a single note with clear 't' and 'd', keeping the tone identical.",
          instruments=("flute", "clarinet", "saxophone"), level_min=1),
    Drill("w-airsupport", "Air support", "stamina", 8,
          "Long tones with a steady air column, counting each breath as a full reset.",
          instruments=("flute", "clarinet", "saxophone"), level_min=2),
    Drill("w-low-register", "Low-register focus", "intonation", 10,
          "Slow low-register long tones, checking that pitch responds to the airstream.",
          instruments=("flute", "clarinet", "saxophone"), level_min=2),
    Drill("w-multiphonic", "Multiphonic or overtones", "technique", 8,
          "Find one stable multiphonic, then move it up a step at a time.",
          instruments=("flute", "clarinet", "saxophone"), level_min=3),

    # ---------------- brass ----------------
    Drill("b-buzz", "Buzzing", "warmup", 6,
          "Buzz on the mouthpiece, moving through the range in a comfortable chord.",
          instruments=("trumpet", "trombone", "horn"), level_min=1),
    Drill("b-attack", "Attack and release", "articulation", 10,
          "Short note on a stable pitch, stopping cleanly with no release pop.",
          instruments=("trumpet", "trombone", "horn"), level_min=2),
    Drill("b-range", "Range and endurance", "stamina", 8,
          "Long tones from the top of the staff down, in one breath.",
          instruments=("trumpet", "trombone", "horn"), level_min=2),
    Drill("b-slot", "Slotting", "intonation", 10,
          "Move between two partials and back, adjusting slots by ear only.",
          instruments=("trumpet", "trombone", "horn"), level_min=3),

    # ---------------- drums ----------------
    Drill("d-rudiments", "Rudiment pattern", "technique", 12,
          "One rudiment at 70 bpm on the pad, accent placement fixed before speed.",
          instruments=("drums",), level_min=1),
    Drill("d-timekeeping", "Timekeeping", "rhythm", 12,
          "Steady quarter notes on a metronome while counting eighths out loud.",
          instruments=("drums",), level_min=1),
    Drill("d-grid", "Grid reading", "sight-reading", 10,
          "Read a written grid, marking where the ghost notes fall before playing.",
          instruments=("drums",), level_min=2),
    Drill("d-dynamics", "Dynamic levels", "dynamics", 8,
          "Same groove at p and f, keeping the time signature identical.",
          instruments=("drums",), level_min=2),
    Drill("d-vision", "Stick control without looking", "technique", 8,
          "Slow paradiddle with eyes closed, checking hand path stays consistent.",
          instruments=("drums",), level_min=2),

    # ---------------- harmonica / accordion ----------------
    Drill("h-blow-draw", "Blow and draw switching", "technique", 10,
          "Alternate blow and draw on one note, then across a scale.",
          instruments=("harmonica",), level_min=1),
    Drill("h-chords", "Chord blocking", "harmonization", 10,
          "Play a simple chord progression and find the comfortable harmonica key.",
          instruments=("harmonica",), level_min=2),
    Drill("a-bellows", "Bellows control", "technique", 10,
          "Even bellows motion with accents on the pull, keeping the tone steady.",
          instruments=("accordion",), level_min=1),
    Drill("a-bass", "Bass and chord button work", "technique", 12,
          "Bass buttons in a simple pattern, then add chords underneath.",
          instruments=("accordion",), level_min=2),
]

INSTRUMENTS: List[Instrument] = [
    Instrument("piano", "Piano", "keyboard", "Two hands, ten fingers, one body - easy to over-practice the wrong thing.",
                ("right hand", "left hand", "coordination"), 5, "4/4, accent on beat 1"),
    Instrument("guitar", "Guitar", "fretted", "Picking hand and fretting hand fail independently - train them apart.",
                ("picking hand", "fretting hand", "coordination"), 4, "4/4, accent on beat 1"),
    Instrument("bass", "Bass", "fretted", "Timing and tone matter more than range.",
                ("fretting hand", "timing", "tone"), 4, "4/4, accent on beat 1"),
    Instrument("ukulele", "Ukulele", "fretted", "Short neck, fast chord changes - the change drill pays off.",
                ("picking hand", "fretting hand", "coordination"), 6, "4/4, accent on beat 1"),
    Instrument("voice", "Voice", "vocal", "Tension is invisible until it ruins the phrase.",
                ("breath", "resonance", "diction"), 3, "4/4, accent on beat 1"),
    Instrument("violin", "Violin", "strings", "Intonation and bow distribution dominate everything else.",
                ("bow arm", "left hand", "coordination"), 3, "4/4, accent on beat 1"),
    Instrument("cello", "Cello", "strings", "Endurance and shifting decide whether the piece gets finished.",
                ("bow arm", "left hand", "coordination"), 3, "4/4, accent on beat 1"),
    Instrument("flute", "Flute", "woodwind", "Air support carries pitch and endurance.",
                ("air", "tongue", "fingering"), 3, "4/4, accent on beat 1"),
    Instrument("clarinet", "Clarinet", "woodwind", "The tongue and the register switch must agree.",
                ("air", "tongue", "fingering"), 3, "4/4, accent on beat 1"),
    Instrument("saxophone", "Saxophone", "woodwind", "Breath economy decides the practice length.",
                ("air", "tongue", "fingering"), 3, "4/4, accent on beat 1"),
    Instrument("trumpet", "Trumpet", "brass", "Range work is delicate - most practice should be mid-range.",
                ("air", "tongue", "embouchure"), 3, "4/4, accent on beat 1"),
    Instrument("trombone", "Trombone", "brass", "Slide position accuracy needs slow, boring repetition.",
                ("slide", "air", "embouchure"), 3, "4/4, accent on beat 1"),
    Instrument("horn", "Horn", "brass", "Transposition and endurance dominate.",
                ("air", "tongue", "embouchure"), 3, "4/4, accent on beat 1"),
    Instrument("drums", "Drums", "percussion", "Timekeeping first, then subdivisions, then dynamics.",
                ("hands", "feet", "timekeeping"), 6, "4/4, accent on beat 1"),
    Instrument("harmonica", "Harmonica", "free reed", "Blow and draw switching is the whole game.",
                ("blow", "draw", "tone"), 6, "4/4, accent on beat 1"),
    Instrument("accordion", "Accordron", "free reed", "Bellows and fingers must be independent.",
                ("bellows", "right hand", "left hand"), 4, "4/4, accent on beat 1"),
]

INSTRUMENT_BY_KEY: Dict[str, Instrument] = {i.key: i for i in INSTRUMENTS}

# Some drill areas are not in the weak-spot list but still need a block home.
EXTRA_AREAS = {"warmup": "Warm-up", "harmonization": "Harmonisation"}


def label_for_area(area: str) -> str:
    return AREA_LABELS.get(area, EXTRA_AREAS.get(area, area.replace("-", " ").title()))


def drills_for(instrument_key: str, area: str, level: str) -> List[Drill]:
    """Return drills that suit this instrument, area and level."""
    prof = INSTRUMENT_BY_KEY.get(instrument_key)
    level_rank = LEVELS.index(level) + 1 if level in LEVELS else 1
    out: List[Drill] = []
    for d in DRILLS:
        if d.area != area:
            continue
        if d.level_min > level_rank:
            continue
        if d.instruments:
            if instrument_key not in d.instruments:
                continue
        elif d.families and prof and prof.family not in d.families:
            continue
        out.append(d)
    return out


def any_drills_for(instrument_key: str, level: str) -> List[Drill]:
    prof = INSTRUMENT_BY_KEY.get(instrument_key)
    level_rank = LEVELS.index(level) + 1 if level in LEVELS else 1
    out: List[Drill] = []
    for d in DRILLS:
        if d.level_min > level_rank:
            continue
        if d.instruments and instrument_key not in d.instruments:
            continue
        if not d.instruments and d.families and prof and prof.family not in d.families:
            continue
        out.append(d)
    return out
