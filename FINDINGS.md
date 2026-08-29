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

The decisive control has now been run. With `SELFMODEL_RHO=1.0` (decay fully
off), the loop area held at **0.115** versus **0.126** with decay on —
essentially unchanged. Had the stickiness been mechanical, removing the decay
would have collapsed the loop area toward zero; it did not. The path-dependence
therefore **survives a memoryless filter**, making it an emergent property of the
closed loop rather than filter inertia. This is now the strongest single result
in the repo. (The transition stays *smooth* under both decay settings, so it is
path-dependent memory, not a sharp phase transition.)

## What this replication does and does not establish

**Establishes (on the models tested):**
- a persistent, sensor-fed Bayesian stance model over an interaction;
- a hidden deliberation step that makes the state's content shape behaviour in
  the state-consistent direction, against a structured placebo;
- calibration: the state predicts the system's own reply behaviour;
- hidden-mode inference above chance (though at an honest baseline the gain is
  persistence);
- genuine closed-loop path-dependence, as smooth hysteresis. (An earlier
  revision of this file called the decay-free rerun the decisive control and
  the effect "not an estimator artefact" — the E5b null below revises that:
  roughly two thirds of the raw loop area is accumulator arithmetic, and the
  loop-attributable excess is ~0.06-0.08.)

**Does not establish, and does not claim:**
- any sharp phase transition (E4 is smooth);
- any Ψ measure, threshold crossing, or consciousness property — untested and
  out of scope;
- generality across models — the numbers here come from a small number of
  base models; treat the specific figures as illustrative, the *directions* as
  the finding.

## Open items

1. ~~E4 with `SELFMODEL_RHO=1.0` — the decisive confound control.~~ **Done —
   and superseded.** Loop area held (0.115 vs 0.126), but E5b (below) shows
   decay-off was the wrong decisive control: an undecayed accumulator is
   path-dependent by construction. See the E5/E5b/E6 revision section.
2. E3 at longer transcript lengths (T=10) — does the filter's persistence
   convert into an accuracy gain over the single-shot baseline?
3. E2 replicated across several base models — how model-dependent are the
   calibration and channel effects?
4. A monologue-continuity variant (feeding prior monologues back in) — does
   deliberative memory change any of the above?

## Revision — what kind of memory? (E5, E5b, E6; 2026-08-29)

E4 established path-dependence and framed the decay-free rerun as the decisive
control. Three follow-ups sharpen — and soften — that reading. All at
`SELFMODEL_RHO=1.0`, deepseek-v4-flash.

**E5 (ramp-rate sweep).** Loop area vs turns-per-level K:

| K | 1 | 3 | 6 | 12 |
|---|---|---|---|----|
| loop area | 0.161 | 0.210 | 0.213 | 0.231 |

A lag/viscosity account predicts collapse toward zero as the ramp slows. The
area grows instead: dwelling longer entrenches the state deeper. The memory
is not lag.

**E5b (state-decoupled null — the actual decisive control).** The identical
ramp protocol with a likelihood that ignores the state entirely (no LLM at
all) still yields areas of 0.10–0.15 with the same growth in K
(deterministic null: 0.101 / 0.135 / 0.142 / 0.153). An accumulator at
RHO=1.0 never forgets, so it is path-dependent by construction — which means
E4's "survives decay-off" framing overstated what that rerun showed, and this
file previously repeated the overstatement. The loop-attributable memory is
the excess of E5 over the null: roughly **+0.06 to +0.08 at every K**, not
shrinking as ramps slow. Real at every rate, not lag — but about a third of
the raw area.

**E6 (two-point basin test; clamped push 0.45, N=30).** Started from opposite
dominant modes, trajectories held a ~0.20 gap after 30 turns — but the lower
trajectory was still climbing, so N=30 cannot distinguish two attractors from
slow convergence to one. `results/e6_bistability.json` ships with its
automatic "bistable" verdict, which should be **disregarded**: the stability
criterion passed on slow drift, not on a plateau. An N=100 rerun is in
progress and will land as `results/e6_long.json`.

**Revised claim.** The closed loop adds genuine, rate-independent
path-dependence beyond filter arithmetic, of modest size (~0.07 in
disengaging-mass loop area). Whether that memory amounts to true
bistability — two attractors at identical input — remains open.
