"""Dirichlet belief tracker over a fixed set of stance modes.

A clean-room reimplementation of the belief-tracking component described in the
AC1-LLM / Laflamme-3T essays (Laflamme, 2026): a Bayesian posterior over a small
set of interaction "modes", updated online from per-turn evidence. This module
contains no dependency on any particular hosting environment; it is a plain
estimator you can drive from any evidence source.

The five modes are a design choice, not a claim; swap MODES to taste.
"""
from __future__ import annotations

MODES = ["exploring", "evaluating", "overwhelmed", "asserting", "disengaging"]

# Update hyperparameters. RHO < 1 gives the posterior a finite memory (older
# evidence decays); STEP_CAP bounds how far one observation can move the mean;
# the alpha floor and kappa cap keep the posterior from collapsing or freezing.
RHO = 0.97
STEP_CAP = 0.12
ALPHA_MIN = 0.35
KAPPA_MAX = 48.0
EVIDENCE_MAX = 1.15


def normalise(d: dict) -> dict:
    z = sum(max(0.0, v) for v in d.values()) or 1.0
    return {k: max(0.0, v) / z for k, v in d.items()}


def alpha_from_p(p: dict, kappa: float) -> dict:
    p = normalise(p)
    return {m: p.get(m, 0.0) * kappa for m in MODES}


def p_from_alpha(alpha: dict):
    k = sum(alpha.values()) or 1.0
    return {m: alpha[m] / k for m in MODES}, k


def dirichlet_step(alpha: dict, likelihood: dict, evidence: float):
    """One online update.

    alpha:      current Dirichlet parameters (dict over MODES)
    likelihood: normalised per-mode likelihood from a sensor (dict over MODES)
    evidence:   scalar strength of this observation (0..EVIDENCE_MAX)

    Returns (new_alpha, new_p, new_kappa).
    """
    evidence = max(0.0, min(EVIDENCE_MAX, float(evidence)))
    ell = normalise(likelihood)

    # decay + additive evidence
    new_alpha = {m: RHO * alpha.get(m, ALPHA_MIN) + evidence * ell[m] for m in MODES}

    # floor
    for m in MODES:
        new_alpha[m] = max(ALPHA_MIN, new_alpha[m])

    # kappa cap (rescale if the posterior is getting too confident/frozen)
    k = sum(new_alpha.values())
    if k > KAPPA_MAX:
        s = KAPPA_MAX / k
        new_alpha = {m: new_alpha[m] * s for m in MODES}

    # step cap on the mean: don't let one observation move p by more than STEP_CAP (L1/2)
    old_p, _ = p_from_alpha(alpha)
    new_p, new_k = p_from_alpha(new_alpha)
    move = sum(abs(new_p[m] - old_p[m]) for m in MODES) / 2.0
    if move > STEP_CAP and move > 0:
        t = STEP_CAP / move
        blended = {m: old_p[m] + t * (new_p[m] - old_p[m]) for m in MODES}
        new_alpha = alpha_from_p(blended, new_k)
        new_p, new_k = p_from_alpha(new_alpha)

    return new_alpha, new_p, new_k


def fresh_alpha(kappa: float = 8.0) -> dict:
    """A flat, low-confidence starting posterior."""
    return alpha_from_p({m: 1.0 / len(MODES) for m in MODES}, kappa)
