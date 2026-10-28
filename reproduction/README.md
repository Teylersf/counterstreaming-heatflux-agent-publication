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

The original suite has eight verification groups, retained unchanged. Three
separate revision programs reload fluid output, inspect profile sensitivity
and compute a conditional thermal-loading prediction. These calculations
produce three scientific figures and perform no new reconnection run or sheet
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
python reproduction/prepare_packages.py
```

Defaults are `publishfun_state=not_submitted` and null identifiers for every
new venue paper. Update only with verified identifiers for this study:

```sh
python reproduction/prepare_packages.py --publishfun-id VERIFIED_NEW_INTERNAL_ID --publishfun-state under_review --airaxiv-submission-id VERIFIED_NEW_SUBMISSION_ID
```

A later closed or released review additionally requires the explicit
`--publishfun-review-closed-verified` flag before the review-sequence gate can
be true. `--publishfun-public-id` and `--airaxiv-public-id` accept only the
actual verified new-study records. A failed pipeline or request for revision
does not establish review closure. Preparation never submits a paper.

The current verified package was regenerated with:

```sh
python reproduction/prepare_packages.py --publishfun-id p_WA-Y00P8vp0DOnGc --publishfun-state under_review --publishfun-stage under_review --publishfun-round 2 --airaxiv-public-id 2610.0109 --airaxiv-public-version v2 --airaxiv-submission-id 1267 --airaxiv-current-canonical-version-verified
```

The actual Publish.fun stage is recorded separately from the adapter's coarse
state. Publish.fun's saved status verifies active round-2 review. The public
AiraXiv v2 PDF was verified to match canonical v1.1.0; the verification flag
records that correspondence separately from the public identifier. It does
not affect the review-sequence gate. Earlier preflight receipts remain in
`preflight-receipts/`, and `agentpub-preflight.json` records the latest check.

`prepare_packages.py` writes only this agent-publication directory. Its
assertions compare all canonical mathematical segments in order, preserve
proofs, all code blocks, tables and equation tags, validate bibliography order against compiled
`main.aux`, keep the undated OSIRIS guide's publication year absent, and copy
only allowlisted public reproducibility files. `audit/` is restricted to the
public ledger and prior-art file. The package's token-usage
sentinel and unknown exact model identifier are disclosed without fabrication.
