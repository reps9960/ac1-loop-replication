# arXiv submission notes

## What to upload
arXiv wants the **LaTeX source**, not the PDF. Upload `ac1_replication.tex`
(arXiv compiles it its own end). No custom packages are used beyond standard
ones (amsmath, booktabs, geometry, hyperref, natbib) — all present on arXiv.

## Category
Primary: **cs.AI** (Artificial Intelligence).
Cross-list (optional): **cs.CL** (Computation and Language).

## The one gate: endorsement
As a first-time submitter with no institutional email, cs.AI requires an
**endorsement** from an existing arXiv author in that category before your first
submission. This is arXiv's spam filter, not a quality bar.
- When you register and try to submit to cs.AI, arXiv gives you an endorsement
  code and a link.
- You need one established cs.AI author to enter it. Options: someone you know
  who has posted to cs.AI; or the endorsement request is visible to potential
  endorsers arXiv suggests.
- Note: Lark himself states he is *preparing* arXiv submissions (cs.AI + q-bio.NC)
  but may not yet be an established author who can endorse. Don't rely on that.

## If endorsement is a blocker
The repo alone is already public and reproducible. Alternatives that need no
endorsement and still reach a research audience:
- **Zenodo** — mints a DOI, no endorsement, archival. (Lark uses Zenodo-style
  DOIs himself.) This is the fastest "citable preprint" route.
- **OSF preprints** or **ResearchGate** — no gate, lower reach.
arXiv has the most reach *and* is the stream Lark's agent scans weekly, so it's
worth pursuing the endorsement — but Zenodo is the no-friction fallback that
still gives you a permanent, citable record.

## Before you submit
- Fill in a real contact/affiliation on the arXiv author form (independent is
  fine).
- The paper credits Laflamme in Acknowledgements and frames the work as
  replication, not rebuttal — keep that framing in the abstract field too.
- Link the GitHub repo in the "Comments" field:
  `Code and data: https://github.com/reps9960/ac1-loop-replication`
