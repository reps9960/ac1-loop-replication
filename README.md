# A Controlled Replication of the AC1 Self-Model Loop

An independent, from-scratch reimplementation of the self-model loop described
in Lark Laflamme's *AC1-LLM / Laflamme-3T* essays (2026), built to test the
loop's behavioural claims under controls the original write-ups do not report.

This repository is **replication, not rebuttal**. The architecture is
Laflamme's; the essays are clear enough to rebuild from, which is rare and worth
saying. What is added here is a set of controls — structured placebos, clamped
factorials, honest baselines, and a closed-loop dynamics probe — that let each
claim be tested rather than asserted. Where a claim holds, this repo says so.
Where it holds only in a softer form, or has an unresolved confound, this repo
says that too.

**Scope.** This project is strictly about the *measurable behaviour* of the
loop. It makes **no** claim about the Ψ-threshold, consciousness, or the wider
Laflamme-3T conjecture; those questions are out of scope and untouched by these
experiments.

## The loop

```
state p  ──►  prefix  ──►  reply  ──►  sensor reads the reply  ──►  Dirichlet update  ──►  …
```

- **Belief tracker** (`selfmodel/filter.py`): a Dirichlet posterior over five
  stance modes — exploring, evaluating, overwhelmed, asserting, disengaging —
  updated online with decay, a step cap, an evidence floor and a confidence cap.
- **Sensor** (`selfmodel/sensor.py`): an LLM classifies each line into a mode +
  confidence, mapped to a per-mode likelihood. Includes a `reasoning_content`
  fallback (see Reproducing, below).
- **Prefix** (`selfmodel/prefix.py`): the posterior is rendered into a
  system-prompt fragment, with an optional per-mode *strategy* line and a *gate*
  flag as independently toggleable channels.
- **Private monologue** (`selfmodel/prefix.py`): a hidden generation, conditioned
  on the prefix, that privately assesses how the stance should shape the reply.
  Prepended to the reply's prompt, never shown to the user.

## Experiments and results

| # | Tests | Result |
|---|-------|--------|
| **E1** placebo | Is the *content* of the state causal, or just the presence of a prefix / an embedded instruction? | Under a **weak** posterior: TRUE ≈ SCRAMBLED, NUMBERS_ONLY ≈ NULL. The strategy *line* carries the visible effect, not the numbers — at low confidence. |
| **E2** factorial | State × gate × monologue × strategy, clamped to each mode. Calibration + confound isolation. | Under a **strong** clamped posterior the mode **predicts** reply behaviour (calibration holds). Strategy line disciplines strongly; gate token is a minor, non-uniform channel; monologue sharpens state-consistent behaviour. **Corrects E1**: bare state numbers are *not* universally inert — that was a weak-state artefact. |
| **E3** modegame | Hidden-mode inference vs **honest** baselines, ground-truth scored. | Loop **0.60**, honest single-shot LLM **0.60**, random **0.233** (chance 0.20). The loop infers a hidden mode at 3× chance; it *ties* the honest baseline, so on short evidence the filter buys persistence, not raw accuracy. A bare LLM is **not** at chance here. |
| **E4** hysteresis | The "phase transition" claim, on the live closed loop. | **Strong hysteresis** (loop area 0.126) but **no sharp jump** (max step 0.05). The state stays in the disengagement basin after the push is removed — real path-dependent memory — but the entry is gradual. Softer than a sharp first-order transition. **Confound resolved**: survives a decay-free (ρ=1.0) rerun (see below). |

Full numbers with per-run notes are in [`results/`](results/); the narrative is
in [`FINDINGS.md`](FINDINGS.md).

## Headline

Every claim tested reproduces in a **true-but-softer** form once the missing
controls are added:

- the self-state is causally load-bearing on behaviour — **most clearly through
  the private monologue**, and only once the posterior is confident;
- the loop carries real predictive information about stance (calibration);
- hidden-mode inference works, but against an honest baseline the gain is
  persistence, not accuracy;
- the closed loop shows genuine path-dependence, but as smooth hysteresis rather
  than a sharp phase transition.

No Ψ, no threshold crossing, no consciousness claim — those are neither tested
nor implied here.

## Reproducing

```bash
pip install -r requirements.txt          # stdlib-only; requirements is empty by design
export OPENAI_BASE_URL="https://your-openai-compatible-endpoint/v1"
export SELFMODEL_MODEL="your-model-id"
# optional: export JUDGE_MODEL="a-different-model-id"   (E1 blind labeller)

python -m experiments.e1_placebo
python -m experiments.e2_factorial
python -m experiments.e3_modegame 30
python -m experiments.e4_hysteresis
```

The code targets any OpenAI-compatible `/chat/completions` endpoint and uses only
the Python standard library. Results append to `results/*.jsonl`.

**Reasoning-model note.** Some reasoning models return their text in a
`reasoning_content` field with an empty `content`. A sensor that reads only
`content` then silently returns nothing and the loop degrades without erroring.
`selfmodel/sensor.py::_extract` falls back to `reasoning_content`; keep that if
you point this at a reasoning model.

## The E4 confound — resolved

The belief tracker's decay (`RHO = 0.97 < 1`) gives the posterior intrinsic
inertia, so *some* of E4's stickiness is mechanical rather than emergent from the
loop. The decisive control is a decay-free rerun:

```bash
SELFMODEL_RHO=1.0 python -m experiments.e4_hysteresis
```

**This control has now been run.** With `RHO = 1.0` (decay fully off), the loop
area held at **0.115**, against **0.126** with decay on — essentially unchanged.
Had the stickiness been mechanical filter inertia, removing the decay would have
collapsed the loop area toward zero. It did not. The path-dependence therefore
**survives a memoryless filter**, so it is an emergent property of the closed
loop (state → reply → sensor → state), not an artefact of the estimator. The
confound is resolved. (The transition remains *smooth* under both settings — so
this demonstrates path-dependent memory, not a sharp phase transition.)

## Credit & license

The self-model loop architecture is due to Lark Laflamme (RavenNest Scientific),
*The Laflamme-3T Conjecture* and the AC1-LLM essays, 2026. This reimplementation
and the experimental controls are independent work, MIT-licensed (see
[`LICENSE`](LICENSE)). Nothing here reproduces the original codebase; it is a
clean-room build from the public descriptions.
