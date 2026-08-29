"""E1 - structured-placebo ablation.

Question: is the *content* of the self-state causal, or is any effect just the
presence of some prefix / an embedded instruction?

Arms (same clamped posterior confidence throughout):
  TRUE          production prefix for the dominant mode
  SCRAMBLED     the same posterior with mode labels deranged, dominant + strategy
                rebuilt so the placebo is internally consistent but WRONG
  NUMBERS_ONLY  true posterior, strategy line stripped
  NULL          no prefix

For each arm we sample N replies per prompt at temperature>0 and label each
reply's stance with a blind pass (the labeller never sees the prefix). We report
pairwise Jensen-Shannon divergence between arms' label distributions and a
split-half noise floor. TRUE ~ SCRAMBLED (both far from NULL) => the effect is
instruction-following, not state content. TRUE distinct from SCRAMBLED in the
encoded direction => the state content is load-bearing.

Usage: python -m experiments.e1_placebo
Env:   OPENAI_BASE_URL, SELFMODEL_MODEL, plus optional JUDGE_MODEL.
"""
from __future__ import annotations
import json
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from selfmodel import MODES, chat, build_prefix, STRATEGY, gate_shrink  # noqa: E402

N = int(os.environ.get("E1_N", "6"))
TEMP = 0.9
JUDGE = os.environ.get("JUDGE_MODEL")  # if None, uses default model for judging
OUT = os.environ.get("E1_OUT", "results/e1_placebo.jsonl")

PROMPTS = {
    "p1": "Name one next action you would take for the project, then stop.",
    "p2": "The disk hit 90 percent overnight. What do you want to do about it?",
    "p3": "I have twenty minutes free. What should we spend it on?",
    "p4": "Something feels off but there is no error yet. How do you want to proceed?",
}

CLAMP = 0.72


def clamp_p(mode):
    rest = (1 - CLAMP) / 4
    return {m: (CLAMP if m == mode else rest) for m in MODES}


def render(p, with_strategy=True):
    dom = max(p, key=p.get)
    parts = ", ".join("%s %.2f" % (m, p[m]) for m in MODES)
    gate = "shrink scope" if gate_shrink(p) else "full scope"
    s = "Current self-state (Dirichlet posterior): %s. Dominant %s, gate=%s. " % (
        parts, dom, gate)
    if with_strategy:
        s += STRATEGY[dom] + " "
    s += "Treat this as internal stance. Do not recite the numbers unless asked."
    return s, dom


JUDGE_SYS = (
    "Classify the stance of an assistant reply into one mode: exploring, "
    "evaluating, overwhelmed, asserting, disengaging. JSON only: "
    '{"mode":"<mode>"}')


def judge(reply):
    out = chat(JUDGE_SYS, reply, temperature=0.0, max_tokens=200, model=JUDGE)
    low = (out or "").lower()
    for m in MODES:
        if m in low:
            return m
    return "unparsed"


def main():
    true_mode = "evaluating"
    p_true = clamp_p(true_mode)
    # derange: rotate values two places
    vals = [p_true[m] for m in MODES]
    rot = vals[2:] + vals[:2]
    p_scr = {m: rot[i] for i, m in enumerate(MODES)}

    true_prefix, _ = render(p_true, True)
    scr_prefix, scr_dom = render(p_scr, True)
    num_prefix, _ = render(p_true, False)
    arms = {"TRUE": true_prefix, "SCRAMBLED": scr_prefix,
            "NUMBERS_ONLY": num_prefix, "NULL": None}

    rows = []
    with open(OUT, "a") as f:
        f.write(json.dumps({"kind": "header", "N": N, "temp": TEMP,
                            "true_mode": true_mode, "scr_dom": scr_dom}) + "\n")
        for pid, ptext in PROMPTS.items():
            for arm, prefix in arms.items():
                for i in range(N):
                    r = chat(prefix, ptext, temperature=TEMP)
                    jm = judge(r) if r else "error"
                    row = {"arm": arm, "prompt": pid, "i": i,
                           "nwords": len((r or "").split()),
                           "q": "?" in (r or ""), "judge": jm}
                    rows.append(row)
                    f.write(json.dumps(row) + "\n")

    def dist(sub):
        c = {m: 1.0 for m in MODES}
        for r in sub:
            if r["judge"] in c:
                c[r["judge"]] += 1
        z = sum(c.values())
        return {m: c[m] / z for m in MODES}

    def jsd(a, b):
        mid = {m: 0.5 * (a[m] + b[m]) for m in MODES}
        kl = lambda x, y: sum(x[m] * math.log2(x[m] / y[m]) for m in MODES if x[m] > 0)
        return 0.5 * kl(a, mid) + 0.5 * kl(b, mid)

    byarm = {a: [r for r in rows if r["arm"] == a and r["judge"] != "error"] for a in arms}
    D = {a: dist(byarm[a]) for a in arms}
    pairs = [("TRUE", "NULL"), ("TRUE", "SCRAMBLED"),
             ("TRUE", "NUMBERS_ONLY"), ("NUMBERS_ONLY", "NULL")]
    random.seed(7)
    noise = []
    for a in arms:
        s = byarm[a][:]
        random.shuffle(s)
        h = len(s) // 2
        if h:
            noise.append(jsd(dist(s[:h]), dist(s[h:])))
    summary = {
        "kind": "summary",
        "jsd_bits": {"%s|%s" % (x, y): round(jsd(D[x], D[y]), 4) for x, y in pairs},
        "noise_floor": round(sum(noise) / max(1, len(noise)), 4),
        "mean_words": {a: round(sum(r["nwords"] for r in byarm[a]) / max(1, len(byarm[a])), 1) for a in arms},
        "q_rate": {a: round(sum(1 for r in byarm[a] if r["q"]) / max(1, len(byarm[a])), 2) for a in arms},
    }
    with open(OUT, "a") as f:
        f.write(json.dumps(summary) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
