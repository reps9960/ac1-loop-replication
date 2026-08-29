"""E5b - state-decoupled null model for the ramp hysteresis (no LLM).

The decisive control for "is the hysteresis a LOOP property?". E4's decay-free
rerun (RHO=1.0) was framed as that control, but it is the wrong one: removing
decay does not remove mechanical path-dependence from the estimator -- it
maximises it, because an accumulator that never forgets is path-dependent by
construction.

The right null: run the IDENTICAL ramp protocol with a likelihood that does not
depend on the state at all. No LLM, no reply, no sensor -- the per-turn
evidence is a state-independent hit plus the same push term. Any hysteresis
this produces is pure filter arithmetic. The loop's real contribution is the
EXCESS of the measured E5 areas over this null.

Result shipped with this repo: the null reproduces both a substantial area
(0.10-0.15) and its growth with K. The measured E5 areas exceed the null by
roughly +0.06 to +0.08 at every K. That excess -- not the raw area -- is the
loop-borne memory.

Runs in seconds; no endpoint required.

Usage: python -m experiments.e5b_null
Env:   E5B_KS (default "1,3,6,12"), E5B_TRIALS (noisy trials, default 3),
       E5B_OUT.
"""
from __future__ import annotations
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import selfmodel.filter as flt  # noqa: E402

flt.RHO = float(os.environ.get("SELFMODEL_RHO", "1.0"))

from experiments.e4_hysteresis import LEVELS  # noqa: E402
from selfmodel import (MODES, dirichlet_step, fresh_alpha, normalise,  # noqa: E402
                       p_from_alpha)

KS = [int(x) for x in os.environ.get("E5B_KS", "1,3,6,12").split(",")]
TRIALS = int(os.environ.get("E5B_TRIALS", "3"))
OUT = os.environ.get("E5B_OUT", "results/e5b_null.json")


def null_likelihood(push, mode_hit=None):
    """Same arithmetic as sensor_with_push, minus any dependence on the reply.

    mode_hit=None spreads an average-strength hit evenly (deterministic null);
    a mode name concentrates the hit there (noisy null draws it at random).
    """
    ell = {m: 0.15 for m in MODES}
    if mode_hit is None:
        for m in MODES:
            ell[m] += 1.5 / len(MODES)
    else:
        ell[mode_hit] += 1.5
    ell["disengaging"] += 2.5 * push
    return normalise(ell), 0.5 + 0.5 * push


def ramp_pair(k, rng=None):
    alpha = fresh_alpha()
    up, down = {}, {}
    for levels, store in ((LEVELS, up), (list(reversed(LEVELS)), down)):
        for lvl in levels:
            for _ in range(k):
                hit = rng.choice(MODES) if rng else None
                ell, ev = null_likelihood(lvl, hit)
                alpha, p, _ = dirichlet_step(alpha, ell, ev)
            store[str(lvl)] = round(p_from_alpha(alpha)[0]["disengaging"], 4)
    area = sum(down[str(l)] - up[str(l)] for l in LEVELS) / len(LEVELS)
    return up, down, round(area, 4)


def main():
    out = {"experiment": "e5b_null", "rho": flt.RHO, "ks": KS,
           "deterministic": {}, "noisy_trials": []}
    for k in KS:
        _, _, area = ramp_pair(k)
        out["deterministic"][str(k)] = area
    rng = random.Random(7)
    for t in range(TRIALS):
        out["noisy_trials"].append({str(k): ramp_pair(k, rng)[2] for k in KS})
    out["reading"] = ("A state-decoupled accumulator at RHO=%.2f produces "
                      "substantial, K-growing hysteresis on its own. Only the "
                      "excess of measured loop areas over this null is "
                      "attributable to the closed loop." % flt.RHO)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps(out["deterministic"]))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
