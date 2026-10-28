# music-practice-forge

A local-first **deliberate-practice planner for musicians**. Give it your instrument, how long you can practise,
which piece you are working on and where you are weak - it returns a timed session sheet, a week of sessions,
a tempo ladder with metronome patterns, plateau-breakers, and a five-axis readiness score.

No account. No API keys. No cloud. Your practice journal stays in a local SQLite file.

---

## Why it exists

Most practice advice is generic: "play slowly", "use a metronome", "record yourself". The hard part is turning
that into **a concrete 45 minutes** that fits the time you actually have, targets the specific weakness you
have today, and moves the tempo in steps small enough to survive.

music-practice-forge does the arithmetic so you can spend the session on the instrument:

- **Blocks add up to exactly your minute budget.** No "warm up for a while", no session that quietly becomes
  a 90-minute session because the reading block ate the clock.
- **Every block has a stop rule.** Most practice sessions fail because nobody decides in advance when to stop.
- **The tempo ladder is sized for your instrument.** A flute and a guitar cannot absorb the same bpm jumps, so
  the step size is derived from the instrument profile and the current tempo, then capped.
- **The week covers every weak spot you flagged**, and the app tells you when it could not fit them all.
- **The journal closes the loop.** Log what you actually played and the app detects plateaus (a tempo that has
  stopped moving), reports the tempo trend, and offers specific interventions instead of "try harder".

## Features

| Area | What you get |
|---|---|
| Session planner | 5-6 timed blocks (warm-up, slow work, tempo ladder, repertoire, reading/ear, log) with drills, instructions and stop rules |
| Week planner | Sessions laid across the week with a theme per day, rest days, weekly load flags |
| Tempo ladder | Rung-by-rung bpm climb with metronome click patterns, minutes per rung and week assignment |
| Plateau detection | Flags pieces whose tempo stopped moving and gives four concrete interventions |
| Readiness score | 0-100 across pacing, goal alignment, load balance, tempo feasibility and journal momentum |
| Journal | Log sessions (piece, minutes, tempo, feel, notes); tracks streak, volume and tempo trend |
| Drill library | 59 drills across 16 instruments, each with the instruction the planner gives you |
| Print / copy | Export the session as a printable markdown sheet, or print the page |

## Tech stack

- **Backend:** Python 3.9+, Flask 3, SQLite (stdlib sqlite3)
- **Frontend:** vanilla HTML / CSS / JS - no build step, no framework, no CDN
- **Tests:** stdlib unittest (16 tests, no external test deps)
- **Deps:** one - Flask

## Run it

```bash
cd music-practice-forge
python3 -m venv .venv && source .venv/bin/activate    # optional
pip install -r requirements.txt
./run.sh            # or: python3 app.py
```

Then open **http://127.0.0.1:5017**

Change the port with `PORT=8080 ./run.sh`.

### Tests

```bash
python3 -m unittest discover -s tests -v
```

## How the planning works

**Block allocation.** Each block has a base weight (warm-up 14%, slow work 18%, ladder 22%, repertoire 22%,
reading/ear 16%, log 8%). Your weak spots add weight to the blocks that fix them - flag *tempo* and the ladder
block grows; flag *sight-reading* and the reading block grows. The minutes are then allocated in 5-minute steps,
steered by how far each block sits from its ideal share, and the total is forced to match your budget exactly.

**Tempo ladder.** Step size = 5% of your current tempo, clamped to the instrument's cap (3 bpm for voice and
strings, 4-6 for most others) and widened only if the gap would need more than 12 rungs. Each rung gets a
metronome pattern that gets harder with speed, and the estimate assumes two touches per rung (reach it, confirm
it) plus a 25% plateau allowance.

**Readiness score.** Weighted mean of five axes: pacing (20%), goal alignment (25%), load balance (20%),
tempo feasibility (20%) and journal momentum (15%). The two weakest axes become your "next actions".

**Load bands.** Recommended weekly minutes: beginner 120-300, intermediate 240-600, advanced 360-900.
Under-shooting is penalised harder than over-shooting.

## Project layout

```
music-practice-forge/
├── app.py                  Flask app + JSON API
├── music/
│   ├── instruments.py      16 instrument profiles, 59 drills
│   ├── planner.py          session blocks, allocation, week layout
│   ├── tempo.py            tempo ladders, plateau detection, momentum
│   ├── scoring.py          five-axis readiness score
│   ├── engine.py           assembles the full plan payload
│   └── db.py               SQLite journal
├── templates/index.html    single-page UI
├── static/css/style.css    styles (light-on-dark, print stylesheet)
├── static/js/app.js        vanilla JS front end
├── tests/test_planner.py   16 unit tests
└── data/practice.db        your journal (created on first run, git-ignored)
```

## API

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/plan` | POST | Build the full plan from the form payload |
| `/api/instruments` | GET | Instruments, areas and the drill library |
| `/api/sessions` | GET / POST | Read or log journal entries |
| `/api/sessions/<id>` | DELETE | Remove a journal entry |
| `/api/export/sheet.md` | POST | Printable practice sheet as markdown |
| `/healthz` | GET | Liveness check |

## Privacy

Everything is stored in `data/practice.db` on your machine. The app makes no outbound network calls.

## License

MIT
