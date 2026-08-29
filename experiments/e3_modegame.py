"""E3 - hidden-mode game (ground-truth scored, no judge).

Each episode: pick a hidden mode M; a simulator writes T short in-mode lines
(never naming M); three predictors guess M and are scored against ground truth:

  RANDOM   uniform guess (chance baseline)
  SINGLE   a plain LLM reads the whole transcript and classifies (an HONEST
           strong baseline -- not a crippled one)
  LOOP     the stance sensor + Dirichlet filter accumulated across the lines

The SINGLE baseline matters: a bare LLM is not at chance on this task, so
reporting chance as the baseline inflates any apparent gain from the loop. If
LOOP ties SINGLE, the filter is buying persistence/state, not raw accuracy.

Usage: python -m experiments.e3_modegame [episodes]
"""
from __future__ import annotations
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from selfmodel import (MODES, chat, stance_likelihood, dirichlet_step,  # noqa: E402
                       fresh_alpha, p_from_alpha)

EPISODES = int(sys.argv[1]) if len(sys.argv) > 1 else 30
T = int(os.environ.get("E3_TURNS", "3"))
OUT = os.environ.get("E3_OUT", "results/e3_modegame.jsonl")

DEFS = {
    "exploring": "curious, asks questions, opens topics",
    "evaluating": "weighing a decision, wants a verdict, names criteria",
    "overwhelmed": "too much going on, wants scope reduced",
    "asserting": "decisive, issues instructions, wants action now",
    "disengaging": "winding down, deferring, closing the session",
}


def sim_line(mode, i):
    sysm = ("You are simulating a person chatting with an assistant about "
            "ordinary work topics. Current stance: %s (%s). Write ONE short chat "
            "line (under 25 words) consistent with that stance. Do NOT name the "
            "stance." % (mode, DEFS[mode]))
    return chat(sysm, "Line %d of the conversation." % (i + 1), temperature=1.0,
                max_tokens=60)


def single_guess(lines):
    sysm = ("Classify the overall stance of the user from these lines. Modes: %s. "
            'JSON only: {"mode":"<mode>"}' % ", ".join(MODES))
    out = chat(sysm, " / ".join(lines), temperature=0.0, max_tokens=40)
    low = (out or "").lower()
    for m in MODES:
        if m in low:
            return m
    return random.choice(MODES)


def main():
    results = []
    with open(OUT, "a") as f:
        f.write(json.dumps({"kind": "header", "episodes": EPISODES, "turns": T}) + "\n")
        for ep in range(EPISODES):
            truth = random.choice(MODES)
            lines, alpha = [], fresh_alpha()
            for i in range(T):
                ln = sim_line(truth, i)
                if not ln:
                    continue
                lines.append(ln)
                ell, e = stance_likelihood(ln)
                if ell:
                    alpha, _, _ = dirichlet_step(alpha, ell, e)
            p, _ = p_from_alpha(alpha)
            loop = max(p, key=p.get)
            single = single_guess(lines) if lines else random.choice(MODES)
            rand = random.choice(MODES)
            row = {"ep": ep, "truth": truth, "loop": loop, "single": single,
                   "rand": rand, "loop_ok": loop == truth,
                   "single_ok": single == truth, "rand_ok": rand == truth}
            results.append(row)
            f.write(json.dumps(row) + "\n")
        acc = {k: round(sum(1 for r in results if r[k + "_ok"]) / max(1, len(results)), 3)
               for k in ("loop", "single", "rand")}
        summary = {"kind": "summary", "episodes": len(results), "accuracy": acc,
                   "chance": round(1.0 / len(MODES), 3)}
        f.write(json.dumps(summary) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
