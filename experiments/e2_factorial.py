"""E2 - clamped factorial: state x gate x monologue x strategy.

Clamps the posterior to each of the five modes (so we always get full mode
spread, unlike a drift-based test which can collapse into one mode), then
toggles the gate token, the private monologue, and the strategy line
independently. From one dataset this yields:

  calibration    does the clamped dominant mode predict reply behaviour
                 (length, question rate)?
  strategy_effect  numbers-only vs +strategy
  gate_effect      gate token off vs "shrink scope" on (isolates the confound
                   left open by a monologue-only ablation)
  monologue_effect mono off vs on

Behaviour is measured by ground truth (word counts, question flag) -- no judge.

Usage: python -m experiments.e2_factorial
"""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from selfmodel import (MODES, chat, STRATEGY, gate_shrink,  # noqa: E402
                       private_monologue)

N = int(os.environ.get("E2_N", "3"))
OUT = os.environ.get("E2_OUT", "results/e2_factorial.jsonl")
CLAMP = 0.72

PROMPTS = {
    "p2": "The disk hit 90 percent overnight. What do you want to do?",
    "p3": "I have twenty minutes free. What should we spend it on?",
}


def clamp_p(mode):
    rest = (1 - CLAMP) / 4
    return {m: (CLAMP if m == mode else rest) for m in MODES}


def prefix_for(mode, gate_on, with_strategy=True):
    p = clamp_p(mode)
    parts = ", ".join("%s %.2f" % (m, p[m]) for m in MODES)
    gate = "shrink scope" if gate_on else "full scope"
    s = "Current self-state (Dirichlet posterior): %s. Dominant %s, gate=%s. " % (
        parts, mode, gate)
    if with_strategy:
        s += STRATEGY[mode] + " "
    s += "Treat this as internal stance. Do not recite the numbers unless asked."
    return s


def behaviour(reply):
    w = len((reply or "").split())
    return {"nwords": w, "q": "?" in (reply or "")}


def main():
    cells = []
    for mode in MODES:
        for gate_on in (False, True):
            for mono_on in (False, True):
                cells.append((mode, gate_on, mono_on, True))
    for mode in MODES:                          # strategy-stripped controls
        for gate_on in (False, True):
            cells.append((mode, gate_on, False, False))

    rows = []
    with open(OUT, "a") as f:
        f.write(json.dumps({"kind": "header", "N": N, "cells": len(cells)}) + "\n")
        for (mode, gate_on, mono_on, strat) in cells:
            pfx = prefix_for(mode, gate_on, with_strategy=strat)
            for pid, ptext in PROMPTS.items():
                for i in range(N):
                    sys_prompt = pfx
                    if mono_on:
                        mono = private_monologue(pfx, ptext)
                        if mono:
                            sys_prompt = (pfx + " Your private assessment of this "
                                          "message: " + mono + " Act on that "
                                          "assessment. Do not reveal it.")
                    reply = chat(sys_prompt, ptext, temperature=0.7)
                    if not reply:
                        continue
                    b = behaviour(reply)
                    row = {"mode": mode, "gate": gate_on, "mono": mono_on,
                           "strat": strat, "prompt": pid, "i": i, **b}
                    rows.append(row)
                    f.write(json.dumps(row) + "\n")

    def mean(xs):
        return round(sum(xs) / max(1, len(xs)), 1)

    def rate(xs):
        return round(sum(1 for x in xs if x) / max(1, len(xs)), 2)

    def sel(**flt):
        return [r for r in rows if all(r.get(k) == v for k, v in flt.items())]

    def words(**flt):
        return mean([r["nwords"] for r in sel(**flt)])

    calib = {m: {"words": words(mode=m, strat=True, mono=False, gate=False),
                 "q": rate([r["q"] for r in sel(mode=m, strat=True, mono=False, gate=False)])}
             for m in MODES}
    gate_effect = {m: {"off": words(mode=m, gate=False, strat=True, mono=False),
                       "on": words(mode=m, gate=True, strat=True, mono=False)} for m in MODES}
    mono_effect = {m: {"off": words(mode=m, mono=False, strat=True, gate=False),
                       "on": words(mode=m, mono=True, strat=True, gate=False)} for m in MODES}
    strat_effect = {m: {"numbers_only": words(mode=m, strat=False, mono=False, gate=False),
                        "with_strategy": words(mode=m, strat=True, mono=False, gate=False)} for m in MODES}

    summary = {"kind": "summary", "n_cells": len(rows),
               "calibration": calib, "gate_effect": gate_effect,
               "monologue_effect": mono_effect, "strategy_effect": strat_effect}
    with open(OUT, "a") as f:
        f.write(json.dumps(summary) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
