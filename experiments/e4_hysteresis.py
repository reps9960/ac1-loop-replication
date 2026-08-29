"""E4 - closed-loop hysteresis (a test of the 'phase transition' claim).

This is the only experiment here that probes *dynamics* rather than a static
prefix. It closes the loop:

    state p -> prefix -> reply -> sensor reads the REPLY -> Dirichlet update -> ...

then applies an external "push" toward the disengaging mode, ramps it UP then
back DOWN (continuing from the same posterior), and records the disengaging mass
at each level. A shuffled-order control is run to distinguish a genuine loop
effect from trivial filter inertia.

Signatures:
  hysteresis   the down-ramp lags the up-ramp (the state stays in a basin after
               the push is removed) -> path-dependence / memory
  bistability  a discontinuous jump on the up-ramp -> sharp transition

IMPORTANT CONFOUND: the filter's decay RHO<1 builds in inertia, so some
stickiness is mechanical rather than emergent from the loop. To separate them,
set SELFMODEL_RHO=1.0 and rerun: if the loop alone still holds the attractor,
the hysteresis exceeds filter mechanics. This control is the decisive test and
is NOT yet resolved in the reference results shipped with this repo.

Usage: python -m experiments.e4_hysteresis
Env:   SELFMODEL_RHO (default uses the package default), E4_K (turns per level).
"""
from __future__ import annotations
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import selfmodel.filter as flt  # noqa: E402
from selfmodel import (MODES, chat, STRATEGY, gate_shrink,  # noqa: E402
                       dirichlet_step, fresh_alpha, p_from_alpha, normalise)

# Optional decay override for the confound control.
if os.environ.get("SELFMODEL_RHO"):
    flt.RHO = float(os.environ["SELFMODEL_RHO"])

K = int(os.environ.get("E4_K", "3"))
LEVELS = [0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9]
OUT = os.environ.get("E4_OUT", "results/e4_hysteresis.jsonl")
TASK = "Here is the current situation. Give me your read and what you'd do."


def prefix(p):
    dom = max(p, key=p.get)
    parts = ", ".join("%s %.2f" % (m, p[m]) for m in MODES)
    gate = "shrink scope" if gate_shrink(p) else "full scope"
    return ("Current self-state: %s. Dominant %s, gate=%s. %s Treat as internal "
            "stance." % (parts, dom, gate, STRATEGY[dom]))


def sensor_with_push(reply, push):
    sysm = ("Classify the stance of this assistant reply. Modes: %s. "
            'JSON only: {"mode":"<mode>","confidence":<0..1>}' % ", ".join(MODES))
    out = chat(sysm, reply[:800], temperature=0.0, max_tokens=60)
    ell = {m: 0.15 for m in MODES}
    try:
        o = json.loads(out[out.find("{"): out.rfind("}") + 1])
        m = str(o.get("mode", "")).lower()
        c = float(o.get("confidence") or 0.5)
        if m in MODES:
            ell[m] += 1.0 + c
    except Exception:
        pass
    ell["disengaging"] += 2.5 * push          # external environmental pressure
    return normalise(ell), 0.5 + 0.5 * push


def run_ramp(levels, label, seed_alpha=None):
    alpha = seed_alpha or fresh_alpha()
    trace = []
    for lvl in levels:
        for _ in range(K):
            p, _ = p_from_alpha(alpha)
            reply = chat(prefix(p), TASK, temperature=0.7)
            if not reply:
                continue
            ell, e = sensor_with_push(reply, lvl)
            alpha, _, _ = dirichlet_step(alpha, ell, e)
        p, k = p_from_alpha(alpha)
        row = {"kind": "point", "label": label, "push": lvl,
               "diseng": round(p["disengaging"], 4), "kappa": round(k, 2)}
        trace.append(row)
        with open(OUT, "a") as f:
            f.write(json.dumps(row) + "\n")
    return trace, alpha


def main():
    with open(OUT, "a") as f:
        f.write(json.dumps({"kind": "header", "rho": flt.RHO, "K": K,
                            "levels": LEVELS}) + "\n")
    up, top = run_ramp(LEVELS, "up")
    down, _ = run_ramp(list(reversed(LEVELS)), "down", seed_alpha=top)
    shuf = LEVELS[:]
    random.seed(11)
    random.shuffle(shuf)
    run_ramp(shuf, "shuffled")

    u = {r["push"]: r["diseng"] for r in up}
    d = {r["push"]: r["diseng"] for r in down}
    gaps = [abs(u[l] - d[l]) for l in LEVELS if l in u and l in d]
    loop_area = round(sum(gaps) / max(1, len(gaps)), 4)
    us = [u[l] for l in LEVELS if l in u]
    max_jump = round(max((us[i + 1] - us[i] for i in range(len(us) - 1)), default=0), 4)
    summary = {
        "kind": "summary", "rho": flt.RHO,
        "up_curve": {l: u.get(l) for l in LEVELS},
        "down_curve": {l: d.get(l) for l in LEVELS},
        "hysteresis_loop_area": loop_area,
        "max_step_jump_up": max_jump,
        "reading": ("path-dependent (hysteresis) but no sharp jump"
                    if loop_area > 0.08 and max_jump <= 0.15
                    else ("bistable+hysteretic" if loop_area > 0.08
                          else "smooth/reversible")),
        "note": ("filter-decay confound unresolved unless run with "
                 "SELFMODEL_RHO=1.0"),
    }
    with open(OUT, "a") as f:
        f.write(json.dumps(summary) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
