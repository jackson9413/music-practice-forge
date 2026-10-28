"""Unit tests for the practice planning engine (stdlib unittest, no deps)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from music.db import add_session, init_db, list_sessions
from music.engine import build_plan
from music.planner import allocate, build_session, build_week
from music.tempo import build_ladder, detect_plateaus, momentum


class TestAllocation(unittest.TestCase):
    def test_blocks_sum_to_budget(self):
        for budget in (20, 30, 45, 60, 75, 90, 120):
            alloc = allocate({"a": 0.3, "b": 0.3, "c": 0.25, "d": 0.15}, budget)
            self.assertEqual(sum(alloc.values()), budget, "budget %d" % budget)

    def test_no_block_below_minimum(self):
        alloc = allocate({"a": 0.9, "b": 0.05, "c": 0.05}, 30)
        for minutes in alloc.values():
            self.assertGreaterEqual(minutes, 5)

    def test_session_total_matches_blocks(self):
        session = build_session("piano", 60, ["technique", "rhythm"], "K545", "intermediate", "balanced")
        self.assertEqual(sum(b.minutes for b in session.blocks), 60)
        self.assertEqual(session.total_minutes, 60)

    def test_session_scales_down_for_short_budget(self):
        session = build_session("guitar", 15, [], "", "beginner", "balanced")
        self.assertEqual(sum(b.minutes for b in session.blocks), 15)
        self.assertLessEqual(len(session.blocks), 3)

    def test_drills_are_not_repeated_across_blocks(self):
        session = build_session("piano", 90, ["technique"], "", "intermediate", "balanced")
        ids = [d.id for b in session.blocks for d in b.drills]
        self.assertEqual(len(ids), len(set(ids)))


class TestWeek(unittest.TestCase):
    def test_week_covers_every_weak_spot(self):
        week = build_week("violin", 45, 5, ["technique", "rhythm", "ear", "memory"], "", "intermediate", "balanced")
        covered = set()
        for s in week.sessions:
            covered.update(s.focus_areas)
        for spot in ("technique", "rhythm", "ear", "memory"):
            self.assertIn(spot, covered)

    def test_weekly_minutes(self):
        week = build_week("piano", 60, 4, ["technique"], "", "intermediate", "balanced")
        self.assertEqual(week.weekly_minutes, 240)
        self.assertEqual(len(week.sessions), 4)

    def test_rest_days_exist(self):
        week = build_week("flute", 30, 3, ["technique"], "", "beginner", "balanced")
        self.assertTrue(week.rest_days)


class TestTempo(unittest.TestCase):
    def test_ladder_climbs_to_target(self):
        ladder = build_ladder(72, 100, "guitar", "intermediate", 4, 45, "Bach")
        self.assertEqual(ladder["status"], "climb")
        self.assertEqual(ladder["rungs"][-1]["bpm"], 100)
        self.assertEqual(ladder["rungs"][0]["bpm"], 72)
        for rung in ladder["rungs"]:
            self.assertGreater(rung["minutes"], 0)

    def test_ladder_holds_when_target_not_higher(self):
        ladder = build_ladder(100, 90, "piano", "advanced", 4, 45, "")
        self.assertEqual(ladder["status"], "hold")

    def test_ladder_step_respects_instrument_cap(self):
        ladder = build_ladder(180, 220, "guitar", "advanced", 5, 45, "")
        self.assertLessEqual(ladder["step_size"], 4)

    def test_plateau_detected_when_tempo_freezes(self):
        entries = [
            {"id": 1, "session_date": "2026-10-01", "piece": "Etude", "tempo": 80},
            {"id": 2, "session_date": "2026-10-02", "piece": "Etude", "tempo": 88},
            {"id": 3, "session_date": "2026-10-03", "piece": "Etude", "tempo": 88},
            {"id": 4, "session_date": "2026-10-04", "piece": "Etude", "tempo": 88},
        ]
        plateaus = detect_plateaus(entries)
        self.assertTrue(plateaus)
        self.assertEqual(plateaus[0]["stuck_tempo"], 88)
        self.assertTrue(plateaus[0]["suggestions"])

    def test_momentum_reports_streak(self):
        entries = [
            {"id": 1, "session_date": "2026-10-01", "piece": "A", "tempo": 60, "minutes": 30},
            {"id": 2, "session_date": "2026-10-02", "piece": "A", "tempo": 64, "minutes": 30},
        ]
        mom = momentum(entries)
        self.assertEqual(mom["sessions"], 2)
        self.assertEqual(mom["minutes"], 60)
        self.assertEqual(mom["tempo_trend"], 4.0)


class TestEngine(unittest.TestCase):
    def test_build_plan_payload(self):
        plan = build_plan({
            "instrument": "piano", "level": "intermediate", "minutes": 60,
            "sessions_per_week": 4, "weak_spots": ["technique", "tempo"],
            "piece": "Mozart K545", "current_tempo": 66, "target_tempo": 96,
        })
        self.assertEqual(plan["session"]["total_minutes"], 60)
        self.assertEqual(plan["week"]["weekly_minutes"], 240)
        self.assertTrue(plan["ladder"]["rungs"])
        self.assertIn("overall", plan["score"])
        self.assertEqual(len(plan["score"]["axes"]), 5)
        self.assertTrue(plan["instrument"]["label"])

    def test_bad_input_is_handled(self):
        plan = build_plan({"instrument": "kazoo", "minutes": "abc", "sessions_per_week": 99})
        self.assertEqual(plan["instrument"]["key"], "piano")
        self.assertGreaterEqual(plan["meta"]["minutes"], 10)
        self.assertLessEqual(plan["meta"]["sessions_per_week"], 7)


class TestDb(unittest.TestCase):
    def setUp(self):
        self.path = "/tmp/mpf_test.db"
        if os.path.exists(self.path):
            os.remove(self.path)
        init_db(self.path)

    def test_add_and_list(self):
        row = add_session(piece="Etude", minutes=45, tempo=72, quality=4, path=self.path)
        self.assertTrue(row["id"])
        rows = list_sessions(path=self.path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["piece"], "Etude")


if __name__ == "__main__":
    unittest.main(verbosity=2)
