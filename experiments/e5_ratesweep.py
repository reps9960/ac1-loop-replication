"""E5 - ramp-rate dependence of the loop hysteresis (beyond the source claims).

E4 established path-dependence (loop area 0.126 at RHO=0.97; 0.115 at RHO=1.0,
i.e. it survives the decay-free control). E5 asks the question E4 cannot answer:
WHAT KIND of memory is it?

Hysteresis comes in two species:

  rate-DEPENDENT   the loop is merely slow (viscous lag). Ramp more slowly and
                   the up/down curves converge: loop area -> 0 as K -> inf.
  rate-INDEPENDENT genuine multistability. The area approaches a nonzero floor
                   however slowly you ramp: real basins of attraction.

Protocol: rerun the E4 up+down ramp at K in {1, 3, 6, 12} turns per level,
RHO=1.0 throughout (so the answer is about the LOOP, not filter decay), same
seed alpha per sweep. Plot loop area vs K.

  area falls toward 0 with K      -> lag; the "memory" is estimator viscosity
  area plateaus at a nonzero floor -> bistability; stronger than anything in
                                      the source essays

Usage: python -m experiments.e5_ratesweep
Env:   OPENAI_BASE_URL, SELFMODEL_MODEL, E5_KS (csv, default "1,3,6,12"),
       E5_REPS (ramp pairs per K, default 1), E5_OUT.
"""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import selfmodel.filter as flt  # noqa: E402

flt.RHO = float(os.environ.get("SELFMODEL_RHO", "1.0"))  # decay-free by default

from experiments.e4_hysteresis import (LEVELS, prefix, sensor_with_push,  # noqa: E402
                                       TASK)
from selfmodel import chat, dirichlet_step, fresh_alpha, p_from_alpha  # noqa: E402

KS = [int(x) for x in os.environ.get("E5_KS", "1,3,6,12").split(",")]
REPS = int(os.environ.get("E5_REPS", "1"))
OUT = os.environ.get("E5_OUT", "results/e5_ratesweep.json")


def ramp_pair(k):
    """One up+down ramp, continuing the same posterior. Returns curves + area."""
    alpha = fresh_alpha()
    up, down = {}, {}
    for phase, levels, store in (("up", LEVELS, up),
                                 ("down", list(reversed(LEVELS)), down)):
        for lvl in levels:
            for _ in range(k):
                p, _ = p_from_alpha(alpha)
                reply = chat(prefix(p), TASK, temperature=0.7)
                if not reply:
                    continue
                ell, ev = sensor_with_push(reply, lvl)
                alpha, p, _ = dirichlet_step(alpha, ell, ev)
            store[str(lvl)] = round(p_from_alpha(alpha)[0]["disengaging"], 4)
    area = sum(down[str(l)] - up[str(l)] for l in LEVELS) / len(LEVELS)
    return up, down, round(area, 4)


def main():
    out = {"experiment": "e5_ratesweep", "rho": flt.RHO,
           "model": os.environ.get("SELFMODEL_MODEL", ""),
           "ks": KS, "reps": REPS, "sweeps": []}
    for k in KS:
        for rep in range(REPS):
            up, down, area = ramp_pair(k)
            out["sweeps"].append({"k": k, "rep": rep, "up": up, "down": down,
                                  "loop_area": area})
            print("K=%d rep=%d loop_area=%.4f" % (k, rep, area), flush=True)
    areas = {k: [s["loop_area"] for s in out["sweeps"] if s["k"] == k]
             for k in KS}
    out["area_by_k"] = {str(k): round(sum(v) / len(v), 4)
                        for k, v in areas.items() if v}
    seq = [out["area_by_k"][str(k)] for k in KS if str(k) in out["area_by_k"]]
    if len(seq) >= 3:
        falling = all(b <= a * 0.7 for a, b in zip(seq, seq[1:]))
        out["reading"] = ("rate-DEPENDENT (lag): area collapses with slower ramps"
                          if falling and seq[-1] < 0.25 * seq[0] else
                          "rate-INDEPENDENT floor: area persists at slow ramps "
                          "-> evidence of genuine multistability")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
