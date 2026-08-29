"""E6 - direct two-point basin test at clamped input (beyond the source claims).

E5 classifies the hysteresis by ramp rate; E6 tests bistability directly and
independently. Clamp the external push at a fixed mid-ramp value and start the
SAME loop from two different initial posteriors:

  init A: dominant "exploring"    (engaged basin, if one exists)
  init B: dominant "disengaging"  (withdrawn basin, if one exists)

Run each forward N turns at identical input, RHO=1.0. Then:

  trajectories converge to one level  -> single attractor (any hysteresis is lag)
  trajectories hold separated levels  -> two attractors at the same input:
                                         bistability, demonstrated directly

Separation criterion: mean |disengaging_A - disengaging_B| over the last
TAIL turns > GAP (default 0.10), with both trajectories individually stable
(tail std < 0.05).

Usage: python -m experiments.e6_bistability
Env:   OPENAI_BASE_URL, SELFMODEL_MODEL, E6_PUSH (default 0.45), E6_N (default
       30), E6_SEEDS (pairs, default 2), E6_OUT.
"""
from __future__ import annotations
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import selfmodel.filter as flt  # noqa: E402

flt.RHO = float(os.environ.get("SELFMODEL_RHO", "1.0"))

from experiments.e4_hysteresis import prefix, sensor_with_push, TASK  # noqa: E402
from selfmodel import (MODES, chat, dirichlet_step, fresh_alpha,  # noqa: E402
                       p_from_alpha)

PUSH = float(os.environ.get("E6_PUSH", "0.45"))
N = int(os.environ.get("E6_N", "30"))
SEEDS = int(os.environ.get("E6_SEEDS", "2"))
TAIL = max(5, N // 3)
GAP = 0.10
OUT = os.environ.get("E6_OUT", "results/e6_bistability.json")


def seeded_alpha(dominant, mass=0.6, kappa=12.0):
    rest = (1.0 - mass) / (len(MODES) - 1)
    return {m: (mass if m == dominant else rest) * kappa for m in MODES}


def run_clamped(alpha):
    traj = []
    for _ in range(N):
        p, _ = p_from_alpha(alpha)
        reply = chat(prefix(p), TASK, temperature=0.7)
        if not reply:
            continue
        ell, ev = sensor_with_push(reply, PUSH)
        alpha, p, _ = dirichlet_step(alpha, ell, ev)
        traj.append(round(p["disengaging"], 4))
    return traj


def main():
    out = {"experiment": "e6_bistability", "rho": flt.RHO, "push": PUSH,
           "n_turns": N, "model": os.environ.get("SELFMODEL_MODEL", ""),
           "pairs": []}
    verdicts = []
    for s in range(SEEDS):
        a = run_clamped(seeded_alpha("exploring"))
        b = run_clamped(seeded_alpha("disengaging"))
        ta, tb = a[-TAIL:], b[-TAIL:]
        gap = round(abs(statistics.mean(ta) - statistics.mean(tb)), 4)
        stable = (statistics.pstdev(ta) < 0.05 and statistics.pstdev(tb) < 0.05)
        bistable = bool(gap > GAP and stable)
        verdicts.append(bistable)
        out["pairs"].append({"seed_pair": s, "traj_from_exploring": a,
                             "traj_from_disengaging": b, "tail_gap": gap,
                             "tail_stable": stable, "bistable": bistable})
        print("pair=%d gap=%.4f stable=%s bistable=%s" % (s, gap, stable,
                                                          bistable), flush=True)
    out["reading"] = ("BISTABLE: separated stable attractors at identical input"
                      if all(verdicts) and verdicts else
                      "MONOSTABLE: trajectories converge -> single attractor; "
                      "any hysteresis is lag, not multistability")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
