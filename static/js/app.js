/* music-practice-forge front end - vanilla JS, no build step. */
(function () {
  "use strict";

  var state = {
    plan: null,
    areas: [],
    instruments: [],
    drills: [],
    lastPayload: null,
    journal: { sessions: [], pieces: [], momentum: {}, plateaus: [] }
  };

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s === undefined || s === null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function toast(msg) {
    var t = $("toast");
    if (!t) {
      t = document.createElement("div");
      t.id = "toast";
      t.className = "toast";
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.classList.add("show");
    setTimeout(function () { t.classList.remove("show"); }, 1900);
  }
  function api(path, options) {
    return fetch(path, options).then(function (r) {
      if (!r.ok) { return r.text().then(function (t) { throw new Error(t || r.status); }); }
      return r.json();
    });
  }
  function post(path, body) {
    return api(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {})
    });
  }

  /* ---------------- form ---------------- */

  function collectForm() {
    var payload = {
      instrument: $("instrument").value,
      level: $("level").value,
      minutes: parseInt($("minutes").value, 10),
      sessions_per_week: parseInt($("sessions_per_week").value, 10),
      focus_preset: $("focus_preset").value,
      piece: $("piece").value.trim(),
      current_tempo: parseInt($("current_tempo").value || "0", 10),
      target_tempo: parseInt($("target_tempo").value || "0", 10),
      weak_spots: []
    };
    var chips = document.querySelectorAll("#weak-chips .chip.on");
    for (var i = 0; i < chips.length; i++) { payload.weak_spots.push(chips[i].getAttribute("data-area")); }
    return payload;
  }

  function saveForm() {
    try { localStorage.setItem("mpf-form", JSON.stringify(collectForm())); } catch (e) { /* ignore */ }
  }

  function restoreForm() {
    var raw = null;
    try { raw = localStorage.getItem("mpf-form"); } catch (e) { raw = null; }
    if (!raw) { return; }
    var data;
    try { data = JSON.parse(raw); } catch (e) { return; }
    if (!data) { return; }
    ["instrument", "level", "focus_preset", "piece"].forEach(function (k) {
      if (data[k] !== undefined && $(k)) { $(k).value = data[k]; }
    });
    ["minutes", "sessions_per_week"].forEach(function (k) {
      if (data[k] !== undefined && $(k)) { $(k).value = data[k]; }
    });
    if (data.current_tempo !== undefined && $("current_tempo")) { $("current_tempo").value = data.current_tempo; }
    if (data.target_tempo !== undefined && $("target_tempo")) { $("target_tempo").value = data.target_tempo; }
    (data.weak_spots || []).forEach(function (area) {
      var chip = document.querySelector('#weak-chips .chip[data-area="' + area + '"]');
      if (chip) { chip.classList.add("on"); }
    });
    syncOutputs();
  }

  function syncOutputs() {
    $("minutes-out").textContent = $("minutes").value;
    $("spw-out").textContent = $("sessions_per_week").value;
    if ($("quality-out") && $("j-quality")) { $("quality-out").textContent = $("j-quality").value; }
  }

  /* ---------------- rendering ---------------- */

  function renderScore(score) {
    var circumference = 2 * Math.PI * 52;
    var offset = circumference * (1 - score.overall / 100);
    var color = score.overall >= 70 ? "#6bcf8f" : (score.overall >= 50 ? "#f0b429" : "#ef6b6b");
    var html = "";
    html += '<div class="card"><div class="card-head"><h3>Session readiness</h3>';
    html += '<span class="sub">' + esc(score.grade) + '</span></div>';
    html += '<div class="score-wrap">';
    html += '<div class="ring"><svg width="128" height="128">';
    html += '<circle cx="64" cy="64" r="52" stroke="#2a3242" stroke-width="12" fill="none"/>';
    html += '<circle cx="64" cy="64" r="52" stroke="' + color + '" stroke-width="12" fill="none"';
    html += ' stroke-linecap="round" stroke-dasharray="' + circumference.toFixed(1) + '"';
    html += ' stroke-dashoffset="' + offset.toFixed(1) + '"/></svg>';
    html += '<div class="value">' + score.overall + '<small>out of 100</small></div></div>';
    html += '<div class="axes">';
    score.axes.forEach(function (a) {
      html += '<div class="axis"><div class="axis-top"><b>' + esc(a.label) + '</b><span>' + a.score + '</span></div>';
      html += '<div class="bar"><i style="width:' + a.score + '%"></i></div></div>';
    });
    html += '</div></div>';
    if (score.next_actions && score.next_actions.length) {
      html += '<div class="actions"><h3>Next actions</h3><ul>';
      score.next_actions.forEach(function (n) { html += '<li>' + esc(n) + '</li>'; });
      html += '</ul></div>';
    }
    html += '</div>';
    return html;
  }

  function renderSession(session, meta) {
    var html = "";
    html += '<div class="card"><div class="card-head"><h3>Today&#39;s session &mdash; ' + esc(session.theme_title) + '</h3>';
    html += '<span class="sub">' + session.total_minutes + ' minutes &middot; ' + esc(meta.level) + '</span></div>';
    session.blocks.forEach(function (b) {
      html += '<div class="block"><div class="block-top"><b>' + esc(b.title) + '</b><span class="minutes">' + b.minutes + ' min</span></div>';
      html += '<div class="why">' + esc(b.why) + '</div>';
      if (b.drills && b.drills.length) {
        html += '<ul>';
        b.drills.forEach(function (d) {
          html += '<li><strong>' + esc(d.name) + '</strong> &mdash; ' + esc(d.how) + '</li>';
        });
        html += '</ul>';
      }
      html += '<span class="stop">' + esc(b.stop_rule) + '</span></div>';
    });
    if (session.plan_notes && session.plan_notes.length) {
      html += '<h3 style="margin-top:14px">Notes on this plan</h3><ul class="flags">';
      session.plan_notes.forEach(function (n) { html += '<li>' + esc(n) + '</li>'; });
      html += '</ul>';
    }
    html += '<div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap">';
    html += '<button class="ghost" id="copy-sheet">Copy printable sheet</button>';
    html += '<button class="ghost" id="print-plan">Print</button>';
    html += '</div></div>';
    return html;
  }

  function renderWeek(week) {
    var html = "";
    html += '<div class="card"><div class="card-head"><h3>The week</h3>';
    html += '<span class="sub">' + week.sessions_per_week + ' sessions &middot; ' + week.weekly_minutes + ' min (' + week.weekly_hours + ' h)</span></div>';
    html += '<div class="week-grid">';
    week.sessions.forEach(function (s) {
      html += '<div class="day"><b>' + esc(s.day) + '</b><div class="theme">' + esc(s.theme_title) + '</div>';
      html += '<div class="meta">' + s.minutes + ' min &middot; ' + esc(s.focus_areas.join(", ")) + '</div></div>';
    });
    if (week.rest_days && week.rest_days.length) {
      week.rest_days.forEach(function (d) {
        html += '<div class="day rest"><b>' + esc(d) + '</b><div class="theme">Rest</div><div class="meta">No instrument</div></div>';
      });
    }
    html += '</div>';
    if (week.flags && week.flags.length) {
      html += '<h3 style="margin-top:14px">Load flags</h3><ul class="flags">';
      week.flags.forEach(function (f) { html += '<li>' + esc(f) + '</li>'; });
      html += '</ul>';
    }
    html += '</div>';
    return html;
  }

  function renderLadder(ladder) {
    if (!ladder || !ladder.rungs || !ladder.rungs.length) { return ""; }
    var html = "";
    html += '<div class="card"><div class="card-head"><h3>Tempo ladder</h3><span class="sub">';
    if (ladder.status === "climb") {
      html += esc(ladder.current_tempo) + ' &rarr; ' + esc(ladder.target_tempo) + ' bpm &middot; ' + esc(ladder.step_size) + ' bpm steps &middot; ~' + esc(ladder.weeks_estimate) + ' weeks';
    } else if (ladder.status === "hold") {
      html += 'Hold at ' + esc(ladder.current_tempo) + ' bpm and make it reliable';
    } else {
      html += 'No current tempo recorded';
    }
    html += '</span></div>';
    html += '<table><thead><tr><th>#</th><th>bpm</th><th>week</th><th>min</th><th>metronome</th><th>what to do</th></tr></thead><tbody>';
    ladder.rungs.forEach(function (r) {
      html += '<tr><td class="num">' + r.index + '</td><td class="num"><strong>' + r.bpm + '</strong></td>';
      html += '<td class="num">' + r.week + '</td><td class="num">' + r.minutes + '</td>';
      html += '<td>' + esc(r.click) + '</td><td>' + esc(r.instruction) + '</td></tr>';
    });
    html += '</tbody></table>';
    if (ladder.flags && ladder.flags.length) {
      html += '<ul class="flags">';
      ladder.flags.forEach(function (f) { html += '<li>' + esc(f) + '</li>'; });
      html += '</ul>';
    }
    html += '</div>';
    return html;
  }

  function renderMomentum(journal) {
    var m = journal.momentum || {};
    var html = "";
    html += '<div class="card"><div class="card-head"><h3>Journal feedback</h3><span class="sub">';
    html += (m.sessions || 0) + ' sessions &middot; ' + (m.minutes || 0) + ' min logged';
    if (m.streak_days) { html += ' &middot; ' + m.streak_days + '-day streak'; }
    html += '</span></div>';
    if (m.tempo_trend !== null && m.tempo_trend !== undefined) {
      html += '<p class="muted">Tempo trend: <strong>' + (m.tempo_trend > 0 ? "+" : "") + m.tempo_trend + ' bpm</strong> per logged session.</p>';
    }
    if (m.notes && m.notes.length) {
      html += '<ul class="flags">';
      m.notes.forEach(function (n) { html += '<li>' + esc(n) + '</li>'; });
      html += '</ul>';
    }
    var plateaus = journal.plateaus || [];
    if (plateaus.length) {
      html += '<h3 style="margin-top:14px">Plateaus</h3>';
      plateaus.forEach(function (p) {
        html += '<div class="block"><div class="block-top"><b>' + esc(p.piece) + '</b><span class="minutes">stuck at ' + esc(p.stuck_tempo) + ' bpm</span></div>';
        html += '<div class="why">No tempo gain over the last ' + esc(p.attempts) + ' logged attempts.</div><ul>';
        p.suggestions.forEach(function (s) { html += '<li>' + esc(s) + '</li>'; });
        html += '</ul></div>';
      });
    }
    html += '</div>';
    return html;
  }

  function renderPlan(data) {
    state.plan = data;
    var body = $("results-body");
    body.classList.remove("hidden");
    $("results-empty").classList.add("hidden");
    var html = "";
    html += renderScore(data.score);
    html += renderSession(data.session, data.meta);
    html += renderWeek(data.week);
    html += renderLadder(data.ladder);
    html += renderMomentum(data.journal);
    body.innerHTML = html;

    var copyBtn = $("copy-sheet");
    if (copyBtn) {
      copyBtn.addEventListener("click", function () {
        post("/api/export/sheet.md", state.lastPayload).then(function (text) {
          return copyText(text);
        }).then(function () { toast("Practice sheet copied"); })
          .catch(function (e) { toast("Copy failed: " + e.message); });
      });
    }
    var printBtn = $("print-plan");
    if (printBtn) { printBtn.addEventListener("click", function () { window.print(); }); }
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
        document.body.removeChild(ta);
        resolve();
      } catch (e) {
        document.body.removeChild(ta);
        reject(e);
      }
    });
  }

  /* ---------------- journal ---------------- */

  function renderJournal() {
    var j = state.journal;
    var html = "";
    html += '<div class="card"><div class="card-head"><h3>Momentum</h3><span class="sub">' + (j.momentum.sessions || 0) + ' sessions logged</span></div>';
    html += '<table><tbody>';
    html += '<tr><th>Total practice</th><td class="num">' + (j.momentum.minutes || 0) + ' min (' + (j.momentum.hours || 0) + ' h)</td></tr>';
    html += '<tr><th>Logging streak</th><td class="num">' + (j.momentum.streak_days || 0) + ' days</td></tr>';
    html += '<tr><th>Tempo trend</th><td class="num">' + (j.momentum.tempo_trend === null || j.momentum.tempo_trend === undefined ? "-" : j.momentum.tempo_trend + " bpm/session") + '</td></tr>';
    html += '<tr><th>Recent sessions</th><td class="num">' + (j.momentum.recent_sessions || 0) + ' (' + (j.momentum.recent_minutes || 0) + ' min)</td></tr>';
    html += '</tbody></table>';
    if (j.momentum.notes && j.momentum.notes.length) {
      html += '<ul class="flags">';
      j.momentum.notes.forEach(function (n) { html += '<li>' + esc(n) + '</li>'; });
      html += '</ul>';
    }
    html += '</div>';

    html += '<div class="card"><div class="card-head"><h3>Logged sessions</h3></div>';
    if (!j.sessions.length) {
      html += '<p class="muted">Nothing logged yet. The first entry is the one that starts the feedback loop.</p>';
    } else {
      html += '<table><thead><tr><th>Date</th><th>Piece</th><th>Area</th><th>Min</th><th>bpm</th><th>Feel</th><th>Notes</th><th></th></tr></thead><tbody>';
      j.sessions.forEach(function (s) {
        html += '<tr><td class="num">' + esc(s.session_date) + '</td><td>' + esc(s.piece) + '</td>';
        html += '<td>' + esc(s.area) + '</td><td class="num">' + esc(s.minutes) + '</td>';
        html += '<td class="num">' + (s.tempo === null || s.tempo === undefined ? "-" : esc(s.tempo)) + '</td>';
        html += '<td class="num">' + esc(s.quality) + '/5</td><td>' + esc(s.notes) + '</td>';
        html += '<td><button class="ghost" data-del="' + s.id + '">Delete</button></td></tr>';
      });
      html += '</tbody></table>';
    }
    html += '</div>';

    $("journal-body").innerHTML = html;

    var delButtons = document.querySelectorAll("[data-del]");
    for (var i = 0; i < delButtons.length; i++) {
      delButtons[i].addEventListener("click", function (ev) {
        var id = ev.target.getAttribute("data-del");
        api("/api/sessions/" + id, { method: "DELETE" }).then(function (res) {
          state.journal = { sessions: res.sessions, pieces: [], momentum: res.momentum, plateaus: res.plateaus };
          renderJournal();
          toast("Session deleted");
        });
      });
    }
  }

  function loadJournal() {
    return api("/api/sessions").then(function (res) {
      state.journal = res;
      renderJournal();
    });
  }

  /* ---------------- library ---------------- */

  function renderLibrary() {
    var inst = $("lib-instrument").value;
    var area = $("lib-area").value;
    var q = $("lib-search").value.trim().toLowerCase();
    var html = "";
    var shown = 0;
    state.drills.forEach(function (d) {
      if (inst !== "all" && d.instruments.length && d.instruments.indexOf(inst) === -1) { return; }
      if (area !== "all" && d.area !== area) { return; }
      if (q && (d.name + " " + d.how).toLowerCase().indexOf(q) === -1) { return; }
      shown += 1;
      html += '<div class="drill"><div class="meta-col"><b>' + esc(d.name) + '</b>';
      html += '<div><span class="tag-sm">' + esc(d.area) + '</span><span class="tag-sm">' + d.minutes + ' min</span></div></div>';
      html += '<div class="how">' + esc(d.how) + '</div></div>';
    });
    if (!shown) { html = '<p class="muted">No drill matches that filter.</p>'; }
    $("library-body").innerHTML = html;
  }

  function loadLibrary() {
    return api("/api/instruments").then(function (res) {
      state.instruments = res.instruments;
      state.areas = res.areas;
      state.drills = res.drills;

      var opt = "";
      res.instruments.forEach(function (i) { opt += '<option value="' + i.key + '">' + esc(i.label) + '</option>'; });
      $("instrument").innerHTML = opt;
      $("lib-instrument").innerHTML = '<option value="all">All instruments</option>' + opt;

      var aopt = '<option value="all">All areas</option>';
      res.areas.forEach(function (a) { aopt += '<option value="' + a.key + '">' + esc(a.label) + '</option>'; });
      $("lib-area").innerHTML = aopt;
      $("j-area").innerHTML = aopt;

      var chips = "";
      res.areas.forEach(function (a) {
        chips += '<span class="chip" data-area="' + a.key + '">' + esc(a.label) + '</span>';
      });
      $("weak-chips").innerHTML = chips;

      restoreForm();
      bindChipClicks();
      renderLibrary();
    });
  }

  function bindChipClicks() {
    var chips = document.querySelectorAll("#weak-chips .chip");
    for (var i = 0; i < chips.length; i++) {
      chips[i].addEventListener("click", function (ev) {
        ev.currentTarget.classList.toggle("on");
        saveForm();
      });
    }
  }

  /* ---------------- presets ---------------- */

  var PRESETS = {
    "beginner-piano": { instrument: "piano", level: "beginner", minutes: 30, sessions_per_week: 5, focus_preset: "balanced", piece: "", current_tempo: 0, target_tempo: 0, weak_spots: ["technique", "sight-reading"] },
    "guitar-fest": { instrument: "guitar", level: "intermediate", minutes: 60, sessions_per_week: 6, focus_preset: "repertoire", piece: "", current_tempo: 96, target_tempo: 120, weak_spots: ["tempo", "dynamics", "stamina"] },
    "exam-prep": { instrument: "piano", level: "advanced", minutes: 90, sessions_per_week: 6, focus_preset: "exam", piece: "", current_tempo: 60, target_tempo: 104, weak_spots: ["tempo", "memory", "rhythm"] }
  };

  function applyPreset(name) {
    var p = PRESETS[name];
    if (!p) { return; }
    $("instrument").value = p.instrument;
    $("level").value = p.level;
    $("minutes").value = p.minutes;
    $("sessions_per_week").value = p.sessions_per_week;
    $("focus_preset").value = p.focus_preset;
    $("current_tempo").value = p.current_tempo;
    $("target_tempo").value = p.target_tempo;
    var chips = document.querySelectorAll("#weak-chips .chip");
    for (var i = 0; i < chips.length; i++) {
      chips[i].classList.toggle("on", p.weak_spots.indexOf(chips[i].getAttribute("data-area")) !== -1);
    }
    syncOutputs();
    saveForm();
    buildPlan();
  }

  /* ---------------- wiring ---------------- */

  function buildPlan() {
    var payload = collectForm();
    state.lastPayload = payload;
    saveForm();
    $("results-body").innerHTML = '<p class="muted">Building...</p>';
    $("results-body").classList.remove("hidden");
    $("results-empty").classList.add("hidden");
    post("/api/plan", payload).then(function (data) {
      if (data.error) { throw new Error(data.error); }
      renderPlan(data);
    }).catch(function (e) {
      $("results-body").innerHTML = '<div class="card"><p class="muted">Could not build the plan: ' + esc(e.message) + '</p></div>';
    });
  }

  function init() {
    document.querySelectorAll(".tab").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll(".tab").forEach(function (b) { b.classList.remove("active"); });
        document.querySelectorAll(".tabpane").forEach(function (p) { p.classList.remove("active"); });
        btn.classList.add("active");
        $("tab-" + btn.getAttribute("data-tab")).classList.add("active");
      });
    });

    $("plan-form").addEventListener("submit", function (ev) { ev.preventDefault(); buildPlan(); });
    $("minutes").addEventListener("input", syncOutputs);
    $("sessions_per_week").addEventListener("input", syncOutputs);
    $("j-quality").addEventListener("input", syncOutputs);
    $("piece").addEventListener("change", saveForm);
    $("instrument").addEventListener("change", saveForm);

    document.querySelectorAll("[data-preset]").forEach(function (b) {
      b.addEventListener("click", function () { applyPreset(b.getAttribute("data-preset")); });
    });

    $("journal-form").addEventListener("submit", function (ev) {
      ev.preventDefault();
      var body = {
        session_date: $("session_date").value,
        piece: $("j-piece").value.trim(),
        area: $("j-area").value,
        minutes: parseInt($("j-minutes").value || "0", 10),
        tempo: parseInt($("j-tempo").value || "0", 10) || null,
        quality: parseInt($("j-quality").value || "3", 10),
        notes: $("j-notes").value.trim()
      };
      post("/api/sessions", body).then(function (res) {
        state.journal = { sessions: res.sessions, pieces: state.journal.pieces, momentum: res.momentum, plateaus: res.plateaus };
        $("j-notes").value = "";
        $("j-tempo").value = "";
        renderJournal();
        toast("Session logged");
      });
    });

    $("lib-instrument").addEventListener("change", renderLibrary);
    $("lib-area").addEventListener("change", renderLibrary);
    $("lib-search").addEventListener("input", renderLibrary);

    var today = new Date().toISOString().slice(0, 10);
    $("session_date").value = today;

    loadLibrary().then(loadJournal);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
