"""State -> prompt injection.

Two injection points from the AC1 design:

  build_prefix(p)         renders the posterior into a system-prompt fragment,
                          optionally with a per-mode "strategy" instruction line
                          and a gate flag.

  private_monologue(...)  the hidden deliberation step: a separate generation,
                          conditioned on the prefix, that privately assesses how
                          the current stance should shape the reply. Its output
                          is prepended to the reply's system prompt but never
                          shown to the user.

Keeping strategy line and gate as toggles matters: the experiments in this repo
show they are separable causal channels, so a faithful reimplementation must be
able to switch each independently.
"""
from __future__ import annotations

from .filter import MODES
from .sensor import chat

STRATEGY = {
    "exploring": "Ask one precise question; do not close the topic.",
    "evaluating": "Answer the decision if one was asked; name the criterion; do not open a new thread.",
    "overwhelmed": "Isolate the single sticking point; drop the extra threads.",
    "asserting": "Give one concrete next action, then stop.",
    "disengaging": "One short close; propose no new work.",
}


def gate_shrink(p: dict) -> bool:
    return p.get("overwhelmed", 0) >= 0.5 or p.get("disengaging", 0) >= 0.45


def build_prefix(p: dict, with_strategy: bool = True,
                 with_gate: bool = True) -> str:
    dom = max(p, key=p.get)
    parts = ", ".join("%s %.2f" % (m, p[m]) for m in MODES)
    s = "Current self-state (Dirichlet posterior): %s. Dominant %s" % (parts, dom)
    if with_gate:
        s += ", gate=%s" % ("shrink scope" if gate_shrink(p) else "full scope")
    s += ". "
    if with_strategy:
        s += STRATEGY[dom] + " "
    s += "Treat this as internal stance. Do not recite the numbers unless asked."
    return s


MONOLOGUE_ASK = (
    "Before replying, privately assess how your current stance should shape your "
    "approach to this specific message. 2-4 sentences. The user will never see this."
)


def private_monologue(prefix: str, user_text: str,
                      model: str | None = None) -> str:
    """Hidden deliberation. Returns '' on failure (caller proceeds without it)."""
    if not prefix or not (user_text or "").strip():
        return ""
    out = chat(prefix + "\n" + MONOLOGUE_ASK, str(user_text)[:1200],
               temperature=0.4, max_tokens=220, model=model)
    return out[:900]
