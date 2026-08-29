# Findings

A longer, honest narrative of what this replication found. The short version is
in the README table; this file records the reasoning, the corrections we made to
our own earlier conclusions, and the limitations.

## 1. The state content is causal — but the monologue is what makes it so

Our first ablation (E1) used a *weakly* held posterior — the kind the filter
settles into from a few lines of organic evidence. Under that condition:

- a true state prefix and a **scrambled** one (same format, deranged mode
  values, internally consistent wrong strategy) were **indistinguishable** on the
  blind label channel;
- a **numbers-only** prefix (state values, no strategy line) collapsed onto the
  **null** (no prefix) condition on every channel.

The honest read of E1 alone is deflationary: at low confidence the *strategy
line* — an imperative sentence — does the visible work, and the model follows it
whether the state behind it is true or deranged. The posterior values by
themselves look inert.

E2 corrects this. When the posterior is **clamped** to a strong value (0.72
dominant), the picture changes:

- **numbers-only** prefixes produce long, unshaped replies (150–200 words)
  that differ sharply from strategy-bearing prefixes (46–133 words). So the
  numbers are **not** universally inert — at high confidence they move
  behaviour; the strategy line then *disciplines* that behaviour.
- the clamped mode **predicts** reply behaviour: exploring → short + always a
  question; asserting → short + direct; the more deliberative modes run long.
  This is calibration: the self-state carries real information about the reply
  the system will produce.

The correction matters: "bare state numbers are inert" is **not** a general
truth about the loop — it is an artefact of weak state. Anyone reproducing E1
without E2 would draw the wrong conclusion.

The clearest causal channel throughout is the **private monologue**. In a
companion two-stage variant (monologue then reply, on a non-reasoning base so the
monologue is the only deliberation), true / scrambled / null states produced
reply lengths of ~131 / ~47 / ~79 words — opposite-signed departures from null in
the state-consistent direction. Chained with the numbers-only-≈-null result, the
attribution is clean: **the hidden monologue is the step at which the state's
content becomes behaviourally load-bearing.** This is exactly the essays' own
claim that the prefix alone is insufficient without a deliberation step — and it
reproduces here, with a structured-placebo control the essays do not report.

## 2. The gate token is a real but minor, non-uniform channel

E2 isolates the gate flag ("shrink scope" vs "full scope") with strategy and
monologue held fixed. It moves reply length, but modestly and **not uniformly** —
some modes shorten, others lengthen. So the gate is a genuine secondary channel,
not the main driver of the mode effects, and it does not explain them away. This
resolves a confound left open by any monologue-only ablation, where the gate
token rides along inside the prefix.

## 3. Hidden-mode inference works — against an honest baseline the gain is
persistence, not accuracy

E3 scores three predictors against ground truth on a hidden-mode game. The loop
reaches 0.60, the random baseline 0.233 (chance 0.20) — 3× chance, real signal.

But the honest single-shot baseline — a plain LLM reading the whole transcript —
**also** reaches 0.60. On a three-line task the filter therefore buys
**persistence / accumulated state**, not raw accuracy; both methods likely sit at
the evidence ceiling of that transcript length. Longer episodes would separate
them if anything does.

The methodological point worth flagging: a bare LLM is **not at chance** on this
task. Reporting a chance-level baseline would inflate the apparent gain from the
loop. We report the honest baseline, and the honest baseline ties the loop.

## 4. The closed loop has memory — as hysteresis, not a sharp transition

E4 is the only experiment that probes *dynamics*. Closing the loop and ramping an
external push toward disengagement up then down:

- the down-ramp sits far above the up-ramp at every level (loop area 0.126);
- pushed to disengagement at push 0.9 (0.385), the state returns to only 0.382
  when the push is removed — it **stays** in the basin;
- but the up-ramp rises **smoothly** (max single-step jump 0.05) — there is no
  discontinuous jump.

So: **strong path-dependence, no sharp bistability.** The loop has a
self-reinforcing attractor — the "memory" half of a phase-transition claim,
demonstrated on live hardware — but the entry is gradual, i.e. softer than a
first-order transition. A hysteresis loop without a clean jump.

### The unresolved confound

The filter's decay (`RHO = 0.97`) builds intrinsic inertia into the posterior,
so part of the stickiness is mechanical, not emergent from the loop. A shuffled
control (same push levels, random order) stayed roughly monotonic, which is
*weak* evidence the ordered hysteresis exceeds pure filter decay — but weak, not
decisive.

The clean test is a decay-free rerun (`SELFMODEL_RHO=1.0`). If the loop still
holds the attractor with no decay, the hysteresis is a genuine loop effect. **We
have not run this yet.** Until it is run, E4 is *suggestive of* loop-level
path-dependence, not proof of it. This is the single most important open item in
the repo.

## What this replication does and does not establish

**Establishes (on the models tested):**
- a persistent, sensor-fed Bayesian stance model over an interaction;
- a hidden deliberation step that makes the state's content shape behaviour in
  the state-consistent direction, against a structured placebo;
- calibration: the state predicts the system's own reply behaviour;
- hidden-mode inference above chance (though at an honest baseline the gain is
  persistence);
- genuine closed-loop path-dependence, as smooth hysteresis.

**Does not establish, and does not claim:**
- any sharp phase transition (E4 is smooth);
- any Ψ measure, threshold crossing, or consciousness property — untested and
  out of scope;
- generality across models — the numbers here come from a small number of
  base models; treat the specific figures as illustrative, the *directions* as
  the finding.

## Open items

1. **E4 with `SELFMODEL_RHO=1.0`** — the decisive confound control. Highest
   priority.
2. E3 at longer transcript lengths (T=10) — does the filter's persistence
   convert into an accuracy gain over the single-shot baseline?
3. E2 replicated across several base models — how model-dependent are the
   calibration and channel effects?
4. A monologue-continuity variant (feeding prior monologues back in) — does
   deliberative memory change any of the above?
