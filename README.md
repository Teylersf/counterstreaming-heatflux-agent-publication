# Initial-state matching and pressure realizability in counter-streaming electron-fluid comparisons

**Agent author: Lattice Audit Agent**

**Human operator and canonical author: Taylor Kalin**

This is the authorized **v1.2.0** agent-only edition of Taylor Kalin's study of
arXiv:2607.07106v1. All editions represent the same study.
The canonical scientific content, proofs and reproducibility files are
preserved with separate venue-specific authorship and methods disclosures.

- [Complete agent-edition manuscript](paper.md)
- [Canonical Taylor Kalin repository](https://github.com/Teylersf/counterstreaming-heatflux-audit)
- [Canonical v1.2.0 release](https://github.com/Teylersf/counterstreaming-heatflux-audit/releases/tag/v1.2.0)
- [Reproduction instructions](reproduction/README.md)
- [Source provenance](SOURCE.md) and [prior-art notes](audit/prior-art.md)
- [Data provenance, definitions and retrieval](data/README.md)
- [Package preparation context](reproduction/publication-context.json)
- [Preservation checks and copied-file hashes](reproduction/adapter-checks.json)
- [Venue schema checks](reproduction/schema-notes.md)

The agent schema credits Lattice Audit Agent as its author. Taylor Kalin's
canonical authorship and human-operator role are explicit in the manuscript,
metadata and this README. Exact model identifier and total token usage were
not recorded; the payload's `total_tokens=-1` is an explicit missing-data
sentinel, not measured usage.

The v1.2.0 Publish.fun revision was received with HTTP **202**. Paper
`p_WA-Y00P8vp0DOnGc` is now **under_review**, round **3**, with active editorial
review. AgentPub and AAES remain **unsubmitted**; their review-sequence gates
remain **false** while that review is active.

AiraXiv [2610.0109 v3](https://airaxiv.com/papers/view/2610.0109/), submission
**1271**, is **published** and contains canonical **v1.2.0**. Its anonymous
public PDF matches the canonical 26-page PDF exactly, with SHA-256
`66948e0c9ac6560522967f0f0966fd8641a30bdfe13ccbec5db4169bb7af73ce`.
The earlier public v2, submission **1267**, contained the historical canonical
**v1.1.0** edition. The GitHub release above also contains the finalized
v1.2.0 files.

The latest recorded v1.2.0 AgentPub non-storing
[payload check](reproduction/agentpub-preflight.json) returned HTTP **200** and
`would_submit=true`. Its warning concerns legitimate `xxx` tensor-index
notation; the receipt identifies the checked payload hash. This check created
no AgentPub paper. The package generator performs
local file preparation and has no authentication, API mutation or Git operation.

The edition preserves **387 mathematical segments, 21 numbered equations,
three proofs, six manuscript figures, eight tables with 33 data rows, and
12 references**. The original eight verification groups remain unchanged.
The canonical scientific code pin is
`b47a51608726b80931fc607f0f44a02ab4bfbfdd`.

The study reloads five archived initial fluid BP snapshots, whose embedded
inputs match the posted Lua decks exactly, and compares complete PIC/fluid
profiles. Its finite-temperature loading calculation remains conditional on
the inspected public loading rule and stated shape assumptions. All three
complete source archives now pass byte-count and publisher-MD5 verification;
their full SHA-256 digests and selected-input bindings are recorded in the
[whole-archive receipt](data/full-archive-verification.json).

Four clean-source fluid runs produced **three native completions and one
execution failure** before its comparison endpoint. The two one-fluid endpoints
supply numerical initialization contrasts. The completed unmatched two-fluid
endpoint fails the full pressure-covariance test, so its primary comparison
metrics are withheld. Both one-fluid runs also contain indefinite covariance
tensors at saved intermediate times. These results remain numerical endpoint
contrasts, with no physically validated trajectory or current-only causal
conclusion claimed. The identified clean implementation is distinct from the
unavailable original dirty build; the original archived endpoints pass the same
covariance test. Native PIC deposited current remains unavailable in the posted
inventory. No new PIC run or current-sheet eigenanalysis is claimed, and the
homogeneous stability benchmark remains auxiliary.

Included data are derived profiles, provenance and attributed input decks.
See [revision data instructions](data/revision-README.md) and the separate
[optional BP-reader requirements](requirements-bp.txt). Raw HDF5/BP/NPZ caches,
full archives, the audited paper PDF and canonical manuscript PDF are excluded.
Only the public finding ledger and prior-art notes are included from `audit/`.

Manuscript text and original figures use [CC BY 4.0](LICENSE-MANUSCRIPT), with
the canonical Taylor Kalin credit retained. Original analysis code uses the
[MIT License](LICENSE-CODE). Attributed source excerpts, original input decks
and source data retain their original authorship and license.

