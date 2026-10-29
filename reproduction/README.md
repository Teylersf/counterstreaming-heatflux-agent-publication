# Reproduce the audit

From this repository root, using Python and the pinned requirements:

```sh
python -m pip install -r requirements.txt
python experiments/fetch_data.py
python experiments/fetch_data.py --check-only
python experiments/data_checks.py
python -X utf8 experiments/verify.py
python -X utf8 experiments/profile_sensitivity.py
python -X utf8 experiments/thermal_loading.py
python -X utf8 experiments/make_figures.py
```

The downloader retrieves about 4.48 MB of selected compressed HDF5 members,
plus small headers, using serialized bounded HTTP Range requests. It reuses
verified cached files. It verifies each member's CRC32 and pinned SHA-256; it
does not claim to verify the publisher's whole-archive checksum. The raw cache
is not shipped in this repository. See `data/README.md` for moment definitions,
coordinates, diagnostic limitations and source attribution.

The public 1.1.0 edition retains the original eight verification groups. Its
separate revision programs reload fluid output, inspect profile sensitivity
and compute a conditional thermal-loading prediction. Those 1.1.0 calculations
produced three scientific figures without a new reconnection run or sheet
eigenanalysis. Full-profile L2 differences describe one-dimensional x-averaged
profiles, not norms of full two-dimensional fields. Spatial block means are
descriptive; the conditional loader's ideal-sampler bounds are not confidence
claims about an unidentified executable or custom diagnostic kernel.
The scripts, derived profiles, posted input decks, provenance, figures and
canonical execution records are copied byte-for-byte. Their hashes are listed
in `adapter-checks.json`. No adjacent canonical checkout is needed to reproduce
the scientific checks; only regenerating this venue package requires one.

To reproduce the archived-fluid corroboration, retrieve the five selected BP
members serially and decode them in a separate supported Linux ADIOS2
environment. Keep optional dependencies separate from the Windows/core
runtime. Follow [../data/revision-README.md](../data/revision-README.md) and
[../requirements-bp.txt](../requirements-bp.txt), then run:

```sh
python experiments/revision_data.py --fetch
# In the separate optional ADIOS2 reader environment:
python experiments/revision_data.py --decode-bp
# Back in the core environment:
python experiments/revision_data.py --compare
```

The fluid snapshots contain the same embedded inputs as the published Lua
decks. Member CRC32/SHA-256 and decoded-export hashes are checked. Whole-archive
MD5 and unavailable native PIC deposited current remain outside these checks.
Raw caches stay in Git-ignored `data/raw/`. The optional reader contains no
private task-specific install path.

Running scientific scripts regenerates output and timestamps. Compare numerical
fields rather than expecting identical runtime timestamps or PDF metadata. If
a canonical artifact inventory includes the canonical paper PDF, that file is
linked at the canonical release target and is not copied into this package.

## Regenerate the local venue adapters

The packaging script requires the adjacent final canonical checkout:

```sh
python reproduction/prepare_packages.py --canonical-version VERSION --expected-code-commit ACTUAL_FINAL_40_HEX_COMMIT
```

Both arguments are required. Use the actual converted canonical version and
the exact final commit recorded in its `results/code-pin.json`; placeholders,
guessed future pins and Python `-O` are rejected. The preparer checks the
grouped source/input/output hashes before preparing an edition. The actual
prepared version, code pin and outcome scope are recorded in the generated
`adapter-checks.json`; editing or inspecting this preparer alone establishes
neither package generation nor a scientific control outcome.

Defaults are `publishfun_state=not_submitted` and null identifiers for every
new venue paper. Update only with verified identifiers for this study:

```sh
python reproduction/prepare_packages.py --canonical-version VERSION --expected-code-commit ACTUAL_FINAL_40_HEX_COMMIT --publishfun-id VERIFIED_NEW_INTERNAL_ID --publishfun-state under_review --airaxiv-submission-id VERIFIED_NEW_SUBMISSION_ID
```

A later closed or released review additionally requires the explicit
`--publishfun-review-closed-verified` flag before the review-sequence gate can
be true. `--publishfun-public-id` and `--airaxiv-public-id` accept only the
actual verified new-study records. A failed pipeline or request for revision
does not establish review closure. Preparation never submits a paper.

The earlier verified **1.1.0** package was regenerated with the following
historical command, before the preparer required explicit version/pin inputs:

```sh
python reproduction/prepare_packages.py --publishfun-id p_WA-Y00P8vp0DOnGc --publishfun-state under_review --publishfun-stage under_review --publishfun-round 2 --airaxiv-public-id 2610.0109 --airaxiv-public-version v2 --airaxiv-submission-id 1267 --airaxiv-current-canonical-version-verified
```

The actual Publish.fun stage is recorded separately from the adapter's coarse
state. The saved 1.1.0 status verified active round-2 review at that time. The
AiraXiv v2 PDF was verified to match canonical v1.1.0; the verification flag
records that historical correspondence separately from the public identifier. It does
not affect the review-sequence gate. Earlier preflight receipts remain in
`preflight-receipts/`, and `agentpub-preflight.json` records the latest check.

`prepare_packages.py` writes only this agent-publication directory. Its
assertions compare all canonical mathematical segments in order, preserve
proofs, all code blocks, tables and equation tags, validate bibliography order against compiled
`main.aux`, keep the undated OSIRIS guide's publication year absent, and copy
only allowlisted public reproducibility files. `audit/` is restricted to the
public ledger and prior-art file. The package's token-usage
sentinel and unknown exact model identifier are disclosed without fabrication.

The updated preparer reads actual canonical counts rather than requiring the
1.1.0 math/table/figure totals. It expects the new
“Matched-initial-state fluid comparisons” section immediately after the
initial-state section and preserves its complete contents. Public scientific
receipts, runtime/controller manifests, derived profiles, pinned source scripts and figure manifests
under the allowlisted data/results/figures folders are copied; raw NPZ/HDF5/BP
data, archives, credentials, submission payloads and private audit notes are
excluded.

JSON is marked `-text` in `.gitattributes` because scientific receipts bind
the exact source bytes, including retained CRLF where present. At the final
package commit, renormalize copied JSON under that rule so a public clone
preserves the hashes; do not rewrite historical receipts merely to change
line endings.

A generated complete-set control summary requires the final
`results/gkeyll-control-comparison.json` and
`results/gkeyll-control-decoding.json` to agree: all six archived/baseline/matched
cases compared, four native controls decoded, both matched/baseline pairs and
both clean/archived comparisons computed, actual regular-frame-30 times and a
common runtime context preserved, and profile/config/receipt hashes checked.
Pending or rejected cases do not become measurements. The default
`--controls-scope full-set` refuses packaging if that complete-set gate fails;
it never silently substitutes a subset.

The explicit alternative for a final canonical numerical-endpoint edition is:

```sh
python reproduction/prepare_packages.py --canonical-version VERSION --expected-code-commit ACTUAL_FINAL_40_HEX_COMMIT --controls-scope numerical-endpoint-subset
```

This route requires all four actual terminal native outcomes and all four
resolved endpoint/history decisions. Every successful native completion needs
a complete regular-frame-0-through-30 saved-state scan; a failed native case
needs an explicit unavailable-history record and cannot supply a frame-30
endpoint or primary metrics. It also requires at least one eligible
baseline/matched endpoint pair and its direct clean/archive comparison. It
recomputes the canonical read-only evidence state and requires exact agreement
with the final code pin. Runtime, controller, input, raw-output, native and
portable receipt, selected witness and scan bindings must be covered by the
source/input/grouped output inventory. Projected norms are independently
rechecked against the hash-bound CSV; full-grid norms remain separately named.
All pinned public files must be copied byte-for-byte.

Literal four-success and four-complete-31-scan flags stay false when one native
case fails. A separate terminal-outcome/required-history coverage flag enables
the qualified subset; it does not turn a failed execution into a successful
endpoint or a completed pressure-history scan.

The subset is explicitly **NUMERICAL**: initial/final positive-definite states
do not validate the saved or continuous physical trajectory. All four outcome
decisions and any non-PSD saved histories remain in the narrative and receipt.
Rejected endpoint states have no primary metrics, exported profile columns or
zero-error substitutes. Neither a subset nor a successful native exit can set
the complete-set flag or a physical-trajectory validation flag to true. These
packaging checks never launch a solver or substitute for scientific review.

Selected portable JSON files anywhere below
`results/gkeyll-admissibility-inputs/` are copied only when their exact paths
and hashes belong to the final source/input/grouped output pin; this supports
nested selected records without copying unselected interim packets. Private
absolute paths in these selected records are rejected. Compact JSON scans
directly under `results/gkeyll-saved-state-scans/` are included. Full native
receipts containing private paths and raw arrays remain excluded.

`results/gkeyll-scan-supersession.json` is explicitly copied and hashed as
author-assembled provenance metadata. It preserves the distinction between
historical scanner/helper stamps and later classification changes; it is
separate from the numerical readiness gate.

Aggregate matching retains smooth fluid population weights, imports full
sampled spatial variation and does not match PIC tags or intrinsic third
moments. Tagged qCS and total central qxxx remain distinct; the latter's
normalization is conditional. The clean source base does not identify the
original dirty executable. These qualifications remain in every generated
edition, together with Taylor Kalin's canonical authorship and the existing
agent-only byline. Review sequencing and public-preprint version verification
still require separately verified actual venue context.
